import pandas as pd
import os

# Lista de aglomerados del NEA
aglomerados_nea = [7, 8, 12, 15]

# Diccionario de ponderadores según variable
ponderadores = {
    "P21": "PONDIIO",   # Ocupación (ESTADO == 1)
    "P47T": "PONDII"    # Ingreso total
}

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
        columnas_necesarias = {
            'ANO4', 'TRIMESTRE', 'ESTADO', 'CH04', 'CH06', 'P47T', 'AGLOMERADO',
            ponderadores["P21"]  # PONDIIO
        }
        if columnas_necesarias.issubset(df.columns):
            df = df[list(columnas_necesarias)]
            df = df.rename(columns={ponderadores["P21"]: 'PONDERA'})  # renombramos a 'PONDERA' para facilitar

            # Filtrar por aglomerados NEA
            df = df[df['AGLOMERADO'].isin(aglomerados_nea)]

            dfs.append(df)

    if not dfs:
        continue

    # Concatenar todos los archivos de la subcarpeta
    df_total = pd.concat(dfs, ignore_index=True)

    # Convertir columnas a tipo numérico
    for col in ['ANO4', 'TRIMESTRE', 'CH06', 'ESTADO', 'CH04', 'P47T', 'PONDERA']:
        df_total[col] = pd.to_numeric(df_total[col], errors='coerce')

    # Filtrar edad entre 25 y 55 años y ponderaciones válidas
    df_total = df_total[df_total['CH06']>=15]
    df_total = df_total[df_total['PONDERA'] > 0]

    # Calcular total de personas (sin filtrar por ESTADO)
    total_personas = df_total.groupby(['ANO4', 'TRIMESTRE', 'CH04'])['PONDERA'].sum().rename("total")

    # Filtrar ocupados (ESTADO == 1)
    ocupados = df_total[df_total['ESTADO'] == 1].groupby(['ANO4', 'TRIMESTRE', 'CH04'])['PONDERA'].sum().rename("ocupados")

    # Unir y calcular tasa de empleo ponderada
    tasa_empleo = pd.concat([total_personas, ocupados], axis=1).fillna(0)
    tasa_empleo['tasa_empleo'] = tasa_empleo['ocupados'] / tasa_empleo['total']
    tasa_empleo = tasa_empleo.reset_index()

    # Mostrar resultado
    print(f"\n📊 Tasa de empleo ponderada por trimestre, sexo y año – Aglomerados NEA – Carpeta: {subcarpeta}")
    print(tasa_empleo[['ANO4', 'TRIMESTRE', 'CH04', 'tasa_empleo']])

