"""Entidad que agrupa los datos y resultados de un experimento."""

from dataclasses import dataclass, field

from .observacion import Observacion
from .trayectoria import Trayectoria


@dataclass
class Experimento:
    """Representa un conjunto de observaciones y sus análisis."""

    nombre: str
    observaciones: list[Observacion] = field(default_factory=list)
    trayectorias: list[Trayectoria] = field(default_factory=list)
    resultados_individuales: dict[int, dict[str, float]] = field(default_factory=dict)
    resultados_colectivos: dict[str, float] = field(default_factory=dict)
    fps: float | None = None
    participantes_reportados: int = 0
    parametros: dict[str, object] = field(default_factory=dict)
    resultados_zonas: dict[str, dict[str, float]] = field(default_factory=dict)
    densidades: list[dict[str, float]] = field(default_factory=list)
    flujos: list[dict[str, float]] = field(default_factory=list)
