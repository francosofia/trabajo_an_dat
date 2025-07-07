import pandas as pd
import os
import matplotlib.pyplot as plt

# Lista de aglomerados del NEA
aglomerados_nea = [7, 8, 12, 15]

# Diccionario de ponderadores según variable
ponderadores = {
    "P21": "PONDIIO",   # Ocupación (ESTADO == 1)
    "P47T": "PONDII"    # Ingreso total
}

# Carpeta principal con subcarpetas por año
carpeta_principal = "bases de dato"

resultados = []  # Acumular tasas

# Recorrer subcarpetas por año
for subcarpeta in sorted(os.listdir(carpeta_principal)):
    ruta_subcarpeta = os.path.join(carpeta_principal, subcarpeta)

    if not os.path.isdir(ruta_subcarpeta):
        continue

    archivos = [f for f in os.listdir(ruta_subcarpeta) if f.endswith(".txt")]
    dfs = []

    for archivo in archivos:
        ruta = os.path.join(ruta_subcarpeta, archivo)
        df = pd.read_csv(ruta, sep=";", encoding="utf-8", low_memory=False)
        df.columns = df.columns.str.strip().str.upper().str.normalize("NFKD") \
            .str.encode("ascii", errors="ignore").str.decode("utf-8")

        columnas_necesarias = {
            'ANO4', 'TRIMESTRE', 'ESTADO', 'CH04', 'CH06', 'P47T', 'AGLOMERADO',
            ponderadores["P21"]
        }

        if columnas_necesarias.issubset(df.columns):
            df = df[list(columnas_necesarias)].rename(columns={ponderadores["P21"]: 'PONDERA'})
            df = df[df['AGLOMERADO'].isin(aglomerados_nea)]
            dfs.append(df)

    if not dfs:
        continue

    df_total = pd.concat(dfs, ignore_index=True)
    for col in ['ANO4', 'TRIMESTRE', 'CH06', 'ESTADO', 'CH04', 'P47T', 'PONDERA']:
        df_total[col] = pd.to_numeric(df_total[col], errors='coerce')

    df_total = df_total[df_total['CH06'] >= 15]
    df_total = df_total[df_total['PONDERA'] > 0]

    total = df_total.groupby(['ANO4', 'TRIMESTRE', 'CH04'])['PONDERA'].sum().rename("total")
    ocupados = df_total[df_total['ESTADO'] == 1].groupby(['ANO4', 'TRIMESTRE', 'CH04'])['PONDERA'].sum().rename("ocupados")

    tasa_empleo = pd.concat([total, ocupados], axis=1).fillna(0)
    tasa_empleo['tasa_empleo'] = tasa_empleo['ocupados'] / tasa_empleo['total']
    tasa_empleo = tasa_empleo.reset_index()
    resultados.append(tasa_empleo)

# Concatenar todos los trimestres
df_final = pd.concat(resultados, ignore_index=True)

# Crear columna de período para eje X
df_final['Periodo'] = df_final['ANO4'].astype(str) + '-T' + df_final['TRIMESTRE'].astype(str)

# Pivotear para poner CH04 (sexo) como columnas
pivot = df_final.pivot(index='Periodo', columns='CH04', values='tasa_empleo').sort_index()

# Etiquetas para leyenda
labels = {1: 'Varones', 2: 'Mujeres'}

# Gráfico de barras lado a lado
plt.figure(figsize=(14, 6))
x = range(len(pivot.index))
bar_width = 0.4

plt.bar([i - bar_width/2 for i in x], pivot[1], width=bar_width, label=labels[1])  # Varones
plt.bar([i + bar_width/2 for i in x], pivot[2], width=bar_width, label=labels[2])  # Mujeres

plt.xticks(ticks=x, labels=pivot.index, rotation=45)
plt.xlabel("Trimestre")
plt.ylabel("Tasa de Empleo")
plt.title("Tasa de empleo por trimestre y sexo – Aglomerados NEA")
plt.legend()
plt.grid(axis='y', linestyle='--', alpha=0.5)
plt.tight_layout()
plt.show()
