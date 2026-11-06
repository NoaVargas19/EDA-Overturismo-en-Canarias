"""Funciones auxiliares para el EDA de sobreturismo en Gran Canaria.

Esquema de los CSV esperados en src/data/ (descargados de ISTAC, ver README):
    frontur_mensual.csv  -> fecha (YYYY-MM-01), isla, turistas
    vivienda_vacacional.csv -> fecha (YYYY-MM-01), isla, viviendas
    poblacion_islas.csv  -> isla, habitantes
"""
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
VERANO = [6, 7, 8]  # junio, julio, agosto (cambia aquí si defines el verano distinto)

MESES_ES = {1: "ene", 2: "feb", 3: "mar", 4: "abr", 5: "may", 6: "jun",
            7: "jul", 8: "ago", 9: "sep", 10: "oct", 11: "nov", 12: "dic"}


def cargar_csv(nombre: str, **kwargs) -> pd.DataFrame:
    """Lee un CSV de src/data/ con un error claro si falta el archivo."""
    ruta = DATA_DIR / nombre
    if not ruta.exists():
        raise FileNotFoundError(
            f"Falta {ruta}. Descárgalo de ISTAC y guárdalo con ese nombre (ver README)."
        )
    return pd.read_csv(ruta, **kwargs)


def limpiar_serie_mensual(df: pd.DataFrame, columna_valor: str) -> pd.DataFrame:
    """Limpieza básica: tipos, espacios, duplicados y nulos (los nulos se reportan, no se rellenan)."""
    df = df.copy()
    df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
    df["isla"] = df["isla"].astype(str).str.strip()
    df[columna_valor] = pd.to_numeric(df[columna_valor], errors="coerce")

    n_dup = df.duplicated(subset=["fecha", "isla"]).sum()
    n_nulos = df[[ "fecha", columna_valor]].isna().any(axis=1).sum()
    print(f"Duplicados eliminados: {n_dup} | Filas con fecha/valor nulo eliminadas: {n_nulos}")

    df = df.drop_duplicates(subset=["fecha", "isla"]).dropna(subset=["fecha", columna_valor])
    df["anio"] = df["fecha"].dt.year
    df["mes"] = df["fecha"].dt.month
    return df.sort_values("fecha").reset_index(drop=True)


def resumen_verano(df: pd.DataFrame, isla: str, anio: int, meses=VERANO) -> dict:
    """Total de turistas del verano, mes pico y su cifra para una isla y año."""
    sub = df[(df["isla"] == isla) & (df["anio"] == anio) & (df["mes"].isin(meses))]
    if sub.empty:
        raise ValueError(f"No hay datos de {isla} en {anio} para los meses {meses}")
    pico = sub.loc[sub["turistas"].idxmax()]
    return {
        "isla": isla,
        "anio": anio,
        "meses_incluidos": [MESES_ES[m] for m in sorted(sub["mes"].unique())],
        "total_verano": int(sub["turistas"].sum()),
        "mes_pico": MESES_ES[int(pico["mes"])],
        "turistas_mes_pico": int(pico["turistas"]),
    }


def turistas_por_habitante(df_turistas: pd.DataFrame, df_poblacion: pd.DataFrame, anio: int) -> pd.DataFrame:
    """Presión turística por isla: turistas del año / habitantes (para el dato 'isla que más sufre')."""
    anual = (df_turistas[df_turistas["anio"] == anio]
             .groupby("isla", as_index=False)["turistas"].sum())
    out = anual.merge(df_poblacion, on="isla", how="inner")
    out["turistas_por_habitante"] = (out["turistas"] / out["habitantes"]).round(2)
    return out.sort_values("turistas_por_habitante", ascending=False).reset_index(drop=True)


def preparar_frontur_istac(ruta_tsv, salida="frontur_mensual.csv") -> pd.DataFrame:
    """Convierte el TSV de observaciones de ISTAC (dataset E16028B_000011) en un CSV limpio.

    Se queda con: turistas principales, residencia 'Total', medida 'Turistas'
    (descarta las variaciones y los turistas secundarios, que cuentan doble).
    Devuelve y guarda un CSV con columnas: fecha, isla, turistas.
    """
    raw = pd.read_csv(ruta_tsv, sep="\t", dtype=str)
    f = raw[(raw["TIPO_VIAJERO"] == "Turistas principales")
            & (raw["LUGAR_RESIDENCIA"] == "Total")
            & (raw["MEDIDAS"] == "Turistas")].copy()
    out = pd.DataFrame({
        "fecha": pd.to_datetime(f["TIME_PERIOD"], format="%m/%Y"),
        "isla": f["TERRITORIO"],
        "turistas": pd.to_numeric(f["OBS_VALUE"], errors="coerce"),
    })
    n_nulos = out["turistas"].isna().sum()
    print(f"Filas sin dato (ISTAC: 'valor no disponible', p. ej. COVID 2020): {n_nulos}")
    out = out.dropna(subset=["turistas"]).sort_values(["isla", "fecha"]).reset_index(drop=True)
    out.to_csv(DATA_DIR / salida, index=False)
    return out


