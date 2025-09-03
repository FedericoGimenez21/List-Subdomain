# Subdomain Recon

Script para la enumeracion automatizada de subdominios de niveles 1, 2 y 3 para testfire.net y vulnweb.com.

## Requisitos
- Python 3.7+
- Las siguientes herramientas deben estar instaladas y en el PATH:
  - subscraper
  - subfinder
  - amass
  - assetfinder
  - sublist3r

## Instalacion en un entorno virtual (venv)

### Linux
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Windows
```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

## Uso

```bash
python subdomain_recon.py -d <dominio> [-o <directorio_output>] [-v]
```
- `<dominio>`: testfire.net o vulnweb.com
- `-o`: (opcional) directorio de salida (por defecto: output)
- `-v`: (opcional) modo verbose

## Ejemplo
```bash
python subdomain_recon.py -d testfire.net -o resultados -v
```


## ¿Cómo funciona el script?

1. **Ejecución de herramientas externas:**
  - El script ejecuta varias herramientas de enumeración de subdominios (subscraper, subfinder, amass, assetfinder, sublist3r) para el dominio objetivo.
  - Tras cada ejecución, registra en el log cuántos subdominios se encontraron.

2. **Limpieza:**
  - Combina todos los resultados y elimina duplicados, quedándose solo con subdominios únicos.

3. **Resolución DNS y verificación HTTP:**
  - Para cada subdominio, resuelve la IP y el CNAME (si existe).
  - Realiza una petición HTTP para verificar si el subdominio responde y almacena el código de estado.
  - Solo los subdominios que responden (código HTTP válido) se consideran "activos".

4. **Extracción de niveles:**
  - Extrae y enumera subdominios de nivel 2 y 3 automáticamente.

5. **Generación de reportes:**
  - Crea archivos JSON y TXT con todos los subdominios y solo los activos.
  - Incluye metadatos como timestamp, herramientas utilizadas y estadísticas.

6. **Logging y manejo de errores:**
  - El script informa el progreso y cualquier error o herramienta faltante mediante mensajes en consola.

---
## Notas
- Asegurate de tener las herramientas externas instaladas y accesibles desde la terminal.
- Los resultados se guardan en archivos JSON y TXT con metadatos y estadisticas.
