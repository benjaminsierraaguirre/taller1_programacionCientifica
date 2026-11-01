# Análisis de trayectorias peatonales

Programa en Python para leer datos, reconstruir trayectorias y analizar experimentos de circulación peatonal.

## Ejecución

```bash
python3 main.py
python3 main.py --input ./data --output ./results
python3 main.py --input ./data --output ./results --fps 25
python3 main.py --help
```

## Datos y frecuencia

En `data` van los TXT y el JSON de metadatos (`2013unidirectional_metadata.json` o `Metadata.json`). Cada línea TXT contiene ID, frame, x, y y z separados por espacios o tabulaciones. Si el TXT tiene un FPS válido, se conserva. `--fps` se usa como alternativa solo cuando falta ese dato. Si después de eso no hay un FPS válido, el programa se detiene con un mensaje claro.

## Pasos

1. Cargar TXT y JSON y crear observaciones.
2. Validar filas incompletas, valores inválidos y pares ID-frame repetidos.
3. Agrupar cada observación por peatón en una pasada y ordenar cada grupo por frame.
4. Excluir trayectorias con una sola observación de las métricas de movimiento.
5. Calcular distancias, velocidades e indicadores individuales.
6. Analizar zonas, densidad y flujo.
7. Exportar resultados a cinco CSV.

## Estilo y organización

Se usan comprensiones sencillas, `zip` para pares consecutivos, `lambda` para ordenar y ciclos directos para actualizar diccionarios o seguir una racha de detención. `Trayectoria.calcular_distancia_entre` centraliza la fórmula de distancia y es estático porque no depende de un objeto. La detección de detenciones mantiene un ciclo imperativo. Las etapas actualizan los objetos `Experimento` y retornan la colección procesada.

## Geometría y criterios

El JSON de los nueve experimentos indica un corredor de 18 m de largo y 5 m de ancho. El análisis usa su región central, x entre -9 y 9 m e y entre 0 y 5 m, dividida en tres zonas de 6 por 5 m. Las dimensiones se leen de los metadatos; los valores predeterminados con nombre son 18 m y 5 m. Las posiciones registradas fuera de esa región no se cuentan en zonas, densidad ni cruces.

En cada zona se informa el total de peatones, cuántos tienen al menos dos observaciones y cuántos aparecen una sola vez. Los promedios de velocidad y tiempo usan solo peatones con al menos dos observaciones en esa zona.

Una velocidad de 0 m/s es una detención total. Para este análisis se considera lenta una velocidad menor o igual a 0,2 m/s y se cuenta una detención solo si esa racha dura al menos 1 segundo. El criterio de velocidad y la duración mínima son decisiones del equipo que deben declararse en el informe. El flujo se calcula por intervalos de un segundo e incluye los intervalos observados sin cruces. La densidad media usa frames con al menos un peatón dentro del área; los frames vacíos quedan fuera y pueden elevar el promedio.

La velocidad máxima conserva el mayor valor observado. También se informa el percentil 95 de las velocidades por tramo para comparar experimentos sin depender tanto de un único valor extremo. El percentil se obtiene ordenando las velocidades y tomando la posición `int(0.95 * (n - 1))`.

## Salidas

`resultados_individuales.csv`, `resumen_experimentos.csv`, `resultados_zonas.csv`, `densidad.csv` y `flujo.csv`.



## Gráficos del informe

Los gráficos se generan a partir de los archivos CSV exportados por el pipeline. Desde la raíz del repositorio, instalar las dependencias de visualización y ejecutar:

```bash
python3 -m pip install matplotlib numpy pandas
python3 scripts/figuras.py --results ./results --output ./figuras
python3 scripts/aporte_ra5.py --results ./results --figuras ./figuras
```

`figuras.py` produce las figuras 1 a 8 sobre velocidades, eficiencia, detenciones, zonas, densidad y flujo. `aporte_ra5.py` calcula la proporción de trayectorias con al menos una detención y genera la figura 9 para comparar las corridas 05 a 09. Este análisis complementario se basa en los CSV ya calculados y no modifica los resultados del pipeline. Las condiciones de salida de las corridas 08 y 09 cambiaron durante la ejecución, por lo que la comparación no establece causalidad.

Los scripts de figuras están en `scripts/`; si se guardaron en otra ubicación, adaptar las rutas de los comandos.

## Análisis de sensibilidad de detenciones

Después de generar los resultados principales, ejecutar desde la raíz del repositorio:

```bash
python3 sensibilidad.py
```

El script vuelve a cargar los datos de `./data` y prueba velocidades umbral de **0,1, 0,2 y 0,3 m/s** y duraciones mínimas de **0,5, 1 y 2 segundos** para las corridas **01, 05, 08 y 09**. Guarda `results/sensibilidad.csv` y contrasta la combinación de **0,2 m/s y 1 segundo** con `results/resultados_individuales.csv`. El criterio base se utiliza en el informe; las alternativas permiten evaluar su sensibilidad.

## Orden recomendado para reproducir el informe

1. Colocar los nueve TXT y el JSON de metadatos en `data/`.
2. Ejecutar `python3 main.py --input ./data --output ./results`.
3. Ejecutar `python3 sensibilidad.py`.
4. Ejecutar los dos scripts de `scripts/` para regenerar las nueve figuras.
5. Consultar los CSV en `results/` y las imágenes en `figuras/`.

En una prueba reportada por el equipo se ejecutó el pipeline en una máquina local con Arch Linux y Python 3.14.8. Esto no equivale a una ejecución en el servidor institucional.
