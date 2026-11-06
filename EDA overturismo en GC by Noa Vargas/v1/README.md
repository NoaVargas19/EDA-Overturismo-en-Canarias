# Sobreturismo y vivienda vacacional en Gran Canaria

EDA sobre la presión turística en Gran Canaria: cuántos turistas recibió la isla este verano (2026),
cuándo fue el pico y qué papel juega la vivienda vacacional (VV) en el acceso a la vivienda.

**Tecnologías:** Python, pandas, matplotlib/seaborn, Jupyter.

## Estructura
```
src/
  memoria.ipynb        # memoria completa del análisis
  data/                # CSV de ISTAC (ver abajo) + hechos_verificados.csv
  notebooks/           # notebooks de pruebas
  utils/helpers.py     # carga, limpieza y funciones de análisis
```

## Datos (ISTAC, datos abiertos)
Descargados del explorador de estadísticas de ISTAC (formato TSV) y convertidos a CSV con las funciones de `src/utils/helpers.py`:

| Archivo en `src/data/` | Contenido | Dataset ISTAC |
|---|---|---|
| `frontur_mensual.csv` | Turistas principales por isla y mes (2010-2026) | FRONTUR, E16028B_000011 |
| `vivienda_vacacional.csv` | Viviendas vacacionales disponibles por isla y mes (2019-2026) | C00065A_000061 |
| `vv_municipios.csv` | Lo mismo, por municipio | C00065A_000061 |
| `poblacion_islas.csv` | Habitantes por isla a 1-1-2025 | E30245A_000002 |
| `poblacion_municipios.csv` | Habitantes por municipio a 1-1-2025 | E30245A_000002 |
| `hechos_verificados.csv` | Cifras clave citadas en la presentación | varias (ISTAC) |

## Cómo ejecutarlo
```
pip install -r requirements.txt
jupyter notebook src/memoria.ipynb
```
