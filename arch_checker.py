import os, subprocess, asyncio, feedparser, requests, threading
from flask import Flask
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from groq import Groq

# --- CONFIGURACIÓN ---
load_dotenv()
TOKEN = os.getenv('TELEGRAM_TOKEN')
raw_id = os.getenv('MY_CHAT_ID')
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

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

def consulta_profunda(pregunta):
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system", 
                    "content": "Sos un experto senior en Arch Linux y desarrollo de software. Explicá de forma clara, técnica pero amigable. Si te preguntan por una librería, mencioná para qué sirve y una ventaja de usarla."
                },
                {"role": "user", "content": pregunta}
            ]
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"❌ Error al consultar a la IA: {e}"

def explicar_paquete(nombre_full):
    # Limpiamos el nombre: tomamos solo la primera parte antes del espacio
    # y antes de cualquier guion que separe la versión.
    nombre_limpio = nombre_full.split(' ')[0].split('-')[0]
    
    url = f"https://archlinux.org/rpc/packages/details/{nombre_limpio}/"
    try:
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            data = r.json()
            desc = data.get('desc', 'Sin descripción.')
            return (desc[:120] + '...') if len(desc) > 120 else desc
    except:
        pass
    return "Info técnica no disponible."
def explicar_con_ia(nombre_pkg):
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile", # Modelo potente y rápido
            messages=[
                {
                    "role": "system", 
                    "content": "Sos un experto en Arch Linux. Explicá brevemente (máximo 15 palabras) qué hace este paquete de software en términos sencillos."
                },
                {"role": "user", "content": nombre_pkg}
            ]
        )
        return completion.choices[0].message.content
    except Exception as e:
        return "No pude procesar la info con IA."
def obtener_novedades_oficiales():
    try:
        feed = feedparser.parse("https://archlinux.org/feeds/packages/")
        rep = "🌐 *REPOS CON IA DESCRIPTIVA*\n\n"
        
        for e in feed.entries[:3]:
            # Limpiamos el nombre para que la IA no se confunda con versiones
            pkg_name = e.title.split(' ')[0]
            explicacion = explicar_con_ia(pkg_name)
            
            rep += f"📦 *{e.title}*\n🤖 _{explicacion}_\n\n"
        return rep
    except Exception as e:
        return f"❌ Error: {e}"
    
        

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


async def ask(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in USUARIOS_PERMITIDOS: return
    
    # Verificamos si el usuario escribió algo después del comando
    if not context.args:
        await update.message.reply_text("🤔 ¿Qué querés saber? Tirame algo, ej: `/ask systemd`", parse_mode='Markdown')
        return

    pregunta = " ".join(context.args)
    await update.message.reply_text(f"🧠 Consultando a la IA sobre: *{pregunta}*...", parse_mode='Markdown')
    
    respuesta = consulta_profunda(pregunta)
    await update.message.reply_text(respuesta)
if __name__ == "__main__":
    if TOKEN and USUARIO_ID != 0:
        threading.Thread(target=run_web_app, daemon=True).start()
        app = ApplicationBuilder().token(TOKEN).build()
        
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("updates", updates))
        app.add_handler(CommandHandler("logs", logs))
        app.add_handler(CommandHandler("ask", ask))
        
        print("🤖 Cloud Bot Ready...")
        app.run_polling()