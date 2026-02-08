import os, subprocess, asyncio, feedparser, requests, threading
from flask import Flask
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from groq import Groq

# --- CONFIGURACIÓN ---
load_dotenv()
TOKEN = os.getenv('TELEGRAM_TOKEN')
# Palabra clave para el comando /ask (puedes setearla en Koyeb)
BOT_SECRET = os.getenv('BOT_SECRET_KEY', 'tucuman_dev_2026')
raw_id = os.getenv('MY_CHAT_ID')
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

try:
    USUARIO_ID = int(raw_id) if raw_id else 0
except ValueError:
    USUARIO_ID = 0

# Lista de administradores para comandos críticos
USUARIOS_PERMITIDOS = [USUARIO_ID]

# --- WEB SERVER PARA KOYEB (Health Check) ---
web_app = Flask(__name__)
@web_app.route('/')
def home(): return "Arch Cloud Bot Online 24/7"

def run_web_app():
    port = int(os.environ.get("PORT", 8080))
    web_app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

# --- PROCESADOR DE IA Y PAQUETES ---

def consulta_profunda(pregunta):
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system", 
                    "content": "Sos un experto senior en Arch Linux. Respondé de forma concisa y técnica. Máximo 300 palabras. Usá Markdown."
                },
                {"role": "user", "content": pregunta}
            ]
        )
        respuesta = completion.choices[0].message.content
        return respuesta[:4000] if len(respuesta) > 4000 else respuesta
    except Exception as e:
        return f"❌ Error al consultar a la IA: {e}"

def explicar_con_ia(nombre_pkg):
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system", 
                    "content": "Sos un experto en Arch Linux. Explicá brevemente (máximo 15 palabras) qué hace este paquete de software."
                },
                {"role": "user", "content": nombre_pkg}
            ]
        )
        return completion.choices[0].message.content
    except:
        return "Info técnica no disponible."

def obtener_novedades_oficiales():
    try:
        feed = feedparser.parse("https://archlinux.org/feeds/packages/")
        rep = "🌐 *REPOS CON IA DESCRIPTIVA*\n\n"
        for e in feed.entries[:3]:
            pkg_name = e.title.split(' ')[0]
            explicacion = explicar_con_ia(pkg_name)
            rep += f"📦 *{e.title}*\n🤖 _{explicacion}_\n\n"
        return rep
    except Exception as e:
        return f"❌ Error: {e}"

# --- MANEJADORES DE COMANDOS ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    guia = (
        "🤖 *ArchNotifier Cloud v3.0*\n\n"
        "🔓 *Comandos Públicos:*\n"
        "/ask [clave] [pregunta] - Consulta a la IA\n\n"
        "🔐 *Comandos Admin:*\n"
        "/updates - Novedades de repos\n"
        "/logs - Estado del servicio"
    )
    await update.message.reply_text(guia, parse_mode='Markdown')

async def updates(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in USUARIOS_PERMITIDOS: return
    await update.message.reply_text("🧐 Analizando los últimos paquetes...")
    await update.message.reply_text(obtener_novedades_oficiales(), parse_mode='Markdown')

async def logs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in USUARIOS_PERMITIDOS: return
    await update.message.reply_text("✅ Bot online en Koyeb. IA activa.")

async def ask(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Sin restricción de ID para que sea semi-público
    if not context.args or len(context.args) < 2:
        await update.message.reply_text("🤔 *Uso:* `/ask [clave] [pregunta]`\nEj: `/ask mi_clave ¿Qué es pacman?`", parse_mode='Markdown')
        return

    clave_user = context.args[0]
    pregunta = " ".join(context.args[1:])

    if clave_user != BOT_SECRET:
        await update.message.reply_text("⛔ Clave incorrecta. No estás autorizado.")
        return

    await update.message.reply_text(f"🧠 *Autorizado.* Consultando sobre: {pregunta}...")
    respuesta = consulta_profunda(pregunta)
    await update.message.reply_text(respuesta, parse_mode='Markdown')

# --- INICIO ---

if __name__ == "__main__":
    if TOKEN:
        threading.Thread(target=run_web_app, daemon=True).start()
        app = ApplicationBuilder().token(TOKEN).build()
        
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("updates", updates))
        app.add_handler(CommandHandler("logs", logs))
        app.add_handler(CommandHandler("ask", ask))
        
        print("🤖 Bot Cloud listo para la acción...")
        app.run_polling()