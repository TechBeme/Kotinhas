import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters



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
    await update.message.reply_text(mensagem_boas_vindas)

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
    item_id = len(dados['grupos']) + 1

    dados['grupos'].append({
        "titulo": titulo,
        "username": f"@{update.message.from_user.username}",
        "valor": valor,
        "id": f"{item_id:04d}"
    })

    mensagem_grupo = f'🎬 {titulo}\n👤 @{update.message.from_user.username}\n💲 R$ {valor}\n🆔 {item_id:04d}'

    # Envia a mensagem para o grupo público e armazena o ID da mensagem
    public_message = await context.bot.send_message(chat_id=PUBLIC_GROUP_ID, text=mensagem_grupo)
    dados['grupos'][-1]['public_message_id'] = public_message.message_id

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
    grupo_removido = None

    for grupo in dados['grupos']:
        if grupo['id'] == item_id:
            grupo_removido = grupo
            break

    if grupo_removido:
        # Verifique se o usuário é o administrador ou o criador do grupo
        if f"@{update.message.from_user.username}" == ADMIN_USERNAME or grupo_removido["username"] == f"@{update.message.from_user.username}":
            try:
                await context.bot.delete_message(chat_id=PUBLIC_GROUP_ID, message_id=grupo_removido['public_message_id'])
                dados['grupos'].remove(grupo_removido)
                await update.message.reply_text(f'🗑️ O grupo "{grupo_removido["titulo"]}" com ID {item_id} foi removido com sucesso.')
            except Exception as e:
                await update.message.reply_text(f"Erro ao remover mensagem: {e}")
        else:
            await update.message.reply_text('❌ Você não tem permissão para remover este grupo.')
    else:
        await update.message.reply_text(f'❌ Grupo com ID {item_id} não encontrado.')

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
    )
    await update.message.reply_text(mensagem_ajuda, parse_mode='Markdown')

async def comandos(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    mensagem_comandos = (
        "Estes são os comandos que você pode usar para interagir com o bot:\n\n"
        "❓ /ajuda - Aprenda a usar o bot.\n"
        "🎬 /grupos - Mostra a lista de todos os grupos existentes.\n"
        "➕ /adicionar - Adiciona um novo grupo na lista.\n"
        "❌ /remover - Remove um grupo da lista pelo ID.\n"
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
    resultados = [grupo for grupo in dados['grupos'] if palavra_chave in grupo['titulo'].lower()]

    if not resultados:
        await update.message.reply_text('❌ Nenhum grupo encontrado com essa palavra-chave.')
    else:
        resposta = "\n\n".join([f"🎬 {item['titulo']}\n👤 {item['username']}\n💲 R$ {item['valor']}\n🆔 {item['id']}" for item in resultados])
        await update.message.reply_text(resposta)

# Função para lidar com mensagens encaminhadas
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
            
            # Verifique se o ID já existe no dicionário de dados
            for grupo in dados['grupos']:
                if grupo['id'] == item_id:
                    await update.message.reply_text(f'❌ Grupo com ID {item_id} já existe.')
                    return
            
            # Envie a mensagem formatada para o grupo público e armazene o ID da mensagem
            try:
                public_message = await context.bot.forward_message(chat_id=PUBLIC_GROUP_ID, from_chat_id=update.message.chat_id, message_id=update.message.message_id)
                dados['grupos'].append({
                    "titulo": titulo,
                    "username": username,
                    "valor": valor,
                    "id": item_id,
                    "public_message_id": public_message.message_id
                })
                await update.message.reply_text(f'✅ Mensagem encaminhada e grupo adicionado com sucesso!')
            except Exception as e:
                await update.message.reply_text(f"Erro ao enviar mensagem: {e}")
        else:
            await update.message.reply_text('❌ Mensagem encaminhada no formato incorreto.')

def main() -> None:
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("grupos", grupos))
    application.add_handler(CommandHandler("adicionar", adicionar))
    application.add_handler(CommandHandler("remover", remover))
    application.add_handler(CommandHandler("ajuda", ajuda))
    application.add_handler(CommandHandler("pesquisar", pesquisar))
    application.add_handler(CommandHandler("comandos", comandos))

    # Adicione este handler para encaminhar mensagens
    application.add_handler(MessageHandler(filters.FORWARDED & filters.TEXT, encaminhar_para_grupo))

    application.run_polling()

if __name__ == '__main__':
    main()