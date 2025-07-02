import pandas as pd
import os

# Región que queremos analizar (por ejemplo: 41 = NEA)
region_deseada = 41

# Carpeta principal con subcarpetas por año
carpeta_principal = "bases de dato"

# Recorrer subcarpetas por año
for subcarpeta in sorted(os.listdir(carpeta_principal)):
    ruta_subcarpeta = os.path.join(carpeta_principal, subcarpeta)

    if not os.path.isdir(ruta_subcarpeta):
        continue

    archivos = [f for f in os.listdir(ruta_subcarpeta) if f.endswith(".txt")]
    dfs = []

    # Leer todos los archivos .txt dentro de la subcarpeta
    for archivo in archivos:
        ruta = os.path.join(ruta_subcarpeta, archivo)
        df = pd.read_csv(ruta, sep=";", encoding="utf-8", low_memory=False)

        # Normalizar nombres de columnas
        df.columns = df.columns.str.strip().str.upper().str.normalize("NFKD") \
            .str.encode("ascii", errors="ignore").str.decode("utf-8")

        # Verificar que tenga las columnas necesarias
        columnas_necesarias = {'ANO4', 'ESTADO', 'CH04', 'CH06', 'P47T', 'REGION'}
        if columnas_necesarias.issubset(df.columns):
            df = df[list(columnas_necesarias)]

            # Filtrar por región deseada
            df = df[df['REGION'] == region_deseada]

            dfs.append(df)

    if not dfs:
        continue

    # Concatenar todos los archivos de la subcarpeta
    df_total = pd.concat(dfs, ignore_index=True)

    # Convertir columnas a tipo numérico
    for col in ['ANO4', 'CH06', 'ESTADO', 'CH04', 'P47T']:
        df_total[col] = pd.to_numeric(df_total[col], errors='coerce')

    # Filtrar edad entre 25 y 55 años
    df_total = df_total[(df_total['CH06'] >= 25) & (df_total['CH06'] <= 55)]

    # Calcular total y ocupados
    total_personas = df_total.groupby(['ANO4', 'CH04']).size().rename("total")
    ocupados = df_total[df_total['ESTADO'] == 1].groupby(['ANO4', 'CH04']).size().rename("ocupados")

    # Unir y calcular tasa de empleo
    tasa_empleo = pd.concat([total_personas, ocupados], axis=1).fillna(0)
    tasa_empleo['tasa_empleo'] = tasa_empleo['ocupados'] / tasa_empleo['total']
    tasa_empleo = tasa_empleo.reset_index()

    # Mostrar resultado por subcarpeta
    print(f"\n📊 Tasa de empleo por sexo y año para la región {region_deseada} – Carpeta: {subcarpeta}")
    print(tasa_empleo[['ANO4', 'CH04', 'tasa_empleo']])
