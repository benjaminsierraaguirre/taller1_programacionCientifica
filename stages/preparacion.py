"""Etapa de preparación de observaciones y trayectorias."""

from models.experimento import Experimento
from models.observacion import Observacion
from models.trayectoria import Trayectoria
from pipeline.contexto import ContextoPipeline
from pipeline.etapa import EtapaPipeline


class PreparacionTrayectorias(EtapaPipeline[list[Experimento], list[Experimento]]):
    """Agrupa validación, organización y reconstrucción de trayectorias."""

    def ejecutar(self, experimentos: list[Experimento], contexto: ContextoPipeline) -> list[Experimento]:
        """Prepara las observaciones y trayectorias de cada experimento."""
        for experimento in experimentos:
            observaciones_validas = self._validar_observaciones(experimento.observaciones)
            organizadas = self._organizar_observaciones(observaciones_validas)
            experimento.observaciones = observaciones_validas
            experimento.trayectorias = self._reconstruir_trayectorias(organizadas)
            print(experimento.nombre, ":", len(experimento.trayectorias), "trayectorias")
        return experimentos

    def _validar_observaciones(self, observaciones: list[Observacion]) -> list[Observacion]:
        """Valida y retorna las observaciones de un experimento."""
        validas = []
        claves_vistas = set()
        descartadas = 0
        for observacion in observaciones:
            coordenadas = [observacion.x, observacion.y, observacion.z]
            finitas = all([valor == valor and valor != float("inf") and valor != -float("inf") for valor in coordenadas])
            clave = (observacion.id_peaton, observacion.frame)
            if observacion.id_peaton <= 0 or observacion.frame < 0 or not finitas or clave in claves_vistas:
                descartadas += 1
            else:
                validas.append(observacion)
                claves_vistas.add(clave)
        if descartadas > 0:
            print("Observaciones inválidas o repetidas:", descartadas)
        return validas

    def _organizar_observaciones(self, observaciones: list[Observacion]) -> dict[int, list[Observacion]]:
        """Organiza las observaciones por identificador de peatón."""
        organizadas = {}
        for observacion in observaciones:
            id_peaton = observacion.id_peaton
            if id_peaton not in organizadas:
                organizadas[id_peaton] = []
            organizadas[id_peaton].append(observacion)
        for id_peaton in organizadas:
            organizadas[id_peaton].sort(key=lambda dato: dato.frame)
        return organizadas

    def _reconstruir_trayectorias(self, organizadas: dict[int, list[Observacion]]) -> list[Trayectoria]:
        """Construye trayectorias desde las observaciones organizadas."""
        cantidad_incompleta = sum([1 for datos in organizadas.values() if len(datos) <= 1])
        if cantidad_incompleta > 0:
            print("Trayectorias de una observación ignoradas:", cantidad_incompleta)
        return [
            Trayectoria(id_peaton, datos)
            for id_peaton, datos in organizadas.items()
            if len(datos) > 1
        ]


