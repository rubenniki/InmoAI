"""
AGENTE INMOBILIARIO EN PYTHON
-----------------------------
Búsqueda de Casas/Chalets cerca de Barcelona
- Precio máximo: 320.000 €
- Requisitos imprescindibles: Garaje y Piscina
- Notificaciones automáticas vía Telegram
"""


import os
import json
import time
import logging
import requests
from bs4 import BeautifulSoup


# Configuración de Logging
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
        """Carga la configuración o establece valores por defecto."""
        config_defecto = {
            "precio_maximo": 320000,
            "ubicacion_objetivo": "Barcelona y alrededores (Baix Llobregat, Vallès, Maresme, Garraf)",
            "requiere_garaje": True,
            "requiere_piscina": True,
            "telegram": {
                "activo": False,
                "bot_token": "TU_TELEGRAM_BOT_TOKEN",
                "chat_id": "TU_TELEGRAM_CHAT_ID"
            },
            "intervalo_chequeo_minutos": 30
        }
        if os.path.exists(self.config_path):
            with open(self.config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        else:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(config_defecto, f, indent=4, ensure_ascii=False)
            logging.info(f"Archivo de configuración creado en '{self.config_path}'.")
            return config_defecto


    def cargar_historial(self):
        """Carga el historial de inmuebles ya procesados para no repetir alertas."""
        if os.path.exists(self.historial_file):
            with open(self.historial_file, "r", encoding="utf-8") as f:
                return set(json.load(f))
        return set()


    def guardar_historial(self):
        """Guarda los IDs de los inmuebles vistos."""
        with open(self.historial_file, "w", encoding="utf-8") as f:
            json.dump(list(self.vistas), f, indent=4, ensure_ascii=False)


    def filtrar_propiedad(self, propiedad):
        """Aplica filtros estrictos sobre la propiedad."""
        # 1. Filtro de Precio
        if propiedad.get("precio", float("inf")) > self.config["precio_maximo"]:
            logging.debug(f"Descartada por precio: {propiedad.get('precio')} €")
            return False


        # 2. Filtro de Garaje
        if self.config["requiere_garaje"] and not propiedad.get("garaje", False):
            logging.debug(f"Descartada por falta de garaje: {propiedad.get('titulo')}")
            return False


        # 3. Filtro de Piscina
        if self.config["requiere_piscina"] and not propiedad.get("piscina", False):
            logging.debug(f"Descartada por falta de piscina: {propiedad.get('titulo')}")
            return False


        return True


    def enviar_alerta_telegram(self, propiedad):
        """Envía una notificación al canal o chat de Telegram configurado."""
        telegram_cfg = self.config.get("telegram", {})
        if not telegram_cfg.get("activo", False):
            logging.info("[ALERTA LOCAL] Nueva propiedad encontrada (Telegram no configurado):")
            logging.info(f" -> {propiedad['titulo']} ({propiedad['precio']:,} €) en {propiedad['ubicacion']}")
            logging.info(f"    Link: {propiedad['url']}")
            return


        token = telegram_cfg.get("bot_token")
        chat_id = telegram_cfg.get("chat_id")
        
        mensaje = (
            f"🏡 <b>¡NUEVA OPORTUNIDAD ENCONTRADA!</b>


"
            f"📌 <b>{propiedad['titulo']}</b>
"
            f"📍 <b>Ubicación:</b> {propiedad['ubicacion']}
"
            f"💰 <b>Precio:</b> {propiedad['precio']:,} €
"
            f"🚗 <b>Garaje:</b> {'Sí' if propiedad['garaje'] else 'No'}
"
            f"🏊 <b>Piscina:</b> {'Sí' if propiedad['piscina'] else 'No'}


"
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
            res = requests.post(url_api, json=payload, timeout=10)
            if res.status_code == 200:
                logging.info(f"Notificación Telegram enviada exitosamente para ID: {propiedad['id']}")
            else:
                logging.error(f"Error enviando mensaje a Telegram: {res.text}")
        except Exception as e:
            logging.error(f"Excepción al conectar con Telegram: {e}")


    def buscar_propiedades(self):
        """
        Simulación/Integración de extracción de datos.
        Aquí se conectaría con APIs o scrapers de portales inmobiliarios.
        """
        logging.info("Iniciando búsqueda de viviendas...")
        
        # Ejemplo de estructura de datos recibida desde la API/Scraper
        propiedades_encontradas = [
            {
                "id": "house_001",
                "titulo": "Chalet independiente con jardín y piscina privada",
                "ubicacion": "Corbera de Llobregat",
                "precio": 298000,
                "garaje": True,
                "piscina": True,
                "url": "https://www.ejemplo-inmobiliaria.com/inmueble/house_001"
            },
            {
                "id": "house_002",
                "titulo": "Casa adosada reformada con garaje y zona comunitaria",
                "ubicacion": "Castellbisbal",
                "precio": 315000,
                "garaje": True,
                "piscina": True,
                "url": "https://www.ejemplo-inmobiliaria.com/inmueble/house_002"
            },
            {
                "id": "house_003",
                "titulo": "Casa de pueblo sin plaza de garaje",
                "ubicacion": "Terrassa",
                "precio": 270000,
                "garaje": False,
                "piscina": True,
                "url": "https://www.ejemplo-inmobiliaria.com/inmueble/house_003"
            },
            {
                "id": "house_004",
                "titulo": "Torre a 4 vientos con piscina y garaje doble",
                "ubicacion": "Vallirana",
                "precio": 319000,
                "garaje": True,
                "piscina": True,
                "url": "https://www.ejemplo-inmobiliaria.com/inmueble/house_004"
            }
        ]


        nuevas_encontradas = 0


        for prop in propiedades_encontradas:
            prop_id = prop["id"]


            # Si ya la vimos anteriormente, la saltamos
            if prop_id in self.vistas:
                continue


            # Registramos que ya se procesó
            self.vistas.add(prop_id)


            # Evaluamos los criterios estrictos
            if self.filtrar_propiedad(prop):
                self.enviar_alerta_telegram(prop)
                nuevas_encontradas += 1


        self.guardar_historial()
        logging.info(f"Búsqueda finalizada. Nuevas oportunidades notificadas: {nuevas_encontradas}")


    def ejecutar_bucle(self):
        """Mantiene el agente ejecutándose en segundo plano de forma continua."""
        intervalo = self.config.get("intervalo_chequeo_minutos", 30) * 60
        logging.info(f"Agente en marcha. Ejecutando comprobación cada {self.config.get('intervalo_chequeo_minutos')} minutos.")
        try:
            while True:
                self.buscar_propiedades()
                logging.info(f"Esperando {self.config.get('intervalo_chequeo_minutos')} minutos hasta el próximo escaneo...")
                time.sleep(intervalo)
        except KeyboardInterrupt:
            logging.info("Agente detenido manualmente por el usuario.")


if __name__ == "__main__":
    agente = AgenteInmobiliario()
    # Para ejecutar una sola búsqueda:
    agente.buscar_propiedades()
    
    # Si deseas dejarlo corriendo 24/7 en un servidor, descomenta la siguiente línea:
    # agente.ejecutar_bucle()