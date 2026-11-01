"""Análisis propio RA5: detenciones sostenidas al variar el ancho nominal de salida.

Reutiliza results/resultados_individuales.csv y results/resumen_experimentos.csv.
No modifica los datos ni el pipeline. La salida nominal de las corridas 08 y 09
cambió durante la ejecución según el metadata, por lo que no hay inferencia causal.

Uso: python3 scripts/aporte_ra5.py
"""
import argparse
import csv
from collections import defaultdict
from pathlib import Path


def calcular(individuales, resumen):
    grupos = defaultdict(list)
    with individuales.open(encoding="utf-8", newline="") as archivo:
        for fila in csv.DictReader(archivo):
            grupos[fila["experimento"]].append(fila)

    resultados = []
    with resumen.open(encoding="utf-8", newline="") as archivo:
        for exp in sorted(csv.DictReader(archivo), key=lambda x: x["experimento"]):
            numero = exp["experimento"][-2:]
            if numero not in {"05", "06", "07", "08", "09"}:
                continue
            filas = grupos[exp["experimento"]]
            n = len(filas)
            if n == 0:
                raise ValueError(f"No se encontraron trayectorias para {numero}")
            con_detencion = sum(float(t["cantidad_detenciones"]) >= 1 for t in filas)
            resultados.append({
                "experimento": numero,
                "salida_nominal_m": float(exp["ancho_salida_m"]),
                "trayectorias_reconstruidas": n,
                "trayectorias_con_al_menos_una_detencion": con_detencion,
                "porcentaje_con_detencion": 100.0 * con_detencion / n,
                "velocidad_media_m_s": float(exp["velocidad_media_m_s"]),
                "flujo_medio_personas_s": float(exp["flujo_medio_personas_s"]),
            })
    return resultados


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--results", type=Path, default=Path("results"))
    p.add_argument("--figuras", type=Path, default=Path("figuras"))
    args = p.parse_args()
    filas = calcular(args.results / "resultados_individuales.csv",
                     args.results / "resumen_experimentos.csv")
    args.results.mkdir(parents=True, exist_ok=True)
    with (args.results / "aporte_ra5.csv").open("w", encoding="utf-8", newline="") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=list(filas[0]))
        escritor.writeheader()
        escritor.writerows(filas)

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.size": 9.5, "axes.spines.top": False,
                         "axes.spines.right": False, "axes.grid": True, "grid.alpha": .15})
    fig, ax = plt.subplots(figsize=(7.7, 3.7))
    labels = [f"{f['experimento']}\n{f['salida_nominal_m']:g} m" for f in filas]
    valores = [f["porcentaje_con_detencion"] for f in filas]
    barras = ax.bar(labels, valores,
                    color=["#126782" if f["experimento"] not in ("08", "09") else "#D0803A" for f in filas],
                    width=.62)
    for bar, val in zip(barras, valores):
        ax.annotate(f"{val:.1f}%", (bar.get_x() + bar.get_width()/2, val),
                    ha="center", va="bottom", xytext=(0, 5), textcoords="offset points", fontsize=9)
    ax.set_ylim(0, 92)
    ax.set_ylabel("Trayectorias con ≥ 1 detención (%)")
    ax.set_xlabel("Experimento y ancho de salida nominal")
    ax.set_title("Incidencia de al menos una detención de ≥ 1 s (v ≤ 0,2 m/s)")
    ax.text(0.5, -0.29, "En las corridas 08 y 09 cambió la salida durante la medición (metadatos).",
            transform=ax.transAxes, ha="center", fontsize=8, color="#665C51")
    fig.tight_layout()
    args.figuras.mkdir(parents=True, exist_ok=True)
    nombre = args.figuras / "figura_09_detenciones_por_salida.png"
    fig.savefig(nombre, bbox_inches="tight", facecolor="white", dpi=170)
    plt.close(fig)
    print("Resultados guardados en", args.results / "aporte_ra5.csv", "y", nombre)
    for f in filas:
        print(f"{f['experimento']}: {f['trayectorias_con_al_menos_una_detencion']}/{f['trayectorias_reconstruidas']} ({f['porcentaje_con_detencion']:.1f}%)")

if __name__ == "__main__":
    main()