ISLAS = ["Lanzarote", "Fuerteventura", "Gran Canaria", "Tenerife",
         "La Gomera", "La Palma", "El Hierro"]


def preparar_vv_istac(ruta_tsv, medida="Viviendas vacacionales disponibles"):
    """Convierte el TSV de ISTAC (dataset C00065A_000061, vivienda vacacional) en dos CSV limpios.

    El TSV mezcla Canarias, islas y municipios en la misma columna TERRITORIO. Los municipios
    vienen justo después de su isla, así que se asigna cada municipio a su isla por el orden.
    Guarda en src/data/:
      vivienda_vacacional.csv -> fecha, isla, viviendas            (solo islas)
      vv_municipios.csv       -> fecha, isla, municipio, viviendas (solo municipios)
    """
    raw = pd.read_csv(ruta_tsv, sep="\t", dtype=str)
    raw = raw[raw["MEDIDAS"] == medida].copy()
    raw["fecha"] = pd.to_datetime(raw["TIME_PERIOD"], format="%m/%Y")
    raw["viviendas"] = pd.to_numeric(raw["OBS_VALUE"], errors="coerce")

    isla_actual, mapa = None, {}
    for terr in dict.fromkeys(raw["TERRITORIO"]):  # respeta el orden del archivo
        if terr == "Canarias":
            continue
        if terr in ISLAS:
            isla_actual = terr
        elif terr == "Desconocido":
            isla_actual = None
            mapa[terr] = None
        else:
            mapa[terr] = isla_actual

    islas = (raw[raw["TERRITORIO"].isin(ISLAS)]
             .rename(columns={"TERRITORIO": "isla"})[["fecha", "isla", "viviendas"]]
             .dropna().sort_values(["isla", "fecha"]))
    muni = raw[raw["TERRITORIO"].isin(mapa)].copy()
    muni["isla"] = muni["TERRITORIO"].map(mapa)
    muni = (muni.rename(columns={"TERRITORIO": "municipio"})[["fecha", "isla", "municipio", "viviendas"]]
            .dropna(subset=["isla", "viviendas"]).sort_values(["isla", "municipio", "fecha"]))

    islas.to_csv(DATA_DIR / "vivienda_vacacional.csv", index=False)
    muni.to_csv(DATA_DIR / "vv_municipios.csv", index=False)
    return islas, muni


def preparar_poblacion_istac(ruta_tsv, anio=2025):
    """Convierte el TSV de población de ISTAC (dataset E30245A_000002) en dos CSV limpios.

    Igual que en vivienda, el TSV mezcla Canarias, islas y municipios; los municipios van
    justo después de su isla. Guarda en src/data/:
      poblacion_islas.csv      -> isla, habitantes
      poblacion_municipios.csv -> isla, municipio, habitantes
    """
    raw = pd.read_csv(ruta_tsv, sep="\t", dtype=str)
    raw = raw[(raw["MEDIDAS"] == "Población") & (raw["TIME_PERIOD"] == str(anio))].copy()
    raw["habitantes"] = pd.to_numeric(raw["OBS_VALUE"], errors="coerce")

    isla_actual, filas = None, []
    for terr, hab in zip(raw["TERRITORIO"], raw["habitantes"]):
        if terr == "Canarias":
            continue
        if terr in ISLAS:
            isla_actual = terr
            filas.append((terr, None, hab))
        else:
            filas.append((isla_actual, terr, hab))
    df = pd.DataFrame(filas, columns=["isla", "municipio", "habitantes"]).dropna(subset=["habitantes"])
    islas = df[df["municipio"].isna()][["isla", "habitantes"]].reset_index(drop=True)
    muni = df[df["municipio"].notna()].reset_index(drop=True)
    islas.to_csv(DATA_DIR / "poblacion_islas.csv", index=False)
    muni.to_csv(DATA_DIR / "poblacion_municipios.csv", index=False)
    return islas, muni
