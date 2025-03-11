import logging
import pandas as pd
import datetime
import threading
import asyncio
import matplotlib.pyplot as plt
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

# Variáveis globais para armazenamento dos registros
registros = []       # Lista de registros; cada registro é um dict com: id, valor, categoria, data
next_id = 1          # Para atribuir IDs únicos a cada registro
saldos_mensais = {}  # Dict com chave = "YYYY-MM", valor = {'saldo': float, 'total_gasto': float}
USER_ID = USER_ID  # Substitua pelo seu ID de usuário do Telegram

# Definição de alias para categorias
ALIASES = {
    "alug": "Residência",
    "luz": "Residência",
    "internet": "Residência",
    "merc": "Alimentação",
    "mercado": "Alimentação",
    "uber": "Transporte"
}

def get_data_atual():
    return datetime.datetime.now().strftime('%Y-%m-%d')

def get_mes_atual():
    return datetime.datetime.now().strftime('%Y-%m')

def iniciar_mes():
    mes = get_mes_atual()
    if mes not in saldos_mensais:
        saldos_mensais[mes] = {'saldo': 0, 'total_gasto': 0}

def aplicar_alias(categoria_input: str) -> str:
    categoria_lower = categoria_input.lower()
    for alias, full in ALIASES.items():
        if alias in categoria_lower:
            return full
    return categoria_input

def atualizar_total_gasto(mes: str):
    total = sum(r['valor'] for r in registros if r['data'].startswith(mes))
    saldos_mensais[mes]['total_gasto'] = total

def verificar_usuario(update: Update):
    return update.effective_user.id == USER_ID

# Comandos mencionados no readme
async def adicionar_gasto(update: Update, context: CallbackContext):
    global next_id
    if not verificar_usuario(update):
        await update.effective_message.reply_text("Você não tem permissão para usar este bot.")
        return
    iniciar_mes()
    mes = get_mes_atual()
    try:
        valor = float(context.args[0])
        categoria_input = " ".join(context.args[1:])
        categoria = aplicar_alias(categoria_input)
        data_atual = get_data_atual()
        registro = {"id": next_id, "valor": valor, "categoria": categoria, "data": data_atual}
        registros.append(registro)
        next_id += 1
        saldos_mensais[mes]['total_gasto'] += valor
        await update.effective_message.reply_text(
            f"Registro adicionado: ID {registro['id']} - Gasto de R${valor:.2f} na categoria {categoria} (Data: {data_atual})"
        )
    except (IndexError, ValueError):
        await update.effective_message.reply_text("Uso correto: /g valor categoria")

async def definir_saldo(update: Update, context: CallbackContext):
    if not verificar_usuario(update):
        await update.effective_message.reply_text("Você não tem permissão para usar este bot.")
        return
    iniciar_mes()
    mes = get_mes_atual()
    try:
        saldo = float(context.args[0])
        saldos_mensais[mes]['saldo'] = saldo
        await update.effective_message.reply_text(f"Saldo mensal definido para {mes}: R${saldo:.2f}")
    except (IndexError, ValueError):
        await update.effective_message.reply_text("Uso correto: /e valor")

async def consultar_saldo_disponivel(update: Update, context: CallbackContext):
    if not verificar_usuario(update):
        await update.effective_message.reply_text("Você não tem permissão para usar este bot.")
        return
    iniciar_mes()
    mes = get_mes_atual()
    atualizar_total_gasto(mes)
    saldo_disponivel = saldos_mensais[mes]['saldo'] - saldos_mensais[mes]['total_gasto']
    await update.effective_message.reply_text(f"Saldo disponível para {mes}: R${saldo_disponivel:.2f}")

