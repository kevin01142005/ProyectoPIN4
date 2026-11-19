import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


def _entero(nombre: str, por_defecto: int) -> int:
    return int(os.getenv(nombre, str(por_defecto)))


@dataclass(frozen=True)
class Configuracion:
    nombre_aplicacion: str = "gestion-inventario-ventas"

    database_url: str = os.getenv("DATABASE_URL", "").strip()
    db_usuario: str = os.getenv("DB_USERNAME", "postgres")
    db_contrasena: str = os.getenv("DB_PASSWORD", "")
    db_host: str = os.getenv("DB_HOST", "localhost")
    db_puerto: int = _entero("DB_PORT", 5432)
    db_nombre: str = os.getenv("DB_NAME", "gestion_inventario_ventas")
    mostrar_sql: bool = os.getenv("MOSTRAR_SQL", "false").lower() == "true"

    jwt_secreto: str = os.getenv("JWT_SECRET", "change-this-secret-in-production-min-256-bits-long")
    jwt_minutos_expiracion: int = _entero("JWT_EXPIRATION_MINUTES", 30)

    semilla_correo: str = os.getenv("SEED_SUPERUSER_EMAIL", "superadmin@accesoriosmoto.com")
    semilla_contrasena: str = os.getenv("SEED_SUPERUSER_PASSWORD", "SuperAdmin123")

    zona_horaria: str = os.getenv("ZONA_HORARIA", "America/Bogota")

    catalogo_motos_url: str = os.getenv("CATALOGO_MOTOS_URL", "http://localhost:4000").strip().rstrip("/")
    catalogo_motos_timeout: float = float(os.getenv("CATALOGO_MOTOS_TIMEOUT_SEGUNDOS", "5"))

    # Circuito de sensores del almacén (ESP32)
    dispositivo_api_key: str = os.getenv("DISPOSITIVO_API_KEY", "").strip()
    temperatura_maxima: float = float(os.getenv("AMBIENTE_TEMP_MAX", "30"))
    temperatura_minima: float = float(os.getenv("AMBIENTE_TEMP_MIN", "15"))
    humedad_maxima: float = float(os.getenv("AMBIENTE_HUM_MAX", "70"))
    humedad_minima: float = float(os.getenv("AMBIENTE_HUM_MIN", "30"))

    # ThingSpeak (gráfica pública de las lecturas del circuito)
    thingspeak_write_key: str = os.getenv("THINGSPEAK_WRITE_KEY", "").strip()
    thingspeak_channel_id: str = os.getenv("THINGSPEAK_CHANNEL_ID", "").strip()

    # Correo saliente (notificaciones automáticas y envío de reportes). Por defecto usa SMTP de Gmail.
    correo_activo: bool = os.getenv("CORREO_ACTIVO", "true").lower() == "true"
    smtp_host: str = os.getenv("SMTP_HOST", "smtp.gmail.com").strip()
    smtp_puerto: int = _entero("SMTP_PORT", 587)
    smtp_usuario: str = os.getenv("SMTP_USER", "").strip()
    smtp_contrasena: str = os.getenv("SMTP_PASSWORD", "").replace(" ", "")
    smtp_timeout: float = float(os.getenv("SMTP_TIMEOUT_SEGUNDOS", "20"))
    correo_remitente: str = os.getenv("CORREO_REMITENTE", "").strip()
    nombre_remitente: str = os.getenv("CORREO_NOMBRE_REMITENTE", "LuxMotos").strip()
    # Si se define, las alertas van solo a estos correos; si no, a los administradores registrados.
    correos_alerta: tuple[str, ...] = tuple(
        c.strip().lower() for c in os.getenv("CORREOS_ALERTA", "").split(",") if c.strip()
    )
    # Mínimo de minutos entre dos alertas de ambiente seguidas (el circuito envía lecturas muy seguido).
    alerta_ambiente_minutos: int = _entero("ALERTA_AMBIENTE_MINUTOS", 30)

    puerto_servidor: int = _entero("SERVER_PORT", 8080)

    cors_origenes: tuple[str, ...] = tuple(
        o.strip().rstrip("/") for o in os.getenv("CORS_ORIGENES", "").split(",") if o.strip()
    )


configuracion = Configuracion()