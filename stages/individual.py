"""Etapa de análisis individual de los experimentos."""

from models.experimento import Experimento
from models.trayectoria import Trayectoria
from pipeline.contexto import ContextoPipeline
from pipeline.etapa import EtapaPipeline


VELOCIDAD_DETENCION_M_S = 0.2
DURACION_MINIMA_DETENCION_S = 1.0


class AnalisisIndividual(EtapaPipeline[list[Experimento], list[Experimento]]):
    """Coordina el análisis de múltiples trayectorias y reúne sus indicadores."""

    def ejecutar(self, experimentos: list[Experimento], contexto: ContextoPipeline) -> list[Experimento]:
        """Analiza las trayectorias de cada experimento."""
        for experimento in experimentos:
            fps = experimento.fps
            if contexto.fps is not None and (fps is None or fps <= 0):
                fps = contexto.fps
            if fps is None or fps <= 0:
                raise ValueError("El FPS debe ser mayor que cero para calcular velocidades.")
            for trayectoria in experimento.trayectorias:
                if len(trayectoria.observaciones) > 1:
                    resultado = self._calcular_indicadores(trayectoria, fps)
                    experimento.resultados_individuales[trayectoria.id_peaton] = resultado
        return experimentos

    def _calcular_indicadores(self, trayectoria: Trayectoria, fps: float) -> dict[str, float]:
        """Calcula los indicadores individuales de una trayectoria."""
        observaciones = sorted(trayectoria.observaciones, key=lambda dato: dato.frame)
        inicio = observaciones[0]
        final = observaciones[-1]
        distancia_total = trayectoria.calcular_distancia_total()
        desplazamiento = trayectoria.calcular_desplazamiento()
        tiempo_total = trayectoria.calcular_tiempo_total(fps)
        tramos = trayectoria.calcular_velocidades(fps)
        velocidades = [velocidad for actual, siguiente, velocidad in tramos]
        eficiencia = desplazamiento / distancia_total if distancia_total > 0 else 0.0
        detenciones = self._detectar_detenciones(tramos, fps)
        tiempo_detenido = sum([(fin - inicio) / fps for inicio, fin in detenciones])
        porcentaje_detenido = tiempo_detenido / tiempo_total * 100 if tiempo_total > 0 else 0.0
        velocidades_ordenadas = sorted(velocidades)
        indice_percentil = int((len(velocidades_ordenadas) - 1) * 0.95) if velocidades_ordenadas else 0
        velocidad_percentil_95 = velocidades_ordenadas[indice_percentil] if velocidades_ordenadas else 0.0
        return {
            "posicion_inicial_x_m": inicio.x,
            "posicion_inicial_y_m": inicio.y,
            "posicion_final_x_m": final.x,
            "posicion_final_y_m": final.y,
            "tiempo_total_s": tiempo_total,
            "distancia_total_m": distancia_total,
            "desplazamiento_m": desplazamiento,
            "velocidad_media_m_s": trayectoria.calcular_velocidad_media(fps),
            "velocidad_maxima_m_s": max(velocidades, default=0.0),
            "velocidad_percentil_95_m_s": velocidad_percentil_95,
            "eficiencia": eficiencia,
            "cantidad_detenciones": float(len(detenciones)),
            "tiempo_detenido_s": tiempo_detenido,
            "porcentaje_detenido": porcentaje_detenido,
        }

    def _detectar_detenciones(self, tramos: list[tuple], fps: float) -> list[tuple[int, int]]:
        """Identifica intervalos de detención de una trayectoria."""
        detenciones = []
        frame_inicio = None
        frame_final = None
        estaba_detenido = False
        for actual, siguiente, velocidad in tramos:
            if velocidad <= VELOCIDAD_DETENCION_M_S:
                if not estaba_detenido:
                    frame_inicio = actual.frame
                frame_final = siguiente.frame
                estaba_detenido = True
            elif estaba_detenido:
                duracion = (frame_final - frame_inicio) / fps
                if duracion >= DURACION_MINIMA_DETENCION_S:
                    detenciones.append((frame_inicio, frame_final))
                estaba_detenido = False
        if estaba_detenido:
            duracion = (frame_final - frame_inicio) / fps
            if duracion >= DURACION_MINIMA_DETENCION_S:
                detenciones.append((frame_inicio, frame_final))
        return detenciones