async def relatorio_mensal(update: Update, context: CallbackContext):
    if not verificar_usuario(update):
        await update.effective_message.reply_text("Você não tem permissão para usar este bot.")
        return
    mes = get_mes_atual()
    dados_mes = [r for r in registros if r['data'].startswith(mes)]
    df = pd.DataFrame(dados_mes)
    csv_filename = f"relatorio_{mes}.csv"
    df.to_csv(csv_filename, index=False)
    if df.empty:
        await update.effective_message.reply_text(
            f"Nenhum gasto registrado em {mes}.\nArquivo CSV gerado: {csv_filename}"
        )
    else:
        relatorio = df.groupby("categoria")["valor"].sum().reset_index()
        mensagem = (
            f"Relatório parcial para {mes}:\n" +
            "\n".join([f"{row.categoria}: R${row.valor:.2f}" for _, row in relatorio.iterrows()]) +
            f"\n\nArquivo CSV gerado: {csv_filename}"
        )
        await update.effective_message.reply_text(mensagem)

async def editar_registro(update: Update, context: CallbackContext):
    if not verificar_usuario(update):
        await update.effective_message.reply_text("Você não tem permissão para usar este bot.")
        return
    try:
        registro_id = int(context.args[0])
        novo_valor = float(context.args[1])
    except (IndexError, ValueError):
        await update.effective_message.reply_text("Uso correto: /editar <id> <novo_valor> [<nova_categoria>]")
        return
    registro = next((r for r in registros if r["id"] == registro_id), None)
    if registro is None:
        await update.effective_message.reply_text(f"Registro com ID {registro_id} não encontrado.")
        return
    # Se uma nova categoria for fornecida, atualiza; senão, mantém a categoria anterior.
    if len(context.args) > 2:
        nova_categoria_input = " ".join(context.args[2:])
        nova_categoria = aplicar_alias(nova_categoria_input)
    else:
        nova_categoria = registro["categoria"]
    mes = registro["data"][:7]
    saldos_mensais[mes]["total_gasto"] -= registro["valor"]
    registro["valor"] = novo_valor
    registro["categoria"] = nova_categoria
    saldos_mensais[mes]["total_gasto"] += novo_valor
    await update.effective_message.reply_text(
        f"Registro ID {registro_id} atualizado: novo valor R${novo_valor:.2f}, categoria {nova_categoria}."
    )

async def excluir_registro(update: Update, context: CallbackContext):
    if not verificar_usuario(update):
        await update.effective_message.reply_text("Você não tem permissão para usar este bot.")
        return
    try:
        registro_id = int(context.args[0])
    except (IndexError, ValueError):
        await update.effective_message.reply_text("Uso correto: /excluir <id>")
        return
    global registros
    registro = next((r for r in registros if r["id"] == registro_id), None)
    if registro is None:
        await update.effective_message.reply_text(f"Registro com ID {registro_id} não encontrado.")
        return
    mes = registro["data"][:7]
    saldos_mensais[mes]["total_gasto"] -= registro["valor"]
    registros = [r for r in registros if r["id"] != registro_id]
    await update.effective_message.reply_text(f"Registro ID {registro_id} excluído.")

async def enviar_grafico(update: Update, context: CallbackContext):
    if not verificar_usuario(update):
        await update.effective_message.reply_text("Você não tem permissão para usar este bot.")
        return
    mes = get_mes_atual()
    dados_mes = [r for r in registros if r["data"].startswith(mes)]
    if not dados_mes:
        await update.effective_message.reply_text(f"Não há registros para gerar gráfico em {mes}.")
        return
    df = pd.DataFrame(dados_mes)
    relatorio = df.groupby("categoria")["valor"].sum().reset_index()
    plt.figure(figsize=(8, 4))
    plt.bar(relatorio["categoria"], relatorio["valor"], color="skyblue")
    plt.xlabel("Categoria")
    plt.ylabel("Valor gasto")
    plt.title(f"Gastos por Categoria - {mes}")
    plt.tight_layout()
    grafico_filename = f"grafico_{mes}.png"
    plt.savefig(grafico_filename)
    plt.close()
    with open(grafico_filename, "rb") as photo:
        await update.effective_message.reply_photo(photo, caption=f"Gráfico de gastos para {mes}")
    os.remove(grafico_filename)

