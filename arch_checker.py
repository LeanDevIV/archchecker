import subprocess, asyncio, os, feedparser
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from flask import Flask
import threading
import os

# --- CONFIGURACIÓN ---
# Carga el .env solo si existe (para local), si no, usa las del sistema (para Koyeb)
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.isfile(dotenv_path):
    load_dotenv(dotenv_path)

TOKEN = os.getenv('TELEGRAM_TOKEN')
raw_id = os.getenv('MY_CHAT_ID')

# Verificación extra para depurar
if not TOKEN:
    print("❌ ERROR: TELEGRAM_TOKEN no detectado en el entorno.")
if not raw_id:
    print("❌ ERROR: MY_CHAT_ID no detectado en el entorno.")

try:
    USUARIO_ID = int(raw_id) if raw_id else 0
except ValueError:
    print(f"❌ ERROR: MY_CHAT_ID tiene un formato inválido: {raw_id}")
    USUARIO_ID = 0

USUARIOS_PERMITIDOS = [USUARIO_ID]
def ejecutar_comando(comando):
    try:
        r = subprocess.run(comando, capture_output=True, text=True, shell=False)
        return r.stdout.strip() if r.returncode == 0 else f"Error: {r.stderr}"
    except Exception as e: return f"❌ Fallo: {e}"

def obtener_ultimas_noticias_arch():
    try:
        feed = feedparser.parse("https://archlinux.org/feeds/packages/")
        if not feed.entries: return "No se encontraron noticias."
        rep = "🌐 *ÚLTIMOS REPOS OFICIALES*\n\n"
        for e in feed.entries[:5]:
            rep += f"🔹 *{e.title}*\n"
        return rep
    except Exception as e: return f"❌ Error: {e}"

# --- MANEJADORES ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in USUARIOS_PERMITIDOS: return
    guia = ("🤖 *ArchNotifier v2.2*\n\n"
            "/check - Tus updates\n/updates - Repos globales\n"
            "/fastfetch - Hardware\n/disco - Almacenamiento\n/logs - Errores")
    await update.message.reply_text(guia, parse_mode='Markdown')

async def updates(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in USUARIOS_PERMITIDOS: return
    await update.message.reply_text(obtener_ultimas_noticias_arch(), parse_mode='Markdown')

async def check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in USUARIOS_PERMITIDOS: return
    raw = ejecutar_comando(['checkupdates'])
    lista = [l for l in raw.split('\n') if l and "Error" not in l]
    if not lista:
        await update.message.reply_text("✅ ¡Todo al día!")
        return
    criticos = ['linux', 'nvidia', 'grub', 'systemd', 'glibc', 'xorg', 'wayland']
    riesgo = [f"⚠️ {p}" for p in lista if any(k in p.lower() for k in criticos)]
    txt = f"📦 *TUS UPDATES*\nTotal: {len(lista)}\n\n"
    if riesgo: txt += "*RIESGO:* \n" + "\n".join(riesgo[:10])
    await update.message.reply_text(txt, parse_mode='Markdown')

async def fastfetch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in USUARIOS_PERMITIDOS: return
    info = ejecutar_comando(['fastfetch', '--pipe'])
    await update.message.reply_text(f"🚀 *SISTEMA*\n```\n{info}\n```", parse_mode='Markdown')

async def disco(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in USUARIOS_PERMITIDOS: return
    uso = ejecutar_comando(['df', '-h', '/', '/home'])
    await update.message.reply_text(f"💾 *DISCO*\n```\n{uso}\n```", parse_mode='Markdown')

async def logs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in USUARIOS_PERMITIDOS: return
    err = ejecutar_comando(['journalctl', '-p', '3', '-n', '5', '--no-pager'])
    await update.message.reply_text(f"⚠️ *LOGS*\n```\n{err or 'Sin errores'}\n```", parse_mode='Markdown')

# --- MINI SERVIDOR WEB PARA KOYEB ---
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "🤖 Bot de Arch de Salt online 24/7"

def run_web_app():
    # Koyeb inyecta automáticamente el puerto en la variable de entorno PORT
    port = int(os.environ.get("PORT", 8080))
    # Ponemos debug=False para producción y evitamos conflictos de hilos
    web_app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

    
if __name__ == "__main__":
    if not TOKEN or USUARIO_ID == 0:
        print("❌ ERROR: No se encontraron las variables en el .env")
    else:
        # 1. Arrancamos el servidor web en un hilo paralelo (Background)
        # Esto engaña a Koyeb haciéndole creer que es una web app
        print("🌐 Iniciando servidor de salud en el puerto 8080...")
        threading.Thread(target=run_web_app, daemon=True).start()

        # 2. Iniciamos el Bot de Telegram normalmente
        print("🤖 Bot resucitado y escuchando...")
        app = ApplicationBuilder().token(TOKEN).build()
        
        # Registro de comandos
        for cmd, func in [
            ("start", start), 
            ("updates", updates), 
            ("check", check), 
            ("fastfetch", fastfetch), 
            ("disco", disco), 
            ("logs", logs)
        ]:
            app.add_handler(CommandHandler(cmd, func))
        
        # Mantenemos el bot corriendo
        app.run_polling()