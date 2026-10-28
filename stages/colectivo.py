"""Etapa de comparación de experimentos."""

from models.experimento import Experimento
from models.resultado_analisis import ResultadoAnalisis
from pipeline.contexto import ContextoPipeline
from pipeline.etapa import EtapaPipeline


class ComparacionExperimentos(EtapaPipeline[list[Experimento], ResultadoAnalisis]):
    """Compara resultados de varios experimentos."""

    def ejecutar(self, experimentos: list[Experimento], contexto: ContextoPipeline) -> ResultadoAnalisis:
        """Retorna los experimentos junto con sus resultados comparativos."""
        comparacion = self._comparar(experimentos)
        return ResultadoAnalisis(experimentos, comparacion)

    def _comparar(self, experimentos: list[Experimento]) -> dict[str, dict[str, float]]:
        """Resume indicadores individuales y colectivos por experimento."""
        return {experimento.nombre: self._resumir_experimento(experimento)
                for experimento in experimentos}

    def _resumir_experimento(self, experimento: Experimento) -> dict[str, float]:
        """Calcula promedios básicos del experimento."""
        personas = list(experimento.resultados_individuales.values())
        cantidad = len(personas)
        velocidades = [persona["velocidad_media_m_s"] for persona in personas]
        distancias = [persona["distancia_total_m"] for persona in personas]
        tiempos = [persona["tiempo_total_s"] for persona in personas]
        percentiles = [persona["velocidad_percentil_95_m_s"] for persona in personas]
        velocidad_media = sum(velocidades) / cantidad if cantidad > 0 else 0.0
        distancia_media = sum(distancias) / cantidad if cantidad > 0 else 0.0
        tiempo_medio = sum(tiempos) / cantidad if cantidad > 0 else 0.0
        percentil_95_medio = sum(percentiles) / cantidad if cantidad > 0 else 0.0
        diferencias = [(velocidad - velocidad_media) ** 2 for velocidad in velocidades]
        desviacion = (sum(diferencias) / cantidad) ** 0.5 if cantidad > 0 else 0.0
        return {
            "cantidad_peatones": cantidad,
            "velocidad_media_m_s": velocidad_media,
            "velocidad_percentil_95_media_m_s": percentil_95_medio,
            "desviacion_velocidad_m_s": desviacion,
            "densidad_media_personas_m2": experimento.resultados_colectivos.get("densidad_media_personas_m2", 0.0),
            "densidad_maxima_personas_m2": experimento.resultados_colectivos.get("densidad_maxima_personas_m2", 0.0),
            "flujo_medio_personas_s": experimento.resultados_colectivos.get("flujo_medio_personas_s", 0.0),
            "flujo_maximo_personas_s": experimento.resultados_colectivos.get("flujo_maximo_personas_s", 0.0),
            "distancia_media_m": distancia_media,
            "tiempo_medio_s": tiempo_medio,
        }

