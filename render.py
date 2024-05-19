import os
import psycopg2
from psycopg2 import sql
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
from flask import Flask
import threading



app = Flask(__name__)

@app.route('/')
def home():
    return "Bot está vivo!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = threading.Thread(target=run)
    t.daemon = True
    t.start()

# Configurar variáveis de ambiente para a conexão com o PostgreSQL
DATABASE_URL = os.getenv('DATABASE_URL')

# Função para conectar ao banco de dados PostgreSQL
def connect_db():
    return psycopg2.connect(DATABASE_URL)

# Criar a tabela de grupos se não existir
def create_table():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS grupos (
            id SERIAL PRIMARY KEY,
            titulo TEXT NOT NULL,
            username TEXT NOT NULL,
            valor TEXT NOT NULL,
            public_message_id INTEGER NOT NULL
        )
    """)
    conn.commit()
    cursor.close()
    conn.close()

# Chamar a função para criar a tabela ao iniciar
create_table()

# Token do bot fornecido pelo BotFather
TOKEN = os.getenv('TOKEN')

# ID do grupo público onde as mensagens serão postadas
PUBLIC_GROUP_ID = int(os.getenv('PUBLIC_GROUP_ID'))

ADMIN_USERNAME = os.getenv('ADMIN_USERNAME')

# Dicionário para armazenar os dados (em produção, você deve usar um banco de dados)
dados = {
    "grupos": []
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    mensagem_boas_vindas = (
        "👋 Olá, bem-vindo ao bot de compartilhamento de assinaturas no Kotas!\n\n"
        "📢 Este bot foi criado para ajudar você a encontrar e compartilhar grupos privados e públicos do Kotas, "
        "um site para dividir assinaturas e economizar.\n\n"
        f"👉 Para ver a lista de grupos disponíveis, clique [aqui](https://t.me/+O9EgeX1jpIBhMGMx).👈\n\n"
        "🎁 Quer economizar ainda mais? Utilize na sua primeira compra o cupom: `JBX3197` para ganhar R$ 5,00 de desconto!\n\n"
        "❓ Use /ajuda para ver a lista de comandos disponíveis e começar a usar o bot."
    )
    await update.message.reply_text(mensagem_boas_vindas, parse_mode='Markdown')

async def grupos(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    numero_de_grupos = len(dados['grupos'])
    mensagem = (
        f"🎉 Temos {numero_de_grupos} grupo(s) esperando por você!\n\n"
        f"👉 Para ver a lista de grupos disponíveis, clique [aqui](https://t.me/+O9EgeX1jpIBhMGMx).👈\n\n"
        "🎁 Quer economizar ainda mais? Utilize na sua primeira compra o cupom: `JBX3197` para ganhar R$ 5,00 de desconto!\n\n"
        "🔍 Você também pode usar o comando /pesquisar seguido de uma palavra-chave para encontrar um grupo específico.\n\n"
        "❓ Se precisar de ajuda, digite /ajuda."
    )
    await update.message.reply_text(mensagem, parse_mode='Markdown')

async def adicionar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if len(context.args) < 2:
        mensagem_instrucoes = (
            "⚠️ Para adicionar um grupo, siga estas etapas:\n\n"
            "1️⃣ Digite o comando /adicionar seguido do valor em reais e do nome do grupo.\n"
            "2️⃣ Use um espaço entre o valor e o nome.\n\n"
            "➡ Exemplo: /adicionar 13,98 Netflix Premium\n\n"
        )
        await update.message.reply_text(mensagem_instrucoes)
        return

    valor = context.args[0].replace(',', '.')
    titulo = ' '.join(context.args[1:])
    username = f"@{update.message.from_user.username}"

    mensagem_grupo = f'🎬 {titulo}\n👤 {username}\n💲 R$ {valor}'

    # Envia a mensagem para o grupo público e armazena o ID da mensagem
    public_message = await context.bot.send_message(chat_id=PUBLIC_GROUP_ID, text=mensagem_grupo)

    # Conecta ao banco de dados e insere o novo grupo
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO grupos (titulo, username, valor, public_message_id) VALUES (%s, %s, %s, %s)",
        (titulo, username, valor, public_message.message_id)
    )
    conn.commit()
    cursor.close()
    conn.close()

    # Envia a mensagem para o usuário que adicionou o grupo
    await update.message.reply_text(f'✅ Grupo adicionado com sucesso!\n\n{mensagem_grupo}')

async def remover(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if len(context.args) != 1:
        mensagem_instrucoes = (
            "⚠️ Para remover um grupo, siga estas etapas:\n\n"
            "1️⃣ Digite o comando /remover seguido do ID do grupo.\n"
            "2️⃣ Use um espaço entre o comando e o ID.\n\n"
            "➡ Exemplo: /remover 0001\n\n"
        )
        await update.message.reply_text(mensagem_instrucoes)
        return

    item_id = context.args[0]

    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM grupos WHERE id = %s", (item_id,))
    grupo_removido = cursor.fetchone()

    if grupo_removido:
        if f"@{update.message.from_user.username}" == ADMIN_USERNAME or grupo_removido[2] == f"@{update.message.from_user.username}":
            try:
                await context.bot.delete_message(chat_id=PUBLIC_GROUP_ID, message_id=grupo_removido[4])
            except Exception as e:
                # Log the exception for debugging purposes
                print(f"Erro ao remover mensagem: {e}")

            # Remova o grupo do banco de dados, independentemente de a mensagem ter sido deletada com sucesso ou não
            cursor.execute("DELETE FROM grupos WHERE id = %s", (item_id,))
            conn.commit()
            await update.message.reply_text(f'🗑️ O grupo com ID {item_id} foi removido com sucesso.')
        else:
            await update.message.reply_text('❌ Você não tem permissão para remover este grupo.')
    else:
        await update.message.reply_text(f'❌ Grupo com ID {item_id} não encontrado.')

    cursor.close()
    conn.close()

async def meusgrupos(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    username = f"@{update.message.from_user.username}"

    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM grupos WHERE username = %s", (username,))
    grupos = cursor.fetchall()
    cursor.close()
    conn.close()

    if not grupos:
        await update.message.reply_text('❌ Você não adicionou nenhum grupo.')
    else:
        resposta = "\n\n".join([f"🎬 {item[1]}\n💲 R$ {item[3]}\n🆔 {item[0]}" for item in grupos])
        await update.message.reply_text(resposta)

async def ajuda(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    mensagem_ajuda = (
        "👋 Olá! Sou o bot do Kotas, seu assistente para gerenciar e compartilhar assinaturas. Vamos começar?\n\n"
        "Aqui estão os comandos que você pode usar para interagir comigo:\n\n"

        "👉 **Ver a lista de grupos:**\n"      
        "1️⃣ Para ver todos os grupos disponíveis, vá até nosso canal clicando [aqui](https://t.me/+O9EgeX1jpIBhMGMx) ou digite /grupos no chat.\n"
        "2️⃣ Para participar de um grupo, mande uma mensagem privada para o usuário (👤 @NomeDoUsuario) com o seu email do Kotas e solicite o convite.\n"
        "🎁 Quer economizar ainda mais? Utilize na sua primeira compra o cupom: `JBX3197` para ganhar R$ 5,00 de desconto!\n\n"

        "👉 **Entendendo as mensagens do canal:**\n"
        "As mensagens do canal têm o seguinte formato:\n"
        "🎬 Nome do grupo/serviço\n"
        "👤 Nome do usuário (administrador do grupo)\n"
        "💲 Preço (valor por mês do serviço)\n"
        "🆔 Identificação do grupo\n\n"

        "👉 **Adicionar grupos:**\n"
        "1️⃣ Crie um grupo no [Kotas](https://kotas.com.br/).\n"
        "2️⃣ Digite /adicionar seguido do valor em reais e do nome do grupo.\n"
        "➡ Exemplo: /adicionar 13,98 Netflix.\n"
        "Após adicionar, seu grupo será listado no [canal](https://t.me/+O9EgeX1jpIBhMGMx) para que todos possam encontrá-lo.\n"
        "Depois disso, basta aguardar alguém entrar em contato. Solicite o email do Kotas e envie o convite para o seu grupo.\n\n"
        
        "👉 **Remover grupo:**\n"
        "Os anúncios dos grupos expiram automaticamente em 14 dias. Para remover um grupo antes desse prazo:\n"
        "1️⃣ Digite /remover seguido do ID do grupo.\n"
        "➡ Exemplo: /remover 0001.\n\n"

        "👉 **Ver meus grupos:**\n"
        "1️⃣ Digite /meusgrupos para ver a lista dos grupos que você adicionou.\n\n"
    )
    await update.message.reply_text(mensagem_ajuda, parse_mode='Markdown')

async def comandos(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    mensagem_comandos = (
        "Estes são os comandos que você pode usar para interagir com o bot:\n\n"
        "❓ /ajuda - Aprenda a usar o bot.\n"
        "🎬 /grupos - Mostra a lista de todos os grupos existentes.\n"
        "➕ /adicionar - Adiciona um novo grupo na lista.\n"
        "❌ /remover - Remove um grupo da lista pelo ID.\n"
        "👤 /meusgrupos - Veja os grupos que você adicionou.\n"
        "🔍 /pesquisar - Busca todos os grupos com uma palavra-chave.\n"
        "📋 /comandos - Lista todos os comandos.\n"
    )
    await update.message.reply_text(mensagem_comandos)

async def pesquisar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if len(context.args) == 0:
        mensagem_instrucoes = (
            "⚠️ Para pesquisar um grupo, siga estas etapas:\n\n"
            "1️⃣ Digite o comando /pesquisar seguido da palavra-chave.\n"
            "2️⃣ Use um espaço entre o comando e a palavra-chave.\n\n"
            "➡ Exemplo: /pesquisar Netflix\n\n"
        )
        await update.message.reply_text(mensagem_instrucoes)
        return

    palavra_chave = ' '.join(context.args).lower()

    # Conecta ao banco de dados e realiza a pesquisa
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM grupos WHERE LOWER(titulo) LIKE %s", ('%' + palavra_chave + '%',))
    resultados = cursor.fetchall()
    cursor.close()
    conn.close()

    if not resultados:
        await update.message.reply_text('❌ Nenhum grupo encontrado com essa palavra-chave.')
    else:
        resposta = "\n\n".join([f"🎬 {item[1]}\n👤 {item[2]}\n💲 R$ {item[3]}\n🆔 {item[0]}" for item in resultados])
        await update.message.reply_text(resposta)

# Função para lidar com mensagens encaminhadas
async def encaminhar_para_grupo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    mensagem = update.message.text
    if mensagem:
        # Divida a mensagem nas linhas individuais e remova espaços em branco extras
        linhas = [linha.strip() for linha in mensagem.split('\n') if linha.strip()]
        
        # Verifique se a mensagem está no formato esperado
        if len(linhas) == 4 and linhas[0].startswith('🎬') and linhas[1].startswith('👤') and linhas[2].startswith('💲') and linhas[3].startswith('🆔'):
            titulo = linhas[0][2:].strip()
            username = linhas[1][2:].strip()
            valor = linhas[2][2:].strip().replace('R$', '').strip()
            item_id = linhas[3][2:].strip()

            # Verifique se o ID já existe no banco de dados
            conn = connect_db()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM grupos WHERE id = %s", (item_id,))
            grupo_existe = cursor.fetchone()
            if grupo_existe:
                await update.message.reply_text(f'❌ Grupo com ID {item_id} já existe.')
                cursor.close()
                conn.close()
                return

            # Envie a nova mensagem formatada para o grupo público
            try:
                nova_mensagem = f'🎬 {titulo}\n👤 {username}\n💲 R$ {valor}\n🆔 {item_id}'
                public_message = await context.bot.send_message(chat_id=PUBLIC_GROUP_ID, text=nova_mensagem)

                # Insira o novo grupo no banco de dados
                cursor.execute(
                    "INSERT INTO grupos (titulo, username, valor, public_message_id) VALUES (%s, %s, %s, %s) RETURNING id",
                    (titulo, username, valor, public_message.message_id)
                )
                new_id = cursor.fetchone()[0]
                conn.commit()
                cursor.close()
                conn.close()

                # Atualiza a mensagem original com o novo ID gerado
                await context.bot.edit_message_text(chat_id=PUBLIC_GROUP_ID, message_id=public_message.message_id,
                    text=f'🎬 {titulo}\n👤 {username}\n💲 R$ {valor}\n🆔 {new_id}')

                await update.message.reply_text(f'✅ Mensagem enviada e grupo adicionado com sucesso!')
            except Exception as e:
                await update.message.reply_text(f"Erro ao enviar mensagem: {e}")
                cursor.close()
                conn.close()
        else:
            await update.message.reply_text('❌ Mensagem encaminhada no formato incorreto.')

async def enviar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_username = update.message.from_user.username
    
    if user_username != ADMIN_USERNAME.strip('@'):
        await update.message.reply_text('❌ Você não tem permissão para usar este comando.')
        return
    
    if not context.args:
        await update.message.reply_text('⚠️ Use o comando da seguinte forma: /enviar <mensagem>')
        return
    
    mensagem = ' '.join(context.args)
    
    # Formatar a mensagem com quebras de linha
    mensagem_formatada = mensagem.replace('\\n', '\n')
    
    try:
        await context.bot.send_message(chat_id=PUBLIC_GROUP_ID, text=mensagem_formatada, parse_mode='Markdown')
        await update.message.reply_text('✅ Mensagem enviada com sucesso!')
    except Exception as e:
        await update.message.reply_text(f"Erro ao enviar mensagem: {e}")

def main() -> None:
    keep_alive()
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("ajuda", ajuda))
    application.add_handler(CommandHandler("grupos", grupos))
    application.add_handler(CommandHandler("adicionar", adicionar))
    application.add_handler(CommandHandler("remover", remover))
    application.add_handler(CommandHandler("meusgrupos", meusgrupos))
    application.add_handler(CommandHandler("pesquisar", pesquisar))
    application.add_handler(CommandHandler("comandos", comandos))
    application.add_handler(CommandHandler("enviar", enviar))
    
    # Adicione este handler para encaminhar mensagens
    application.add_handler(MessageHandler(filters.FORWARDED & filters.TEXT, encaminhar_para_grupo))

    application.run_polling()

if __name__ == '__main__':
    main()