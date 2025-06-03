import feedparser
import requests
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import os
from openai import OpenAI

# Cargar variables de entorno
load_dotenv()

gmail_address = os.getenv("GMAIL_ADDRESS")
gmail_password = os.getenv("GMAIL_PASSWORD")
email_receiver = os.getenv("EMAIL_RECEIVER")
openai_api_key = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=openai_api_key)

# Fuentes RSS
rss_feeds = {
    "The Economist": "https://www.economist.com/the-world-this-week/rss.xml",
    "Reuters": "http://feeds.reuters.com/reuters/businessNews",
    "Gestión Perú": "https://gestion.pe/arcio/rss/",
    "Wall Street Journal": "https://feeds.a.dj.com/rss/RSSMarketsMain.xml",
    "Forbes": "https://www.forbes.com/business/feed/",
    "Forbes México": "https://www.forbes.com.mx/feed/",
    "New York Times": "https://rss.nytimes.com/services/xml/rss/nyt/Business.xml"
}

def obtener_noticias(rss_url, limite=2):
    feed = feedparser.parse(rss_url)
    return feed.entries[:limite]

def resumir_noticia(titulo, descripcion, link):
    prompt = (
        f"Resume la siguiente noticia en español de forma concisa y clara, en un párrafo breve sin copiar literalmente:\n\n"
        f"Título: {titulo}\nDescripción: {descripcion}\nLink: {link}\n\nResumen:"
    )
    try:
        respuesta = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5
        )
        return respuesta.choices[0].message.content.strip()
    except Exception as e:
        return f"[Error al resumir la noticia: {e}]"

def generar_resumenes():
    resumenes = {}
    for fuente, url in rss_feeds.items():
        noticias = obtener_noticias(url)
        resumenes[fuente] = []
        for entrada in noticias:
            titulo = entrada.title
            descripcion = entrada.get("summary", "")
            link = entrada.link
            resumen = resumir_noticia(titulo, descripcion, link)
            resumenes[fuente].append({
                "titulo": titulo,
                "resumen": resumen,
                "link": link
            })
    return resumenes

def enviar_email(resumenes):
    mensaje = MIMEMultipart("alternative")
    mensaje["Subject"] = "📰 Resumen diario de noticias de negocios"
    mensaje["From"] = gmail_address
    mensaje["To"] = email_receiver

    html = """\
    <html>
      <body style="font-family: Arial, sans-serif;">
        <h2>🗞️ Noticias destacadas de hoy</h2>
    """

    for fuente, noticias in resumenes.items():
        html += f"<h3>{fuente}</h3><ul>"
        for noticia in noticias:
            html += f"""
            <li>
              <p><strong>{noticia['titulo']}</strong><br>
              {noticia['resumen']}<br>
              <a href="{noticia['link']}">Leer más</a></p>
            </li>
            """
        html += "</ul>"

    html += """\
      </body>
    </html>
    """

    mensaje.attach(MIMEText(html, "html"))

    contexto = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=contexto) as server:
        server.login(gmail_address, gmail_password)
        server.sendmail(gmail_address, email_receiver, mensaje.as_string())

if __name__ == "__main__":
    print("📡 Obteniendo noticias y generando resumen...")
    resumenes = generar_resumenes()
    print("✉️ Enviando correo...")
    enviar_email(resumenes)
    print("✅ Correo enviado.")


