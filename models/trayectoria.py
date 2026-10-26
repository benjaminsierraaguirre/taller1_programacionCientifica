"""Modelo básico de una trayectoria peatonal."""

from dataclasses import dataclass, field

from .observacion import Observacion


@dataclass
class Trayectoria:
    """Representa las observaciones y cálculos propios de un peatón."""

    id_peaton: int
    observaciones: list[Observacion] = field(default_factory=list)

    @staticmethod
    def calcular_distancia_entre(actual: Observacion, siguiente: Observacion) -> float:
        """Calcula la distancia entre dos observaciones consecutivas."""
        diferencia_x = siguiente.x - actual.x
        diferencia_y = siguiente.y - actual.y
        return (diferencia_x ** 2 + diferencia_y ** 2) ** 0.5

    def calcular_distancia_total(self) -> float:
        """Calcula la distancia total recorrida por el peatón."""
        observaciones = sorted(self.observaciones, key=lambda dato: dato.frame)
        distancias = [
            Trayectoria.calcular_distancia_entre(actual, siguiente)
            for actual, siguiente in zip(observaciones, observaciones[1:])
        ]
        return sum(distancias)

    def calcular_desplazamiento(self) -> float:
        """Calcula el desplazamiento entre el inicio y el final."""
        observaciones = sorted(self.observaciones, key=lambda dato: dato.frame)
        if len(observaciones) < 2:
            return 0.0
        return Trayectoria.calcular_distancia_entre(observaciones[0], observaciones[-1])

    def calcular_velocidades(self, fps: float) -> list[tuple[Observacion, Observacion, float]]:
        """Calcula velocidad y observaciones de cada tramo."""
        if fps <= 0:
            return []
        observaciones = sorted(self.observaciones, key=lambda dato: dato.frame)
        return [
            (actual, siguiente,
             Trayectoria.calcular_distancia_entre(actual, siguiente)
             / ((siguiente.frame - actual.frame) / fps))
            for actual, siguiente in zip(observaciones, observaciones[1:])
            if siguiente.frame > actual.frame
        ]

    def calcular_tiempo_total(self, fps: float) -> float:
        """Calcula el tiempo entre la primera y la última observación, en segundos."""
        observaciones = sorted(self.observaciones, key=lambda dato: dato.frame)
        if fps <= 0 or len(observaciones) < 2:
            return 0.0
        return (observaciones[-1].frame - observaciones[0].frame) / fps

    def calcular_velocidad_media(self, fps: float) -> float:
        """Calcula la velocidad media usando la frecuencia del experimento."""
        tiempo_total = self.calcular_tiempo_total(fps)
        if tiempo_total <= 0:
            return 0.0
        return self.calcular_distancia_total() / tiempo_total
