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

## Notas
- Asegurate de tener las herramientas externas instaladas y accesibles desde la terminal.
- Los resultados se guardan en archivos JSON y TXT con metadatos y estadisticas.
