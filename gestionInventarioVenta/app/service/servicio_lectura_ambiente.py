from datetime import datetime, timedelta, timezone
from typing import Optional

from app.config.configuracion import configuracion
from app.dto.ambiente.lectura_ambiente_request import LecturaAmbienteRequest
from app.dto.ambiente.lectura_ambiente_response import LecturaAmbienteResponse, ResumenAmbienteResponse
from app.model.lectura_ambiente import LecturaAmbiente
from app.model.tipo_notificacion import TipoNotificacion
from app.repository.lectura_ambiente_repository import LecturaAmbienteRepository
from app.service.servicio_notificacion import notificar_en_segundo_plano
from app.service.servicio_thingspeak import publicar_lectura
from app.util.anio_mes import zona
from app.util.plantillas_correo import construir_html


class ServicioLecturaAmbiente:
    def __init__(self, lectura_repository: LecturaAmbienteRepository):
        self.lectura_repository = lectura_repository

    def registrar(self, request: LecturaAmbienteRequest) -> LecturaAmbienteResponse:
        lectura = LecturaAmbiente(
            dispositivo=request.dispositivo.strip(),
            temperatura=request.temperatura,
            humedad=request.humedad,
            presion=request.presion,
        )
        # Si el circuito no envía hora (el ESP32 no tiene reloj propio), se usa la del servidor.
        if request.medido is not None:
            lectura.medido = request.medido if request.medido.tzinfo else request.medido.replace(tzinfo=timezone.utc)
        else:
            lectura.medido = datetime.now(timezone.utc)

        respuesta = self._a_response(self.lectura_repository.save(lectura))

        # Gráfica en tiempo real: reenvía la temperatura a ThingSpeak (en segundo plano, sin afectar al circuito).
        publicar_lectura(respuesta.temperatura, respuesta.presion)

        # Notificación automática: la lectura salió de los límites de la bodega (con pausa entre alertas).
        if respuesta.alerta:
            humedad = f"{respuesta.humedad:.1f} %" if respuesta.humedad is not None else "sin dato"
            notificar_en_segundo_plano(
                TipoNotificacion.ALERTA_AMBIENTE,
                f"Alerta del almacén: {respuesta.alerta}",
                construir_html(
                    "Alerta de condiciones del almacén",
                    [
                        f"Motivo: {respuesta.alerta}.",
                        f"Dispositivo: {respuesta.dispositivo}",
                        f"Temperatura: {respuesta.temperatura:.1f} °C · Humedad: {humedad}",
                        f"Medido el {respuesta.medido.astimezone(zona()):%d/%m/%Y a las %H:%M}.",
                    ],
                ),
                referencia=respuesta.dispositivo,
                minutos_entre_alertas=configuracion.alerta_ambiente_minutos,
            )
        return respuesta

    def listar(self, horas: int, limite: int) -> list[LecturaAmbienteResponse]:
        desde = datetime.now(timezone.utc) - timedelta(hours=horas)
        return [self._a_response(l) for l in self.lectura_repository.find_desde(desde, limite)]

    def ultima(self) -> Optional[LecturaAmbienteResponse]:
        lectura = self.lectura_repository.find_ultima()
        return self._a_response(lectura) if lectura else None

    def resumen(self, horas: int) -> ResumenAmbienteResponse:
        lecturas = self.listar(horas, 5000)
        if not lecturas:
            return ResumenAmbienteResponse(
                total=0, temperatura_min=None, temperatura_max=None, temperatura_promedio=None,
                humedad_min=None, humedad_max=None, humedad_promedio=None,
                lecturas_con_alerta=0, ultima=None,
            )
        temps = [l.temperatura for l in lecturas]
        hums = [l.humedad for l in lecturas if l.humedad is not None]
        return ResumenAmbienteResponse(
            total=len(lecturas),
            temperatura_min=min(temps), temperatura_max=max(temps),
            temperatura_promedio=round(sum(temps) / len(temps), 2),
            humedad_min=min(hums) if hums else None, humedad_max=max(hums) if hums else None,
            humedad_promedio=round(sum(hums) / len(hums), 2) if hums else None,
            lecturas_con_alerta=sum(1 for l in lecturas if l.alerta),
            ultima=lecturas[-1],
        )

    @staticmethod
    def _alerta(temperatura: float, humedad: Optional[float]) -> Optional[str]:
        """Compara con los límites definidos para la bodega (se configuran en el .env)."""
        motivos = []
        if temperatura > configuracion.temperatura_maxima:
            motivos.append(f"Temperatura alta ({temperatura:.1f} °C)")
        elif temperatura < configuracion.temperatura_minima:
            motivos.append(f"Temperatura baja ({temperatura:.1f} °C)")
        if humedad is None:
            pass
        elif humedad > configuracion.humedad_maxima:
            motivos.append(f"Humedad alta ({humedad:.1f} %)")
        elif humedad < configuracion.humedad_minima:
            motivos.append(f"Humedad baja ({humedad:.1f} %)")
        return "; ".join(motivos) or None

    @classmethod
    def _a_response(cls, l: LecturaAmbiente) -> LecturaAmbienteResponse:
        temp = float(l.temperatura)
        hum = float(l.humedad) if l.humedad is not None else None
        return LecturaAmbienteResponse(
            id=l.id, dispositivo=l.dispositivo, temperatura=temp, humedad=hum,
            presion=float(l.presion) if l.presion is not None else None,
            medido=l.medido, alerta=cls._alerta(temp, hum),
        )