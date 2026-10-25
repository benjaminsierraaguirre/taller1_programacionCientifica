"""Etapa de carga de varios experimentos."""

import json
from pathlib import Path

from models.experimento import Experimento
from models.observacion import Observacion
from pipeline.contexto import ContextoPipeline
from pipeline.etapa import EtapaPipeline


class CargaExperimentos(EtapaPipeline[None, list[Experimento]]):
    """Carga una colección de experimentos desde la ruta configurada."""

    def ejecutar(self, entrada: None, contexto: ContextoPipeline) -> list[Experimento]:
        """Carga los experimentos indicados por la configuración."""
        experimentos = self._cargar_experimentos(contexto.ruta_entrada)
        for experimento in experimentos:
            if (experimento.fps is None or experimento.fps <= 0) and contexto.fps is not None:
                experimento.fps = contexto.fps
        for experimento in experimentos:
            if experimento.fps is None or experimento.fps <= 0:
                raise ValueError("El archivo " + experimento.nombre + " no tiene un FPS válido. Usa --fps para indicarlo.")
        print("Experimentos cargados:", len(experimentos))
        return experimentos

    def _cargar_experimentos(self, ruta_entrada: Path) -> list[Experimento]:
        """Carga los experimentos disponibles en la ruta recibida."""
        ruta_json = ruta_entrada / "2013unidirectional_metadata.json"
        if not ruta_json.exists():
            ruta_json = ruta_entrada / "Metadata.json"
        datos_json = {}
        if ruta_json.exists():
            archivo_json = open(ruta_json, "r", encoding="utf-8")
            datos_json = json.load(archivo_json)
            archivo_json.close()

        corridas = datos_json.get("experiment", {}).get("run", [])
        datos_por_nombre = {dato["run_name"]: dato for dato in corridas}
        archivos_txt = sorted(ruta_entrada.glob("*.txt"), key=lambda archivo: archivo.name)
        experimentos = []
        for ruta_txt in archivos_txt:
            observaciones = []
            fps = 0.0
            archivo = open(ruta_txt, "r", encoding="utf-8")
            linea = archivo.readline().strip()
            while linea != "":
                if linea.startswith("#"):
                    partes = linea.split()
                    if len(partes) >= 3 and partes[1] == "framerate:":
                        fps = float(partes[2])
                else:
                    partes = linea.split()
                    if len(partes) == 5:
                        try:
                            observacion = Observacion(int(partes[0]), int(partes[1]), float(partes[2]), float(partes[3]), float(partes[4]))
                            observaciones.append(observacion)
                        except ValueError:
                            print("Fila no numérica ignorada:", linea)
                    else:
                        print("Fila incompleta ignorada:", linea)
                linea = archivo.readline().strip()
            archivo.close()

            nombre = ruta_txt.stem
            dato = datos_por_nombre.get(nombre, {})
            experimento = Experimento(
                nombre=nombre,
                observaciones=observaciones,
                fps=fps,
                participantes_reportados=dato.get("number_participants", 0),
                parametros=dato.get("parameter", {}),
            )
            experimentos.append(experimento)
            print(nombre, ":", len(observaciones), "observaciones")
        return experimentos



