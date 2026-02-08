import os, feedparser, requests, threading, asyncio
from flask import Flask
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from groq import Groq

# --- CONFIGURACIÓN ---
load_dotenv()
TOKEN = os.getenv('TELEGRAM_TOKEN')
BOT_SECRET = os.getenv('BOT_SECRET_KEY', 'tucuman_dev_2026')
raw_id = os.getenv('MY_CHAT_ID')
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

try:
    USUARIO_ID = int(raw_id) if raw_id else 0
except ValueError:
    USUARIO_ID = 0

USUARIOS_PERMITIDOS = [USUARIO_ID]

# Variable global para evitar spam de noticias repetidas
ultima_noticia_id = None

# --- WEB SERVER PARA KOYEB (Health Check) ---
web_app = Flask(__name__)
@web_app.route('/')
def home(): return "Arch Cloud Bot Online 24/7"

def run_web_app():
    port = int(os.environ.get("PORT", 8080))
    web_app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

# --- PROCESADOR DE IA ---

def explicar_con_ia(nombre_pkg, profundo=False):
    """Maneja tanto explicaciones breves como consultas profundas"""
    prompt = "Sos un experto en Arch Linux. Explicá brevemente (15 palabras) qué hace este paquete."
    if profundo:
        prompt = "Sos un experto senior en Arch Linux. Respondé de forma concisa y técnica. Máximo 300 palabras. Usá Markdown."
    
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": nombre_pkg}
            ]
        )
        res = completion.choices[0].message.content
        return res[:4000] if len(res) > 4000 else res
    except Exception as e:
        return f"❌ Error de IA: {e}"

# --- LÓGICA DE MONITOREO AUTOMÁTICO ---

async def verificar_noticias_automatico(context: ContextTypes.DEFAULT_TYPE):
    global ultima_noticia_id
    try:
        feed = feedparser.parse("https://archlinux.org/feeds/packages/")
        if not feed.entries: return
        
        nueva_entry = feed.entries[0]
        
        # Inicialización en el primer arranque
        if ultima_noticia_id is None:
            ultima_noticia_id = nueva_entry.id
            return

        # Si el ID cambió, hay un paquete nuevo
        if nueva_entry.id != ultima_noticia_id:
            ultima_noticia_id = nueva_entry.id
            pkg_name = nueva_entry.title.split(' ')[0]
            desc = explicar_con_ia(pkg_name)
            
            # Alerta visual si es core/crítico
            alertas = ['linux', 'grub', 'systemd', 'nvidia', 'pacman']
            emoji = "📢"
            if any(k in pkg_name.lower() for k in alertas):
                emoji = "🚨 *¡ALERTA CRÍTICA!*"
            
            mensaje = f"{emoji}\n\n📦 *{nueva_entry.title}*\n🤖 _{desc}_"
            await context.bot.send_message(chat_id=USUARIO_ID, text=mensaje, parse_mode='Markdown')
    except Exception as e:
        print(f"Error en monitoreo: {e}")

# --- MANEJADORES DE COMANDOS ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    guia = (
        "🤖 *ArchNotifier Cloud v4.0*\n\n"
        "🔓 *Público:* `/ask [clave] [pregunta]`\n"
        "🔐 *Admin:* `/updates`, `/logs`\n\n"
        "📡 *Estado:* Monitoreo automático cada 30 min."
    )
    await update.message.reply_text(guia, parse_mode='Markdown')

async def updates(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in USUARIOS_PERMITIDOS: return
    await update.message.reply_text("🧐 Analizando el feed oficial...")
    
    feed = feedparser.parse("https://archlinux.org/feeds/packages/")
    rep = "🌐 *ÚLTIMOS REPOS*\n\n"
    for e in feed.entries[:3]:
        pkg = e.title.split(' ')[0]
        rep += f"📦 *{e.title}*\n🤖 _{explicar_con_ia(pkg)}_\n\n"
    await update.message.reply_text(rep, parse_mode='Markdown')

async def ask(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or len(context.args) < 2:
        await update.message.reply_text("🤔 `/ask [clave] [pregunta]`")
        return
    
    if context.args[0] != BOT_SECRET:
        await update.message.reply_text("⛔ Clave incorrecta.")
        return

    pregunta = " ".join(context.args[1:])
    msg = await update.message.reply_text(f"🧠 Consultando sobre *{pregunta}*...")
    respuesta = explicar_con_ia(pregunta, profundo=True)
    await msg.edit_text(respuesta, parse_mode='Markdown')

async def logs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in USUARIOS_PERMITIDOS: return
    await update.message.reply_text("✅ Bot en Koyeb: OK\n✅ Monitoreo: Activo")

# --- BLOQUE PRINCIPAL ---

if __name__ == "__main__":
    if TOKEN:
        # Iniciar Flask en hilo aparte
        threading.Thread(target=run_web_app, daemon=True).start()
        
        # Configurar Application con JobQueue
        app = ApplicationBuilder().token(TOKEN).build()
        
        # Tarea repetitiva: cada 3600 segundos (60 min)
        app.job_queue.run_repeating(verificar_noticias_automatico, interval=3600, first=10)
        
        # Handlers
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("updates", updates))
        app.add_handler(CommandHandler("logs", logs))
        app.add_handler(CommandHandler("ask", ask))
        
        print("🤖 Bot Cloud v4.0 listo. Monitoreo automático iniciado.")
        app.run_polling()