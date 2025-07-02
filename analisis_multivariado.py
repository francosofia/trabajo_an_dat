import pandas as pd
import numpy as np
import os
from ipc import *
# Inflación IPC para ajuste de ingresos


# Región que se desea analizar
region_deseada = 41

# Carpeta principal que contiene subcarpetas por año
carpeta_principal = "bases de dato"

# Recorrer subcarpetas (por año) y procesar los .txt
for subcarpeta in sorted(os.listdir(carpeta_principal)):
    ruta_subcarpeta = os.path.join(carpeta_principal, subcarpeta)
    
    if not os.path.isdir(ruta_subcarpeta):
        continue

    archivos = [f for f in os.listdir(ruta_subcarpeta) if f.endswith(".txt")]
    dfs = []

    for archivo in archivos:
        ruta = os.path.join(ruta_subcarpeta, archivo)
        df = pd.read_csv(ruta, sep=";", encoding="utf-8", low_memory=False)

        # Normalizar columnas
        df.columns = df.columns.str.strip().str.upper().str.normalize('NFKD') \
            .str.encode('ascii', errors='ignore').str.decode('utf-8')

        # Filtrar columnas necesarias
        columnas_necesarias = {'ANO4', 'TRIMESTRE', 'ESTADO', 'NIVEL_ED', 'CH06', 'P47T', 'REGION'}
        if columnas_necesarias.issubset(df.columns):
            df = df[list(columnas_necesarias)]
            df = df[df['REGION'] == region_deseada]
            dfs.append(df)

    if not dfs:
        continue

    # Concatenar los dataframes de la subcarpeta
    df = pd.concat(dfs, ignore_index=True)

    # Conversión de tipos y limpieza
    df = df[df['CH06'] >= 1]
    df['ANO4'] = pd.to_numeric(df['ANO4'], errors='coerce')
    df['TRIMESTRE'] = pd.to_numeric(df['TRIMESTRE'], errors='coerce')
    df['CH06'] = pd.to_numeric(df['CH06'], errors='coerce')
    df['P47T'] = pd.to_numeric(df['P47T'], errors='coerce')

    # Filtrar PEA
    pea = df[df['ESTADO'].isin([1, 2])]

    # Ajustar ingresos por inflación
# Ajustar ingresos por inflación
    df['ipc'] = df['ANO4'].map(ipc)
    df['ingreso_real'] = df['P47T'] / df['ipc']
# Crear clave combinada Año-Trimestre para el IPC
    df['clave_ipc'] = df['ANO4'].astype(int).astype(str) + '-T' + df['TRIMESTRE'].astype(int).astype(str)

# Mapear IPC a partir del nuevo diccionario
    df['ipc'] = df['clave_ipc'].map(ipc)

# Calcular ingreso real ajustado por IPC
    df['ingreso_real'] = df['P47T'] / df['ipc']


    # ───── Análisis 1 ─────
    grouped = pea.groupby(['ANO4', 'NIVEL_ED'])['ESTADO'].value_counts(normalize=True).unstack().fillna(0)
    grouped['tasa_desocupacion'] = grouped[2] / (grouped[1] + grouped[2])

    print(f"\n📊 Tasa de desocupación por nivel educativo ({subcarpeta}) – Región {region_deseada}:")
    print(grouped['tasa_desocupacion'])

    # ───── Análisis 2 ─────
    edad_ingresos = df[df['P47T'].notnull()].groupby('CH06')['ingreso_real'].mean()
    print(f"\n📊 Ingreso real promedio por edad ({subcarpeta}) – Región {region_deseada}:")
    print(edad_ingresos)
