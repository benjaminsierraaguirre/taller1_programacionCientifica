"""Etapa de exportación de resultados."""

import csv
from pathlib import Path

from models.resultado_analisis import ResultadoAnalisis
from pipeline.contexto import ContextoPipeline
from pipeline.etapa import EtapaPipeline


class ExportacionResultados(EtapaPipeline[ResultadoAnalisis, None]):
    """Exporta los resultados de los experimentos y su comparación."""

    def ejecutar(self, resultados: ResultadoAnalisis, contexto: ContextoPipeline) -> None:
        """Guarda los resultados en la ruta de salida configurada."""
        self._exportar(resultados, contexto.ruta_salida)

    def _exportar(self, resultados: ResultadoAnalisis, ruta_salida: Path) -> None:
        """Exporta los resultados a la ruta indicada."""
        ruta_salida.mkdir(parents=True, exist_ok=True)
        filas_individuales = [
            {"experimento": experimento.nombre, "id_peaton": id_peaton, **indicadores}
            for experimento in resultados.experimentos
            for id_peaton, indicadores in experimento.resultados_individuales.items()
        ]
        filas_zonas = [
            {"experimento": experimento.nombre, "zona": zona, **indicadores}
            for experimento in resultados.experimentos
            for zona, indicadores in experimento.resultados_zonas.items()
        ]
        filas_densidad = [
            {"experimento": experimento.nombre, **medicion}
            for experimento in resultados.experimentos
            for medicion in experimento.densidades
        ]
        filas_flujo = [
            {"experimento": experimento.nombre, **medicion}
            for experimento in resultados.experimentos
            for medicion in experimento.flujos
        ]
        filas_resumen = [
            {
                "experimento": nombre,
                **indicadores,
                "direccion": experimento.parametros.get("movement_direction", ""),
                "ancho_entrada_m": experimento.parametros.get("entrance width [m]", ""),
                "ancho_salida_m": experimento.parametros.get("exit width [m]", ""),
                "participantes_reportados": experimento.participantes_reportados,
            }
            for nombre, indicadores in resultados.comparacion.items()
            for experimento in resultados.experimentos
            if experimento.nombre == nombre
        ]
        self._guardar_csv(ruta_salida / "resultados_individuales.csv", filas_individuales)
        self._guardar_csv(ruta_salida / "resumen_experimentos.csv", filas_resumen)
        self._guardar_csv(ruta_salida / "resultados_zonas.csv", filas_zonas)
        self._guardar_csv(ruta_salida / "densidad.csv", filas_densidad)
        self._guardar_csv(ruta_salida / "flujo.csv", filas_flujo)
        print("Resultados guardados en:", ruta_salida)

    def _guardar_csv(self, ruta: Path, filas: list[dict[str, object]]) -> None:
        """Escribe filas de diccionarios en un archivo CSV."""
        if not filas:
            return
        nombres_columnas = list(dict.fromkeys([nombre for fila in filas for nombre in fila]))
        archivo = open(ruta, "w", newline="", encoding="utf-8")
        escritor = csv.DictWriter(archivo, fieldnames=nombres_columnas)
        escritor.writeheader()
        escritor.writerows(filas)
        archivo.close()
