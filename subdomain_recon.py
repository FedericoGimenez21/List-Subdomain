#!/usr/bin/env python3
"""
subdomain_recon.py

Script para automatizar la enumeracion de subdominios de niveles 1, 2 y 3 para testfire.net y vulnweb.com.

Requisitos:
- Ejecuta Subscraper, Subfinder, Amass, Assetfinder y Sublist3r
- Combina y filtra resultados
- Resuelve DNS y verifica HTTP
- Genera reportes JSON y TXT
- Logging y manejo de errores
"""
import argparse
import subprocess
import sys
import os
import json
import socket
import requests
import datetime
import logging
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configuracion de logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def check_tool(cmd, name):
    """Verifica si una herramienta esta instalada."""
    try:
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, timeout=10)
        return True
    except Exception as e:
        logging.warning(f"Herramienta no disponible: {name} ({e})")
        return False

def run_command(cmd, name, timeout=300):
    """Ejecuta un comando y retorna la salida."""
    try:
        result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout, text=True)
        if result.returncode != 0:
            logging.warning(f"{name} retorno codigo {result.returncode}: {result.stderr.strip()}")
        return result.stdout
    except Exception as e:
        logging.warning(f"Error ejecutando {name}: {e}")
        return ""

def parse_args():
    parser = argparse.ArgumentParser(description="Enumeracion de subdominios automatizada.")
    parser.add_argument("-d", "--domain", required=True, choices=["testfire.net", "vulnweb.com"], help="Dominio objetivo")
    parser.add_argument("-o", "--output", default="output", help="Directorio de salida")
    parser.add_argument("-v", "--verbose", action="store_true", help="Modo verbose")
    return parser.parse_args()

def get_timestamp():
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

def extract_subdomains_level(subdomains, level):
    """Extrae subdominios de un nivel especifico (2 o 3)."""
    result = set()
    for sub in subdomains:
        parts = sub.split('.')
        if len(parts) >= (level + 2):
            result.add('.'.join(parts[-(level+2):]))
    return result

def dns_resolve(subdomain, timeout=3):
    try:
        ip = socket.gethostbyname(subdomain)
        cname = None
        try:
            cname = socket.gethostbyname_ex(subdomain)[0]
        except Exception:
            pass
        return ip, cname
    except Exception:
        return None, None

def http_check(subdomain, timeout=5):
    try:
        url = f"http://{subdomain}"
        r = requests.get(url, timeout=timeout, allow_redirects=True)
        return r.status_code
    except Exception:
        return None

def main():
    args = parse_args()
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    domain = args.domain
    output_dir = args.output
    os.makedirs(output_dir, exist_ok=True)
    timestamp = get_timestamp()
    tools = {
        "subscraper": (f"python3 subscraper/subscraper/subscraper.py -d {domain} -silent -active", ["python3", "subscraper.py"]),
        "subfinder": (f"subfinder -d {domain} -all -silent", ["subfinder"]),
        #"amass": (f"amass enum -passive -d {domain}", ["amass"]),
        "assetfinder": (f"assetfinder --subs-only {domain}", ["assetfinder"]),
        "sublist3r": (f"sublist3r -d {domain}", ["python", "sublist3r"]),
    }
    available_tools = []
    all_subdomains = set()
    for name, (cmd, check) in tools.items():
        if check_tool(' '.join(check) + ' --help', name):
            logging.info(f"Ejecutando {name}...")
            out = run_command(cmd, name)
            found = set(line.strip() for line in out.splitlines() if line.strip() and domain in line)
            logging.info(f"{name}: {len(found)} subdominios encontrados tras la ejecucion.")
            all_subdomains.update(found)
            available_tools.append(name)
        else:
            logging.warning(f"{name} no está disponible. Saltando...")
    logging.info(f"Total subdominios encontrados (sin filtrar): {len(all_subdomains)}")
    # Limpieza 
    all_subdomains = set(s for s in all_subdomains if s.endswith(domain))
    logging.info(f"Total subdominios unicos: {len(all_subdomains)}")
    # Resolucion DNS y verificacion HTTP
    subdomain_data = {}
    active_subdomains = {}
    # ---
    # Resolucion DNS y verificacion HTTP de subdominios encontrados.
    # Se utiliza ThreadPoolExecutor para realizar consultas DNS y comprobaciones HTTP en paralelo,
    # acelerando el proceso para grandes listas de subdominios.
    # Para cada subdominio:
    #   - Se resuelve la IP y el CNAME (si existe).
    #   - Si la IP es valida, se realiza una peticion HTTP para verificar si el subdominio responde.
    #   - Se almacena la informacion (IP, CNAME, codigo HTTP) en subdomain_data.
    #   - Si el subdominio responde (codigo HTTP < 600), se agrega a active_subdomains.
    # ---
    with ThreadPoolExecutor(max_workers=20) as executor:
        future_to_sub = {executor.submit(dns_resolve, sub): sub for sub in all_subdomains}
        for future in as_completed(future_to_sub):
            sub = future_to_sub[future]
            ip, cname = future.result()
            if ip:
                status = http_check(sub)
                subdomain_data[sub] = {"ip": ip, "cname": cname, "http_status": status}
                if status and status < 600:
                    active_subdomains[sub] = subdomain_data[sub]
            else:
                subdomain_data[sub] = {"ip": None, "cname": None, "http_status": None}
    # Niveles 2 y 3
    lvl2 = extract_subdomains_level(all_subdomains, 2)
    lvl3 = extract_subdomains_level(all_subdomains, 3)
    # Estadisticas
    stats = {
        "total": len(all_subdomains),
        "activos": len(active_subdomains),
        "nivel2": len(lvl2),
        "nivel3": len(lvl3),
    }
    metadata = {
        "timestamp": timestamp,
        "dominio": domain,
        "herramientas": available_tools,
        "estadisticas": stats,
    }
    # Salidas
    base = os.path.join(output_dir, f"subdominios_completos_{domain}_{timestamp}")
    base_act = os.path.join(output_dir, f"subdominios_activos_{domain}_{timestamp}")
    # JSON completos
    with open(base + ".json", "w", encoding="utf-8") as f:
        json.dump({"metadata": metadata, "subdominios": subdomain_data}, f, indent=2, ensure_ascii=False)
    # JSON activos
    with open(base_act + ".json", "w", encoding="utf-8") as f:
        json.dump({"metadata": metadata, "subdominios": active_subdomains}, f, indent=2, ensure_ascii=False)
    # TXT completos
    with open(base + ".txt", "w", encoding="utf-8") as f:
        for s in sorted(all_subdomains):
            f.write(s + "\n")
    # TXT activos
    with open(base_act + ".txt", "w", encoding="utf-8") as f:
        for s in sorted(active_subdomains):
            f.write(s + "\n")
    logging.info(f"Reportes generados en: {output_dir}")
    logging.info(f"Subdominios totales: {len(all_subdomains)} | Activos: {len(active_subdomains)} | Nivel2: {len(lvl2)} | Nivel3: {len(lvl3)}")

if __name__ == "__main__":
    main()
