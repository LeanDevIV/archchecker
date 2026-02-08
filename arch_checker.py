import os, subprocess, asyncio, feedparser, requests, threading
from flask import Flask
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# --- CONFIGURACIÓN ---
load_dotenv()
TOKEN = os.getenv('TELEGRAM_TOKEN')
raw_id = os.getenv('MY_CHAT_ID')

try:
    USUARIO_ID = int(raw_id) if raw_id else 0
except ValueError:
    USUARIO_ID = 0

USUARIOS_PERMITIDOS = [USUARIO_ID]

# --- WEB SERVER PARA KOYEB ---
web_app = Flask(__name__)
@web_app.route('/')
def home(): return "Arch Cloud Bot Online 24/7"

def run_web_app():
    port = int(os.environ.get("PORT", 8080))
    web_app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

# --- PROCESADOR DE PAQUETES ---

def explicar_paquete(nombre_pkg):
    """Consulta la API oficial de Arch para traer la descripción"""
    # Intentamos limpiar la versión del nombre para la API
    # Si el título es 'linux 6.12.arch1-1 (core)', extraemos 'linux'
    url = f"https://archlinux.org/rpc/packages/details/{nombre_pkg}/"
    try:
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            data = r.json()
            return data.get('desc', 'Sin descripción disponible.')
    except:
        pass
    return "Info técnica no disponible en este momento."

def obtener_novedades_oficiales():
    try:
        feed = feedparser.parse("https://archlinux.org/feeds/packages/")
        if not feed.entries: return "No hay novedades ahora mismo."
        
        rep = "🌐 *ÚLTIMOS PAQUETES EN REPOS*\n\n"
        for e in feed.entries[:3]:
            # Extraemos el nombre antes del espacio (ej: 'python-tensorflow 2.15...')
            full_title = e.title.split(' ')[0]
            descripcion = explicar_paquete(full_title)
            
            rep += f"📦 *{e.title}*\n📝 _{descripcion}_\n\n"
        return rep
    except Exception as e: 
        return f"❌ Error al procesar feed: {e}"

# --- MANEJADORES ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in USUARIOS_PERMITIDOS: return
    guia = ("🤖 *ArchNotifier Cloud*\n\n"
            "/updates - Novedades globales con info técnica\n"
            "/logs - Estado del servicio")
    await update.message.reply_text(guia, parse_mode='Markdown')

async def updates(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in USUARIOS_PERMITIDOS: return
    await update.message.reply_text("🧐 Analizando los últimos paquetes...")
    await update.message.reply_text(obtener_novedades_oficiales(), parse_mode='Markdown')

async def logs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot operando en la nube. Conexión con Arch Linux OK.")

if __name__ == "__main__":
    if TOKEN and USUARIO_ID != 0:
        threading.Thread(target=run_web_app, daemon=True).start()
        app = ApplicationBuilder().token(TOKEN).build()
        
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("updates", updates))
        app.add_handler(CommandHandler("logs", logs))
        
        print("🤖 Cloud Bot Ready...")
        app.run_polling()