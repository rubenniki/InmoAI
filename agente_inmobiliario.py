"""
AGENTE INMOBILIARIO EN PYTHON (Con User-Agent para evitar bloqueos)
-------------------------------------------------------------------
Búsqueda de Casas/Chalets cerca de Barcelona
- Precio máximo: 320.000 €
- Requisitos: Garaje y Piscina
- Notificaciones automáticas vía Telegram
"""

import os
import json
import time
import logging
import requests
import feedparser

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)

class AgenteInmobiliario:
    def __init__(self, config_path="config.json"):
        self.config_path = config_path
        self.config = self.cargar_configuracion()
        self.historial_file = "viviendas_vistas.json"
        self.vistas = self.cargar_historial()

    def cargar_configuracion(self):
        config_defecto = {
            "precio_maximo": 320000,
            "ubicacion_objetivo": "Barcelona y alrededores",
            "requiere_garaje": True,
            "requiere_piscina": True,
            "telegram": {
                "activo": True,
                "bot_token": "8743113115:AAEIGLZcqAPoS7dEEb0hPerdNZX48_Ly1k8",
                "chat_id": "622267779"
            },
            "intervalo_chequeo_minutos": 30
        }
        if os.path.exists(self.config_path):
            with open(self.config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        else:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(config_defecto, f, indent=4, ensure_ascii=False)
            return config_defecto

    def cargar_historial(self):
        if os.path.exists(self.historial_file):
            with open(self.historial_file, "r", encoding="utf-8") as f:
                return set(json.load(f))
        return set()

    def guardar_historial(self):
        with open(self.historial_file, "w", encoding="utf-8") as f:
            json.dump(list(self.vistas), f, indent=4, ensure_ascii=False)

    def filtrar_propiedad(self, propiedad):
        if propiedad.get("precio", float("inf")) > self.config["precio_maximo"]:
            return False
        if self.config["requiere_garaje"] and not propiedad.get("garaje", False):
            return False
        if self.config["requiere_piscina"] and not propiedad.get("piscina", False):
            return False
        return True

    def enviar_alerta_telegram(self, propiedad):
        telegram_cfg = self.config.get("telegram", {})
        if not telegram_cfg.get("activo", False):
            return

        token = telegram_cfg.get("bot_token")
        chat_id = telegram_cfg.get("chat_id")
        
        mensaje = (
            "🏡 <b>¡NUEVA OPORTUNIDAD REAL ENCONTRADA!</b>\n\n"
            f"📌 <b>{propiedad['titulo']}</b>\n"
            f"📍 <b>Ubicación:</b> {propiedad['ubicacion']}\n"
            f"💰 <b>Precio Máx/Estimado:</b> {propiedad['precio']:,} €\n"
            f"🚗 <b>Garaje/Parking:</b> {'Sí' if propiedad['garaje'] else 'No'}\n"
            f"🏊 <b>Piscina:</b> {'Sí' if propiedad['piscina'] else 'No'}\n\n"
            f"🔗 <a href='{propiedad['url']}'>Ver anuncio completo</a>"
        )

        url_api = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": mensaje,
            "parse_mode": "HTML",
            "disable_web_page_preview": False
        }
        
        try:
            time.sleep(1)
            requests.post(url_api, json=payload, timeout=10)
        except Exception as e:
            logging.error(f"Error conectando con Telegram: {e}")

    def buscar_propiedades(self):
        logging.info("Iniciando búsqueda multi-fuente...")

        # Header de navegador web real para que Trovit no bloquee la petición
        user_agent_browser = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

        urls_rss = [
            "https://inmuebles.trovit.es/index.php/cod.rss_search/type.1/what_d.casa/where_d.Barcelona/price_max.320000",
            "https://inmuebles.trovit.es/index.php/cod.rss_search/type.1/what_d.chalet/where_d.Barcelona/price_max.320000"
        ]

        propiedades_encontradas = []

        for url in urls_rss:
            try:
                # Se añade el agent para evitar el bloqueo 403
                feed = feedparser.parse(url, agent=user_agent_browser)
                logging.info(f"Anuncios leídos del feed: {len(feed.entries)}")

                for entry in feed.entries:
                    titulo = entry.get("title", "")
                    link = entry.get("link", "")
                    descripcion = entry.get("summary", "").lower()
                    texto_completo = f"{titulo.lower()} {descripcion}"

                    prop_id = str(hash(link))

                    palabras_garaje = ["garaje", "parking", "pàrquing", "cochera", "aparcamiento"]
                    palabras_piscina = ["piscina", "pool", "comunitaria"]

                    tiene_garaje = any(p in texto_completo for p in palabras_garaje)
                    tiene_piscina = any(p in texto_completo for p in palabras_piscina)

                    propiedades_encontradas.append({
                        "id": prop_id,
                        "titulo": titulo,
                        "ubicacion": "Provincia de Barcelona",
                        "precio": self.config["precio_maximo"],
                        "garaje": tiene_garaje,
                        "piscina": tiene_piscina,
                        "url": link
                    })
            except Exception as e:
                logging.error(f"Error leyendo feed: {e}")

        nuevas_encontradas = 0
        for prop in propiedades_encontradas:
            if prop["id"] in self.vistas:
                continue

            self.vistas.add(prop["id"])

            if self.filtrar_propiedad(prop):
                self.enviar_alerta_telegram(prop)
                nuevas_encontradas += 1

        self.guardar_historial()
        logging.info(f"Búsqueda finalizada. Nuevas avisadas: {nuevas_encontradas}")

if __name__ == "__main__":
    agente = AgenteInmobiliario()
    agente.buscar_propiedades()
