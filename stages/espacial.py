"""Etapa de análisis espacial, densidad y flujo."""

from models.experimento import Experimento
from models.trayectoria import Trayectoria
from pipeline.contexto import ContextoPipeline
from pipeline.etapa import EtapaPipeline


LONGITUD_CORREDOR_DEFAULT_M = 18.0
ANCHO_CORREDOR_DEFAULT_M = 5.0
CENTRO_CORREDOR_X_M = 0.0
INICIO_CORREDOR_Y_M = 0.0
CANTIDAD_ZONAS = 3
LINEA_FLUJO_X_M = 0.0


class AnalisisEspacial(EtapaPipeline[list[Experimento], list[Experimento]]):
    """Agrupa el análisis por zonas y los cálculos de densidad y flujo."""

    def ejecutar(self, experimentos: list[Experimento], contexto: ContextoPipeline) -> list[Experimento]:
        """Analiza las zonas, la densidad y el flujo de cada experimento."""
        for experimento in experimentos:
            experimento.resultados_zonas = self._analizar_zonas(experimento)
            experimento.resultados_colectivos.update(self._calcular_densidad(experimento))
        return experimentos

    def _obtener_geometria(self, experimento: Experimento) -> tuple[float, float, float, float, float, float]:
        """Obtiene dimensiones del JSON y calcula los límites de la región."""
        largo = float(experimento.parametros.get("corridor length [m]", LONGITUD_CORREDOR_DEFAULT_M))
        ancho = float(experimento.parametros.get("corridor width [m]", ANCHO_CORREDOR_DEFAULT_M))
        x_min = CENTRO_CORREDOR_X_M - largo / 2
        x_max = CENTRO_CORREDOR_X_M + largo / 2
        y_min = INICIO_CORREDOR_Y_M
        y_max = y_min + ancho
        return x_min, x_max, y_min, y_max, largo, ancho

    def _analizar_zonas(self, experimento: Experimento) -> dict[str, dict[str, float]]:
        """Calcula peatones, velocidad media y tiempo en cada zona."""
        x_min, x_max, y_min, y_max, largo, ancho = self._obtener_geometria(experimento)
        ancho_zona = largo / CANTIDAD_ZONAS
        area_zona = (largo * ancho) / CANTIDAD_ZONAS
        personas_por_zona = [{} for numero in range(CANTIDAD_ZONAS)]
        for trayectoria in experimento.trayectorias:
            for observacion in trayectoria.observaciones:
                dentro = x_min <= observacion.x <= x_max and y_min <= observacion.y <= y_max
                if dentro:
                    zona = int((observacion.x - x_min) / ancho_zona)
                    if zona >= CANTIDAD_ZONAS:
                        zona = CANTIDAD_ZONAS - 1
                    personas_por_zona[zona].setdefault(trayectoria.id_peaton, []).append(observacion)

        resultados = {}
        fps = experimento.fps or 0.0
        for numero_zona in range(CANTIDAD_ZONAS):
            personas = [
                (id_peaton, sorted(datos, key=lambda dato: dato.frame))
                for id_peaton, datos in personas_por_zona[numero_zona].items()
            ]
            personas_con_medicion = [(id_peaton, datos) for id_peaton, datos in personas if len(datos) > 1]
            tiempos = [
                (datos[-1].frame - datos[0].frame) / fps if fps > 0 else 0.0
                for id_peaton, datos in personas_con_medicion
            ]
            distancias = [
                sum([
                    Trayectoria.calcular_distancia_entre(actual, siguiente)
                    for actual, siguiente in zip(datos, datos[1:])
                ])
                for id_peaton, datos in personas_con_medicion
            ]
            velocidades = [distancia / tiempo for distancia, tiempo in zip(distancias, tiempos) if tiempo > 0]
            cantidad_total = len(personas)
            cantidad_con_medicion = len(personas_con_medicion)
            cantidad_que_rozan = sum([1 for id_peaton, datos in personas if len(datos) == 1])
            resultados["zona_" + str(numero_zona + 1)] = {
                "peatones": cantidad_total,
                "peatones_con_al_menos_2_observaciones": cantidad_con_medicion,
                "peatones_que_solo_rozan": cantidad_que_rozan,
                "velocidad_media_m_s": sum(velocidades) / len(velocidades) if velocidades else 0.0,
                "tiempo_medio_s": sum(tiempos) / len(tiempos) if tiempos else 0.0,
                "area_m2": area_zona,
            }
        return resultados

    def _calcular_densidad(self, experimento: Experimento) -> dict[str, float]:
        """Calcula densidad y velocidad media por cada frame observado con peatones."""
        x_min, x_max, y_min, y_max, largo, ancho = self._obtener_geometria(experimento)
        area = largo * ancho
        personas_por_frame = {}
        velocidades_por_frame = {}
        fps = experimento.fps or 0.0
        for trayectoria in experimento.trayectorias:
            observaciones = sorted(trayectoria.observaciones, key=lambda dato: dato.frame)
            for observacion in observaciones:
                dentro = x_min <= observacion.x <= x_max and y_min <= observacion.y <= y_max
                if dentro:
                    personas_por_frame.setdefault(observacion.frame, set()).add(observacion.id_peaton)
            pares_dentro = [
                (actual, siguiente)
                for actual, siguiente in zip(observaciones, observaciones[1:])
                if fps > 0 and siguiente.frame > actual.frame
                and x_min <= actual.x <= x_max and x_min <= siguiente.x <= x_max
                and y_min <= actual.y <= y_max and y_min <= siguiente.y <= y_max
            ]
            for actual, siguiente in pares_dentro:
                tiempo = (siguiente.frame - actual.frame) / fps
                velocidad = Trayectoria.calcular_distancia_entre(actual, siguiente) / tiempo
                velocidades_por_frame.setdefault(actual.frame, []).append(velocidad)

        frames = sorted(personas_por_frame, key=lambda frame: frame)
        primer_frame = frames[0] if frames else 0
        experimento.densidades = [
            {
                "frame": frame,
                "tiempo_s": (frame - primer_frame) / fps if fps > 0 else 0.0,
                "peatones": len(personas_por_frame[frame]),
                "densidad_personas_m2": len(personas_por_frame[frame]) / area,
                "velocidad_media_m_s": (
                    sum(velocidades_por_frame[frame]) / len(velocidades_por_frame[frame])
                    if velocidades_por_frame.get(frame) else 0.0
                ),
            }
            for frame in frames
        ]
        valores = [fila["densidad_personas_m2"] for fila in experimento.densidades]
        return {
            "densidad_media_personas_m2": sum(valores) / len(valores) if valores else 0.0,
            "densidad_maxima_personas_m2": max(valores, default=0.0),
        }

    def _calcular_flujo(self, experimento: Experimento, fps: float | None) -> dict[str, float]:
        """Cuenta cruces de la línea central en intervalos de un segundo."""
        return {}
