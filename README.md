# 🛡️ ArchChecker

> **Herramienta personal de monitoreo para Arch Linux con análisis de riesgo basado en IA.**

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python)
![Arch Linux](https://img.shields.io/badge/Arch%20Linux-Critical-1793d1?style=for-the-badge&logo=arch-linux)
![Koyeb](https://img.shields.io/badge/Deploy-Koyeb-black?style=for-the-badge&logo=koyeb)
![Groq](https://img.shields.io/badge/AI-Groq%20Llama%203-orange?style=for-the-badge)

## 📖 Sobre el Proyecto

Este proyecto nació como una solución personal para resolver un problema clásico de los usuarios de Arch Linux: **"¿Qué voy a romper si actualizo hoy?"**.

**Archchecker** es un bot de Telegram que vive en la nube (24/7) y monitorea automáticamente el feed RSS oficial de paquetes de Arch. No solo te avisa cuando hay actualizaciones, sino que utiliza la **API de Groq (modelo Llama 3)** para analizar qué hace cada paquete y evaluar el riesgo de la actualización antes de que toques tu terminal.

### ✨ Características Principales

* **☁️ Cloud Native:** Desplegado en **Koyeb** utilizando un servidor Flask ligero para mantener el servicio activo ("Keep-Alive").
* **🧠 Análisis con IA:** Integra **Groq Cloud** para explicar en lenguaje natural qué función cumple cada librería o paquete.
* **🚨 Detección de Riesgo:** Identifica automáticamente actualizaciones críticas (Kernel, Drivers Nvidia, GRUB, Systemd) y envía alertas visuales.
* **⏰ Monitoreo Automático:** Utiliza `JobQueue` para escanear los repositorios cada 60 minutos sin intervención humana.
* **🔐 Modo Híbrido:**
    * **Admin:** Comandos exclusivos para el dueño (logs, force update).
    * **Público (con llave):** Comando `/ask` protegido por contraseña para consultas técnicas con la IA.

---

## 🛠️ Tecnologías Utilizadas

Este bot fue construido utilizando las siguientes librerías y servicios:

* **[Python-Telegram-Bot](https://python-telegram-bot.org/):** Framework asíncrono para la API de Telegram.
* **[Groq API](https://groq.com/):** Inferencia de IA ultra-rápida usando modelos Llama-3.
* **[Feedparser](https://feedparser.readthedocs.io/):** Para consumir el RSS de Arch Linux.
* **[Flask](https://flask.palletsprojects.com/):** Micro-servidor web para satisfacer los Health Checks de Koyeb.
* **[Koyeb](https://www.koyeb.com/):** Plataforma Serverless para el despliegue.

---

## 🚀 Instalación y Uso Local

Si querés clonar este proyecto y correrlo en tu máquina o modificarlo:

1.  **Clonar el repositorio:**
    ```bash
    git clone [https://github.com/LeanDevIV/archchecker](https://github.com/LeanDevIV/archchecker)
    cd archchecker
    ```

2.  **Crear entorno virtual e instalar dependencias:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # En Linux/Mac
    pip install -r requirements.txt
    ```

3.  **Configurar variables de entorno:**
    Creá un archivo `.env` en la raíz con lo siguiente:
    ```ini
    TELEGRAM_TOKEN=tu_token_de_botfather
    MY_CHAT_ID=tu_id_numerico_de_telegram
    GROQ_API_KEY=tu_api_key_de_groq
    BOT_SECRET_KEY=sanguche_de_milanesa  # Clave para usar /ask
    ```

4.  **Ejecutar:**
    ```bash
    python arch_checker.py
    ```

---

## ☁️ Despliegue en Koyeb

Este proyecto está optimizado para **Koyeb**.

1.  Conectá tu repositorio de GitHub a Koyeb.
2.  Seleccioná el tipo de servicio como **Web Service**.
3.  En la configuración de **Build & Deployment**:
    * **Build Command:** (Dejar vacío, usa detección automática de Python).
    * **Run Command:** `python arch_checker.py` (o usará el `Procfile` automáticamente).
4.  **Variables de Entorno:**
    Cargá las mismas variables del `.env` (`TELEGRAM_TOKEN`, `GROQ_API_KEY`, etc.) en el panel de Koyeb.
5.  **Puertos:** Asegurate de exponer el puerto **8080** (HTTP), que es donde escucha el servidor Flask "fantasma".

---

## 🤖 Comandos del Bot

| Comando | Descripción | Acceso |
| :--- | :--- | :--- |
| `/start` | Muestra el panel de bienvenida y estado. | Público |
| `/ask [clave] [duda]` | Consulta técnica a la IA sobre Arch/Linux. | Requiere Clave |
| `/updates` | Fuerza un chequeo manual del feed y muestra los últimos 3. | Admin |
| `/logs` | Verifica el estado de salud del servicio en la nube. | Admin |

---

## ⚠️ Disclaimer

Este es un proyecto personal con fines educativos y de experimentación. Aunque analiza riesgos, **siempre leé la [Wiki de Arch](https://wiki.archlinux.org/) antes de actualizar**.
---
## Contacto
¿Tienes dudas? [Escríbeme un correo](mailto:leandrocordoba318@gmail.com) o visita mi perfil
---
Hecho con mucho 🧉, cariño e insomnio.
.

