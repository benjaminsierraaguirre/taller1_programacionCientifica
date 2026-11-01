"""Análisis de sensibilidad del criterio de detención (umbral y duración mínima)."""

import csv
from pathlib import Path

import stages.individual as ind
from pipeline.contexto import ContextoPipeline
from stages import CargaExperimentos, PreparacionTrayectorias

EXPERIMENTOS = ("01", "05", "08", "09")
UMBRALES = (0.1, 0.2, 0.3)       # m/s
DURACIONES = (0.5, 1.0, 2.0)     # s
RUTA_SALIDA = Path("results/sensibilidad.csv")
RUTA_INDIVIDUALES = Path("results/resultados_individuales.csv")


def calcular_filas(experimentos) -> list[dict]:
    """Recalcula las detenciones para cada combinación de parámetros."""
    analisis = ind.AnalisisIndividual()
    filas = []
    for exp in experimentos:
        if exp.nombre[-2:] not in EXPERIMENTOS:
            continue
        fps = exp.fps
        # los tramos y tiempos se calculan una sola vez por peatón
        tramos = [t.calcular_velocidades(fps) for t in exp.trayectorias]
        tiempos = [t.calcular_tiempo_total(fps) for t in exp.trayectorias]
        for umbral in UMBRALES:
            for minimo in DURACIONES:
                ind.VELOCIDAD_DETENCION_M_S = umbral
                ind.DURACION_MINIMA_DETENCION_S = minimo
                detenciones = [analisis._detectar_detenciones(tr, fps) for tr in tramos]
                porcentajes = [
                    100 * sum((f - i) / fps for i, f in d) / t if t > 0 else 0.0
                    for d, t in zip(detenciones, tiempos)
                ]
                filas.append({
                    "experimento": exp.nombre,
                    "umbral_m_s": umbral,
                    "duracion_minima_s": minimo,
                    "detenciones_total": sum(len(d) for d in detenciones),
                    "porcentaje_detenido_medio": round(sum(porcentajes) / len(porcentajes), 2),
                })
    return filas


def verificar(filas: list[dict]) -> None:
    """Compara la combinación 0,2 m/s y 1 s con los resultados del pipeline."""
    if not RUTA_INDIVIDUALES.exists():
        print("No hay results/resultados_individuales.csv: ejecuta antes python main.py")
        return
    totales = {}
    with open(RUTA_INDIVIDUALES, encoding="utf-8") as archivo:
        for fila in csv.DictReader(archivo):
            nombre = fila["experimento"]
            totales[nombre] = totales.get(nombre, 0) + float(fila["cantidad_detenciones"])
    print("\nVerificación (umbral 0.2 y 1.0 s contra results/resultados_individuales.csv):")
    for fila in filas:
        if fila["umbral_m_s"] == 0.2 and fila["duracion_minima_s"] == 1.0:
            esperado = totales.get(fila["experimento"])
            estado = "OK" if esperado == fila["detenciones_total"] else "NO COINCIDE"
            print(f"  {fila['experimento']}: script={fila['detenciones_total']} "
                  f"pipeline={esperado:.0f} -> {estado}")


def main() -> None:
    contexto = ContextoPipeline(Path("data"), Path("results"))
    experimentos = PreparacionTrayectorias().ejecutar(
        CargaExperimentos().ejecutar(None, contexto), contexto
    )
    filas = calcular_filas(experimentos)
    RUTA_SALIDA.parent.mkdir(exist_ok=True)
    with open(RUTA_SALIDA, "w", newline="", encoding="utf-8") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=list(filas[0]))
        escritor.writeheader()
        escritor.writerows(filas)
    print("Guardado en", RUTA_SALIDA)
    verificar(filas)


if __name__ == "__main__":
    main()