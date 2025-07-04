import pandas as pd
import os

# Carpeta principal que contiene subcarpetas por año
carpeta_principal = "bases de dato"

# Región a analizar
region_deseada = 41

# Recorrer subcarpetas por año
for subcarpeta in sorted(os.listdir(carpeta_principal)):
    ruta_subcarpeta = os.path.join(carpeta_principal, subcarpeta)
    
    if os.path.isdir(ruta_subcarpeta):
        archivos_txt = [f for f in os.listdir(ruta_subcarpeta) if f.endswith(".txt")]
        
        if not archivos_txt:
            print(f"⚠️ No hay archivos .txt en {ruta_subcarpeta}")
            continue

        archivo = archivos_txt[0]  # Solo uno por carpeta
        ruta_archivo = os.path.join(ruta_subcarpeta, archivo)

        df = pd.read_csv(ruta_archivo, sep=";", encoding="utf-8", low_memory=False)
        df.columns = df.columns.str.strip().str.upper().str.normalize("NFKD").str.encode("ascii", errors="ignore").str.decode("utf-8")

        columnas_necesarias = {'ANO4', 'ESTADO', 'PP04B_COD', 'REGION', 'PONDERA'}
        if not columnas_necesarias.issubset(df.columns):
            print(f"❌ El archivo {archivo} no contiene las columnas necesarias.")
            continue

        # Filtrar por región
        df = df[df['REGION'] == region_deseada]
        df = df[['ANO4', 'ESTADO', 'PP04B_COD', 'PONDERA']]

        # Filtrar personas ocupadas
        ocupados = df[df['ESTADO'] == 1]

        if ocupados.empty:
            print(f"⚠️ No hay personas ocupadas en el archivo {archivo}")
            continue

        # Calcular proporción ponderada de ocupados por tipo de ocupación
        empleo_por_ocupacion = (
            ocupados.groupby(['ANO4', 'PP04B_COD'])['PONDERA']
            .sum()
            .groupby(level=0, group_keys=False)
            .apply(lambda x: x / x.sum())
            .rename("tasa_empleo_ponderada")
            .reset_index()
        )

        # Mostrar resultados
        print(f"\n📊 Proporción ponderada de ocupados por tipo de ocupación – Región {region_deseada} – Año {subcarpeta}:")
        print(empleo_por_ocupacion)
