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
ultima_noticia_id = None

# --- WEB SERVER (Koyeb Keep-Alive) ---
web_app = Flask(__name__)
@web_app.route('/')
def home(): return "Arch Cloud Bot v5.0 Online"

def run_web_app():
    port = int(os.environ.get("PORT", 8080))
    web_app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

# --- LÓGICA DE SEMÁFORO Y IA ---

def clasificar_riesgo(pkg_name):
    """Devuelve un emoji según la importancia del paquete"""
    nombre = pkg_name.lower()
    
    # 🔴 CRÍTICO: Si se rompe esto, el sistema no arranca o falla gravemente
    criticos = ['linux', 'linux-lts', 'systemd', 'grub', 'pacman', 'glibc', 'gcc', 'filesystem']
    if any(c in nombre for c in criticos):
        return "🔴"
    
    # 🟡 PRECAUCIÓN: Gráficos y entornos de escritorio
    medios = ['nvidia', 'mesa', 'wayland', 'xorg', 'plasma', 'gnome', 'qt', 'gtk', 'pipewire']
    if any(m in nombre for m in medios):
        return "🟡"
        
    # 🟢 SEGURO: Aplicaciones y librerías menores
    return "🟢"

def consultar_ia(prompt_usuario, modo="breve"):
    """
    modo='breve': Max 300 palabras, respuesta directa.
    modo='deep': Sin limite estricto (recortado por Telegram), razonamiento profundo.
    """
    sistema = "Sos un experto en Arch Linux. Sé conciso y directo."
    if modo == "deep":
        sistema = "Sos un ingeniero experto en Linux. Analizá paso a paso, explicá el por qué y da ejemplos técnicos. Usá Markdown."
    else:
        sistema += " Resumí tu respuesta en menos de 150 palabras."

    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": sistema},
                {"role": "user", "content": prompt_usuario}
            ]
        )
        res = completion.choices[0].message.content
        # Recorte de seguridad para Telegram (4096 chars)
        return res[:4000] if len(res) > 4000 else res
    except Exception as e:
        return f"❌ Error de IA: {e}"

def explicar_paquete_breve(pkg_name):
    """Usa IA para una descripción de 1 línea en los updates"""
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "Define este paquete de Arch Linux en máximo 10 palabras."},
                {"role": "user", "content": pkg_name}
            ]
        )
        return completion.choices[0].message.content
    except: return "Sin información."

# --- MONITOREO AUTOMÁTICO ---

async def verificar_noticias_automatico(context: ContextTypes.DEFAULT_TYPE):
    global ultima_noticia_id
    try:
        feed = feedparser.parse("https://archlinux.org/feeds/packages/")
        if not feed.entries: return
        
        nueva_entry = feed.entries[0]
        if ultima_noticia_id is None:
            ultima_noticia_id = nueva_entry.id
            return

        if nueva_entry.id != ultima_noticia_id:
            ultima_noticia_id = nueva_entry.id
            pkg_name = nueva_entry.title.split(' ')[0]
            
            emoji = clasificar_riesgo(pkg_name)
            desc = explicar_paquete_breve(pkg_name)
            
            # Solo avisar si es crítico o medio (Opcional: quitar filtro para avisar de todo)
            aviso = f"📢 *UPDATE DETECTADO*"
            if emoji == "🔴": aviso = "🚨 *¡UPDATE CRÍTICO!*"
            
            mensaje = f"{aviso}\n\n{emoji} *{nueva_entry.title}*\n📝 _{desc}_"
            await context.bot.send_message(chat_id=USUARIO_ID, text=mensaje, parse_mode='Markdown')
    except Exception as e:
        print(f"Error monitoreo: {e}")

# --- COMANDOS ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    guia = (
        "🤖 *ArchNotifier v5.0*\n\n"
        "🚦 *Semaforo de Riesgo:*\n"
        "🔴 Kernel/Boot | 🟡 Drivers/GUI | 🟢 Apps\n\n"
        "💻 *Comandos:*\n"
        "`/updates` - Ver últimos 5 paquetes\n"
        "`/ask [clave] [pregunta]` - Respuesta rápida\n"
        "`/ask [clave] deep [pregunta]` - Razonamiento profundo"
    )
    await update.message.reply_text(guia, parse_mode='Markdown')

async def updates(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚦 Analizando repositorios...", parse_mode='Markdown')
    feed = feedparser.parse("https://archlinux.org/feeds/packages/")
    rep = "🌐 *ÚLTIMOS 5 PAQUETES*\n\n"
    
    for e in feed.entries[:5]:
        pkg = e.title.split(' ')[0]
        emoji = clasificar_riesgo(pkg)
        desc = explicar_paquete_breve(pkg)
        rep += f"{emoji} *{e.title}*\n|_{desc}_\n\n"
        
    await update.message.reply_text(rep, parse_mode='Markdown')

async def ask(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Validación básica de argumentos
    if not context.args or len(context.args) < 2:
        await update.message.reply_text("⚠️ Uso: `/ask [clave] [pregunta]` o `/ask [clave] deep [pregunta]`", parse_mode='Markdown')
        return

    # Validar Clave
    clave_user = context.args[0]
    if clave_user != BOT_SECRET:
        await update.message.reply_text("⛔ Clave incorrecta.")
        return

    # Lógica Deep vs Breve
    # Chequeamos si la segunda palabra es 'deep'
    if context.args[1].lower() == 'deep':
        modo = "deep"
        pregunta = " ".join(context.args[2:]) # Saltamos clave y 'deep'
        msg_loading = "🧠 *Pensando a fondo...* (Modo Deep)"
    else:
        modo = "breve"
        pregunta = " ".join(context.args[1:]) # Saltamos solo la clave
        msg_loading = "💡 *Analizando...* (Modo Breve)"

    if not pregunta:
        await update.message.reply_text("🤔 ¿Y la pregunta?")
        return

    msg = await update.message.reply_text(msg_loading, parse_mode='Markdown')
    respuesta = consultar_ia(pregunta, modo=modo)
    await msg.edit_text(respuesta, parse_mode='Markdown')

# --- MAIN ---

if __name__ == "__main__":
    if TOKEN:
        threading.Thread(target=run_web_app, daemon=True).start()
        app = ApplicationBuilder().token(TOKEN).build()
        
        # Monitoreo cada 1 hora (3600s)
        app.job_queue.run_repeating(verificar_noticias_automatico, interval=3600, first=10)
        
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("updates", updates))
        app.add_handler(CommandHandler("ask", ask))
        
        print("🤖 Bot v5.0 (Traffic Light Edition) listo...")
        app.run_polling()