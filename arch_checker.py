import subprocess, asyncio, os, feedparser
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# --- CONFIGURACIÓN ---
load_dotenv()
TOKEN = os.getenv('TELEGRAM_TOKEN')
try:
    USUARIO_ID = int(os.getenv('MY_CHAT_ID'))
except (TypeError, ValueError):
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

if __name__ == "__main__":
    if TOKEN and USUARIO_ID != 0:
        app = ApplicationBuilder().token(TOKEN).build()
        for cmd, func in [("start", start), ("updates", updates), ("check", check), 
                          ("fastfetch", fastfetch), ("disco", disco), ("logs", logs)]:
            app.add_handler(CommandHandler(cmd, func))
        print("🤖 Bot online..."); app.run_polling()