async def backup_historico(update: Update, context: CallbackContext):
    if not verificar_usuario(update):
        await update.effective_message.reply_text("Você não tem permissão para usar este bot.")
        return
    df = pd.DataFrame(registros)
    backup_filename = "backup_historico.csv"
    df.to_csv(backup_filename, index=False)
    with open(backup_filename, "rb") as doc:
        await update.effective_message.reply_document(document=doc, filename=backup_filename)
    os.remove(backup_filename)

async def listar_gastos(update: Update, context: CallbackContext):
    if not verificar_usuario(update):
        await update.effective_message.reply_text("Você não tem permissão para usar este bot.")
        return
    if not registros:
        await update.effective_message.reply_text("Nenhum gasto registrado.")
        return
    mensagem = "Lista de todos os gastos:\n"
    for r in registros:
        mensagem += f"ID {r['id']}: {r['data']} - {r['categoria']} - R${r['valor']:.2f}\n"
    await update.effective_message.reply_text(mensagem)

# automático para gerar relatório (CSV) do mês anterior
def gerar_relatorio_automatico():
    while True:
        agora = datetime.datetime.now()
        if agora.day == 1 and agora.hour == 0:
            mes_anterior = (agora - datetime.timedelta(days=1)).strftime("%Y-%m")
            dados_mes = [r for r in registros if r["data"].startswith(mes_anterior)]
            if dados_mes:
                df = pd.DataFrame(dados_mes)
                csv_filename = f"relatorio_{mes_anterior}.csv"
                df.to_csv(csv_filename, index=False)
                logging.info(f"Relatório do mês {mes_anterior} gerado automaticamente. Arquivo CSV criado.")
        threading.Event().wait(3600)

# automático para enviar resumo periódico
def enviar_resumo_periodico(application: Application):
    last_summary_date = None
    while True:
        agora = datetime.datetime.now()
        if agora.hour == 18 and (last_summary_date != agora.date()):
            hoje = get_data_atual()
            dados_hoje = [r for r in registros if r["data"] == hoje]
            if dados_hoje:
                df = pd.DataFrame(dados_hoje)
                relatorio = df.groupby("categoria")["valor"].sum().reset_index()
                mensagem = f"Resumo do dia {hoje}:\n" + "\n".join(
                    [f"{row.categoria}: R${row.valor:.2f}" for _, row in relatorio.iterrows()]
                )
            else:
                mensagem = f"Resumo do dia {hoje}: Sem registros de gastos."
            asyncio.run_coroutine_threadsafe(
                application.bot.send_message(chat_id=USER_ID, text=mensagem),
                application.loop
            )
            last_summary_date = agora.date()
        threading.Event().wait(3600)

def main():
    #objeto Request com timeout aumentado
    application = Application.builder().token("TOKEN_DO_BOT").build()
    
    application.add_handler(CommandHandler("g", adicionar_gasto))
    application.add_handler(CommandHandler("e", definir_saldo))
    application.add_handler(CommandHandler("csd", consultar_saldo_disponivel))
    application.add_handler(CommandHandler("rm", relatorio_mensal))
    application.add_handler(CommandHandler("editar", editar_registro))
    application.add_handler(CommandHandler("excluir", excluir_registro))
    application.add_handler(CommandHandler("grafico", enviar_grafico))
    application.add_handler(CommandHandler("backup", backup_historico))
    application.add_handler(CommandHandler("lista", listar_gastos))
    
    #threads para tarefas automáticas
    thread_relatorio = threading.Thread(target=gerar_relatorio_automatico, daemon=True)
    thread_relatorio.start()
    
    thread_resumo = threading.Thread(target=enviar_resumo_periodico, args=(application,), daemon=True)
    thread_resumo.start()
    
    application.run_polling()

if __name__ == '__main__':
    main()
