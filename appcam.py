import requests
import pandas as pd
from io import StringIO

url = "https://docs.google.com/spreadsheets/d/157VmpJo9qvuKDmx12yya2E1caGa28HB4Kxd3-EeY_G8/gviz/tq?tqx=out:csv"

resp = requests.get(url, timeout=20)
resp.raise_for_status()  # lanzará excepción si no se puede descargar

text = resp.content.decode('utf-8', errors='replace')
# opcional: inspeccionar inicio para detectar HTML (login) en vez de CSV
print("Primeros 300 caracteres del archivo:\n", text[:300])

df = pd.read_csv(StringIO(text))
df.columns = [c.strip() for c in df.columns]
print("Columnas detectadas:", df.columns.tolist())
print("Número de filas:", len(df))
print("\nVista previa (primeras 10 filas):")
print(df.head(10).to_string(index=False))
