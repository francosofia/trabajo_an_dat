import pandas as pd
import os
import matplotlib.pyplot as plt

# Carpeta principal que contiene subcarpetas por año
carpeta_principal = "bases de dato"

# Región a analizar
region_deseada = 41

# Cargar clasificador CAES
caes = pd.read_csv("caes_codigos_descripciones.csv", dtype={'PP04B_COD': str})

# Lista para acumular resultados
todos_los_resultados = []

# Recorrer subcarpetas por año
for subcarpeta in sorted(os.listdir(carpeta_principal)):
    ruta_subcarpeta = os.path.join(carpeta_principal, subcarpeta)
    
    if os.path.isdir(ruta_subcarpeta):
        archivos_txt = [f for f in os.listdir(ruta_subcarpeta) if f.endswith(".txt")]
        
        if not archivos_txt:
            print(f"⚠️ No hay archivos .txt en {ruta_subcarpeta}")
            continue

        archivo = archivos_txt[0]
        ruta_archivo = os.path.join(ruta_subcarpeta, archivo)

        df = pd.read_csv(ruta_archivo, sep=";", encoding="utf-8", low_memory=False)
        df.columns = df.columns.str.strip().str.upper().str.normalize("NFKD").str.encode("ascii", errors="ignore").str.decode("utf-8")

        columnas_necesarias = {'ANO4', 'ESTADO', 'PP04B_COD', 'REGION', 'PONDERA'}
        if not columnas_necesarias.issubset(df.columns):
            print(f"❌ El archivo {archivo} no contiene las columnas necesarias.")
            continue

        df = df[df['REGION'] == region_deseada]
        df = df[['ANO4', 'ESTADO', 'PP04B_COD', 'PONDERA']]

        ocupados = df[df['ESTADO'] == 1]

        if ocupados.empty:
            print(f"⚠️ No hay personas ocupadas en el archivo {archivo}")
            continue

        ocupados = ocupados.copy()
        ocupados['PP04B_COD'] = ocupados['PP04B_COD'].astype(str).str.replace('.0', '', regex=False).str.zfill(4)

        empleo_por_ocupacion = (
            ocupados.groupby(['ANO4', 'PP04B_COD'])['PONDERA']
            .sum()
            .groupby(level=0, group_keys=False)
            .apply(lambda x: x / x.sum())
            .rename("tasa_empleo_ponderada")
            .reset_index()
        )

        empleo_con_descripcion = pd.merge(
            empleo_por_ocupacion,
            caes,
            on='PP04B_COD',
            how='left'
        )

        # Verificar códigos no encontrados
        codigos_no_encontrados = empleo_con_descripcion[empleo_con_descripcion['Actividad'].isna()]['PP04B_COD'].unique()
        if len(codigos_no_encontrados) > 0:
            print(f"❗ Códigos de actividad sin descripción en año {subcarpeta}: {', '.join(codigos_no_encontrados)}")

        # Guardar subcarpeta como identificador temporal (para eje X)
        empleo_con_descripcion['Periodo'] = subcarpeta
        todos_los_resultados.append(empleo_con_descripcion)

        print(f"\n📊 Proporción ponderada de ocupados por tipo de ocupación – Año {subcarpeta}:")
        print(empleo_con_descripcion[['ANO4', 'PP04B_COD', 'Actividad', 'tasa_empleo_ponderada']])

# Unir todos los resultados
df_final = pd.concat(todos_los_resultados, ignore_index=True)

# Seleccionar las 5 actividades más frecuentes
actividades_top = df_final['Actividad'].value_counts().nlargest(5).index.tolist()
df_top = df_final[df_final['Actividad'].isin(actividades_top)]

# Crear gráfico
plt.figure(figsize=(12, 6))

for actividad in actividades_top:
    datos = df_top[df_top['Actividad'] == actividad]
    plt.plot(datos['Periodo'], datos['tasa_empleo_ponderada'], marker='o', label=actividad)

plt.title("Tasa de empleo ponderada por actividad (Región NEA)")
plt.xlabel("Periodo (por año )")
plt.ylabel("Tasa de empleo ponderada")
plt.xticks(rotation=45)
plt.legend()
plt.tight_layout()
plt.grid(True)
plt.show()
