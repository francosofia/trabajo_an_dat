import pandas as pd
import os
import matplotlib.pyplot as plt

# Lista de aglomerados del NEA
aglomerados_nea = [7, 8, 12, 15]

# Carpeta principal con subcarpetas por año
carpeta_principal = "bases de dato"

# Lista para guardar los resultados
resultados = []

# Recorrer subcarpetas (por año)
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
        df.columns = df.columns.str.strip().str.upper().str.normalize('NFKD') \
            .str.encode('ascii', errors='ignore').str.decode('utf-8')

        columnas_necesarias = {'ANO4', 'TRIMESTRE', 'ESTADO', 'NIVEL_ED', 'CH06', 'AGLOMERADO'}
        if columnas_necesarias.issubset(df.columns):
            df = df[list(columnas_necesarias)]
            df = df[df['AGLOMERADO'].isin(aglomerados_nea)]
            dfs.append(df)

    if not dfs:
        continue

    # Unir los archivos del año
    df_total = pd.concat(dfs, ignore_index=True)

    # Convertir columnas a numérico
    for col in ['ANO4', 'TRIMESTRE', 'CH06', 'ESTADO', 'NIVEL_ED']:
        df_total[col] = pd.to_numeric(df_total[col], errors='coerce')

    df_total = df_total[df_total['CH06'] >= 10]

    # Filtrar PEA
    pea = df_total[df_total['ESTADO'].isin([1, 2])]

    # Agrupar por trimestre, año y nivel educativo
    conteo = pea.groupby(['ANO4', 'TRIMESTRE', 'NIVEL_ED']).size().reset_index(name='cantidad')

    # Total por año y trimestre
    total_pea = pea.groupby(['ANO4', 'TRIMESTRE']).size().reset_index(name='total_pea')

    # Unir para calcular proporciones
    resultado = pd.merge(conteo, total_pea, on=['ANO4', 'TRIMESTRE'])
    resultado['porcentaje'] = resultado['cantidad'] / resultado['total_pea'] * 100

    resultados.append(resultado)

# Concatenar todos los resultados
final = pd.concat(resultados, ignore_index=True)

# Ordenar
final = final.sort_values(by=['ANO4', 'TRIMESTRE', 'NIVEL_ED'])

# Mostrar resultados por consola
for (anio, trimestre), grupo in final.groupby(['ANO4', 'TRIMESTRE']):
    print(f"\n📅 Año {anio} - Trimestre {trimestre}")
    print(grupo[['NIVEL_ED', 'porcentaje']].to_string(index=False))

# ---------- VISUALIZACIÓN ----------

# Filtrar solo niveles del 1 al 7
final_filtrado = final[final['NIVEL_ED'].between(1, 7)]

# Crear columna de período para el eje X
final_filtrado['Periodo'] = final_filtrado['ANO4'].astype(str) + '-T' + final_filtrado['TRIMESTRE'].astype(str)

# Pivotear: filas = Periodo, columnas = Nivel_ED, valores = cantidad
pivot = final_filtrado.pivot(index='Periodo', columns='NIVEL_ED', values='cantidad').fillna(0)

# Ordenar por periodo cronológicamente
pivot = pivot.sort_index()

# Crear gráfico de barras agrupadas
pivot.plot(kind='bar', figsize=(16, 8), width=0.8)

plt.title("Cantidad de personas en la PEA por nivel educativo (1 a 7) – Aglomerados NEA")
plt.xlabel("Trimestre")
plt.ylabel("Cantidad de personas")
plt.xticks(rotation=45)
plt.legend(title="Nivel educativo")
plt.grid(axis='y', linestyle='--', alpha=0.5)
plt.tight_layout()
plt.show()
