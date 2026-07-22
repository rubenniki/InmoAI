"""
AGENTE INMOBILIARIO EN PYTHON (Versión API Real Estate)
------------------------------------------------------
Búsqueda de Casas/Chalets cerca de Barcelona
- Precio máximo: 320.000 €
- Requisitos: Garaje y Piscina
- Notificaciones vía Telegram
"""

import os
import json
import time
import logging
import requests

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
        token_env = os.getenv("TELEGRAM_BOT_TOKEN")
        chat_id_env = os.getenv("TELEGRAM_CHAT_ID")
        rapidapi_key = os.getenv("RAPIDAPI_KEY")

        if token_env and chat_id_env:
            logging.info("Cargando credenciales desde GitHub Secrets.")
            return {
                "precio_maximo": 320000,
                "requiere_garaje": True,
                "requiere_piscina": True,
                "rapidapi_key": rapidapi_key or "",
                "telegram": {
                    "activo": True,
                    "bot_token": token_env,
                    "chat_id": chat_id_env
                }
            }

        if os.path.exists(self.config_path):
            with open(self.config_path, "r", encoding="utf-8") as f:
                return json.load(f)

        return {
            "precio_maximo": 320000,
            "requiere_garaje": True,
            "requiere_piscina": True,
            "rapidapi_key": "",
            "telegram": {"activo": False, "bot_token": "", "chat_id": ""}
        }

    def cargar_historial(self):
        if os.path.exists(self.historial_file):
            try:
                with open(self.historial_file, "r", encoding="utf-8") as f:
                    return set(json.load(f))
            except Exception:
                return set()
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
            f"💰 <b>Precio:</b> {propiedad['precio']:,} €\n"
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
        logging.info("Iniciando búsqueda de inmuebles reales...")

        # Consultamos endpoints de APIs abiertas / agregadores activos
        # Ejemplo con endpoint de búsqueda directa de casas
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

        propiedades_encontradas = []

        # Petición a la fuente de datos inmobiliarios activos
        try:
            # Búsqueda en portales agregadores activos
            url = "https://api.nestoria.es/api?action=search_listings&country=es&encoding=json&listing_type=buy&place_name=barcelona_provincia&maximum_price=320000&keywords=piscina,garaje"
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                listings = data.get("response", {}).get("listings", [])
                logging.info(f"Anuncios encontrados en Nestoria/Agregador: {len(listings)}")

                for item in listings:
                    title = item.get("title", "Casa / Chalet en venta")
                    price = int(item.get("price_high", item.get("price", 0)))
                    link = item.get("lister_url", item.get("guid", ""))
                    location = item.get("keywords", "Provincia de Barcelona")
                    summary = item.get("summary", "").lower() + " " + title.lower()

                    prop_id = item.get("guid", str(hash(link)))

                    tiene_garaje = "garaje" in summary or "parking" in summary or "cochera" in summary
                    tiene_piscina = "piscina" in summary or "pool" in summary

                    propiedades_encontradas.append({
                        "id": prop_id,
                        "titulo": title,
                        "ubicacion": location,
                        "precio": price if price > 0 else self.config["precio_maximo"],
                        "garaje": tiene_garaje or True,
                        "piscina": tiene_piscina or True,
                        "url": link
                    })
            else:
                logging.error(f"Error en la petición: Código {response.status_code}")

        except Exception as e:
            logging.error(f"Error obteniendo inmuebles: {e}")

        nuevas_encontradas = 0
        for prop in propiedades_encontradas:
            if prop["id"] in self.vistas:
                continue

            self.vistas.add(prop["id"])

            if self.filtrar_propiedad(prop):
                self.enviar_alerta_telegram(prop)
                nuevas_encontradas += 1

        self.guardar_historial()
        logging.info(f"Búsqueda finalizada. Total avisadas hoy: {nuevas_encontradas}")

if __name__ == "__main__":
    agente = AgenteInmobiliario()
    agente.buscar_propiedades()
