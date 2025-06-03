import os
import feedparser
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
gmail_address = os.getenv("GMAIL_ADDRESS")
gmail_password = os.getenv("GMAIL_PASSWORD")
email_receiver = os.getenv("EMAIL_RECEIVER")

rss_feeds = [
    "https://rss.nytimes.com/services/xml/rss/nyt/Business.xml",
    "https://feeds.a.dj.com/rss/RSSMarketsMain.xml",
    "http://feeds.bbci.co.uk/news/technology/rss.xml",
    "http://feeds.reuters.com/reuters/technologyNews",
    "http://rss.cnn.com/rss/money_news_international.rss",
    "https://www.economist.com/the-world-this-week/rss.xml",
    "https://www.forbes.com/most-popular/feed/",
    "https://www.ft.com/?format=rss",
    "https://elcomercio.pe/arcio/rss/",
    "https://gestion.pe/arcio/rss/",
    "https://rpp.pe/feed",
    "https://www.forbes.com.mx/feed/",
    "https://reforma.com/rss/portada.xml",
    "https://milenio.com/rss",
    "https://www.mckinsey.com/rss",
    "https://www.bcg.com/feeds/publications",
    "https://www.bain.com/about/media-center/rss-feeds/",
    "https://www2.deloitte.com/content/dam/insights/us/rss/DI-rss.xml",
    "https://www.strategyand.pwc.com/gx/en/rss.xml",
    "https://www.ey.com/en_gl/insights/rss",
]

def clasificar_y_traducir(titulo, descripcion):
    prompt = (
        f"Clasifica la siguiente noticia en una de estas categorías: Tecnología, Negocios, Economía. "
        f"Traduce el título y el resumen al español neutral si están en otro idioma. "
        f"Responde en formato JSON así: "
        f'{{"categoria": "...", "titulo": "...", "resumen": "..."}}\n\n'
        f"Título: {titulo}\nDescripción: {descripcion}"
    )
    respuesta = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    return eval(respuesta.choices[0].message.content)

def obtener_resumenes():
    resumenes = {"Tecnología": [], "Negocios": [], "Economía": []}
    for url in rss_feeds:
        feed = feedparser.parse(url)
        for entrada in feed.entries[:5]:
            try:
                resultado = clasificar_y_traducir(entrada.title, entrada.get("summary", ""))
                categoria = resultado["categoria"]
                if categoria in resumenes and len(resumenes[categoria]) < 7:
                    resumenes[categoria].append({
                        "titulo": resultado["titulo"],
                        "resumen": resultado["resumen"],
                        "link": entrada.link,
                        "fuente": feed.feed.get("title", "Fuente desconocida")
                    })
            except Exception:
                continue
    return resumenes

def enviar_email(resumenes):
    asunto = "Centro de Noticias GaamP"
    mensaje = MIMEMultipart("alternative")
    mensaje["Subject"] = asunto
    mensaje["From"] = "GaamP Noticias"
    mensaje["To"] = email_receiver

    html = "<html><body>"
    html += '<h2 style="text-align:center;">Centro de Noticias GaamP</h2>'
    for categoria in ["Tecnología", "Negocios", "Economía"]:
        html += f'<h3 style="color:#003366;">🗂️ {categoria}</h3><ul>'
        for noticia in resumenes[categoria]:
            html += f'''
                <li>
                    <strong>{noticia["titulo"]}</strong><br>
                    <em>{noticia["resumen"]}</em><br>
                    <a href="{noticia["link"]}">Leer más</a> - <span style="color:gray;">{noticia["fuente"]}</span>
                </li><br>
            '''
        html += "</ul><hr>"
    html += "<p style='font-size:12px;color:gray;'>Enviado automáticamente por el Agente de Noticias GaamP</p>"
    html += "</body></html>"

    parte_html = MIMEText(html, "html")
    mensaje.attach(parte_html)

    contexto = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=contexto) as servidor:
        servidor.login(gmail_address, gmail_password)
        servidor.sendmail(gmail_address, email_receiver, mensaje.as_string())

if __name__ == "__main__":
    resumenes = obtener_resumenes()
    enviar_email(resumenes)

