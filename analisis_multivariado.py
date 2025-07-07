import pandas as pd
import os
import matplotlib.pyplot as plt

# Rutas personalizables por el usuario
carpeta_principal = "bases de dato"  # Ruta a la carpeta con los datos
ruta_caes = "caes_codigos_descripciones.csv"  # Clasificador CAES con columnas: PP04B_COD, Actividad

# Región NEA
aglomerados_nea = [7, 8, 12, 15]

# Cargar clasificadores
caes = pd.read_csv(ruta_caes, dtype={'PP04B_COD': str})

# Lista para resultados
resultados = []

# Recorrer carpetas por año
for subcarpeta in sorted(os.listdir(carpeta_principal)):
    ruta_subcarpeta = os.path.join(carpeta_principal, subcarpeta)
    if not os.path.isdir(ruta_subcarpeta):
        continue

    archivos_txt = [f for f in os.listdir(ruta_subcarpeta) if f.endswith(".txt")]
    if not archivos_txt:
        continue

    archivo = archivos_txt[0]
    ruta_archivo = os.path.join(ruta_subcarpeta, archivo)

    df = pd.read_csv(ruta_archivo, sep=";", encoding="utf-8", low_memory=False)
    df.columns = df.columns.str.strip().str.upper().str.normalize("NFKD").str.encode("ascii", errors="ignore").str.decode("utf-8")

    columnas_necesarias = {'ANO4', 'TRIMESTRE', 'CH04', 'CH06', 'NIVEL_ED', 'ESTADO', 'PP04B_COD', 'PP04D_COD', 'AGLOMERADO', 'PONDIIO'}
    if not columnas_necesarias.issubset(df.columns):
        print(f"❌ Faltan columnas necesarias en {archivo}")
        continue

    df = df[list(columnas_necesarias)]
    df = df[df['AGLOMERADO'].isin(aglomerados_nea)]

    # Conversión de tipos
    for col in ['ANO4', 'TRIMESTRE', 'CH04', 'CH06', 'NIVEL_ED', 'ESTADO', 'PONDIIO']:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # Filtrar PEA (ocupados), mayores de 15 años
    df = df[(df['ESTADO'] == 1) & (df['CH06'] >= 15) & (df['PONDIIO'] > 0)]

    # Normalizar código de actividad
    df['PP04B_COD'] = df['PP04B_COD'].astype(str).str.replace(".0", "", regex=False).str.zfill(4)

    # Merge con descripción CAES
    df = pd.merge(df, caes, how="left", on="PP04B_COD")

    # Añadir período
    df["Periodo"] = df["ANO4"].astype(str) + "-T" + df["TRIMESTRE"].astype(str)

    resultados.append(df)

# Concatenar todo
df_final = pd.concat(resultados, ignore_index=True)

# ---------- EJEMPLO DE GRÁFICO: Nivel educativo ----------
niveles_validos = df_final[df_final["NIVEL_ED"].between(1, 7)]
pivot = niveles_validos.pivot_table(index="Periodo", columns="NIVEL_ED", values="PONDIIO", aggfunc="sum").fillna(0)
pivot = pivot.sort_index()

plt.figure(figsize=(16, 8))
pivot.plot(kind="bar", stacked=True, figsize=(16, 8), width=0.9)
plt.title("Distribución de personas ocupadas por nivel educativo – Región NEA")
plt.xlabel("Trimestre")
plt.ylabel("Cantidad ponderada de personas")
plt.xticks(rotation=45)
plt.legend(title="Nivel educativo")
plt.grid(axis="y", linestyle="--", alpha=0.5)
plt.tight_layout()
plt.show()

# ---------- EXPORTAR RESULTADO ----------
df_final.to_csv("analisis_multivariado_pea.csv", index=False)
print("✅ Archivo generado: analisis_multivariado_pea.csv")
