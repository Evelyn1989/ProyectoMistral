import argparse
import json
import statistics
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import psutil


def main():
    parser = argparse.ArgumentParser(
        description="Ejecuta la suite y mide los recursos del equipo."
    )
    parser.add_argument(
        "--modelo",
        default="ministral-3:3b-instruct-2512-q4_K_M"
    )
    parser.add_argument("--etiqueta", required=True)
    args = parser.parse_args()

    # Cada corrida tiene una carpeta independiente.
    fecha = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    carpeta = Path("results") / args.etiqueta / fecha
    carpeta.mkdir(parents=True, exist_ok=True)

    script = Path(__file__).with_name("inference.py")
    comando = [
        sys.executable,
        str(script),
        "--modelo", args.modelo,
        "--archivo", "prompts/suite.json",
        "--temperatura", "0.2",
        "--max-tokens", "256",
        "--salida", str(carpeta)
    ]

    muestras = []
    inicio = time.perf_counter()

    # Inicia el contador antes de medir.
    psutil.cpu_percent(interval=None)
    proceso = subprocess.Popen(comando)

    try:
        while True:
            codigo = proceso.poll()
            memoria = psutil.virtual_memory()

            muestras.append({
                "segundos": round(time.perf_counter() - inicio, 3),
                "cpu_equipo_pct": psutil.cpu_percent(interval=None),
                "ram_equipo_usada_gib": memoria.used / (1024 ** 3)
            })

            if codigo is not None:
                break

            time.sleep(0.5)

    except KeyboardInterrupt:
        proceso.terminate()
        proceso.wait()
        print("\nPrueba interrumpida; se conservaran las muestras.")

    # La primera lectura de CPU no representa un intervalo completo.
    cpu = [m["cpu_equipo_pct"] for m in muestras[1:]]
    ram = [m["ram_equipo_usada_gib"] for m in muestras]

    resultado = {
        "modelo": args.modelo,
        "etiqueta": args.etiqueta,
        "alcance": "Equipo completo, no solo Ollama",
        "intervalo_muestreo_s": 0.5,
        "codigo_salida": proceso.returncode,
        "duracion_s": time.perf_counter() - inicio,
        "cpu_promedio_pct": statistics.mean(cpu) if cpu else None,
        "cpu_pico_pct": max(cpu) if cpu else None,
        "ram_pico_gib": max(ram),
        "muestras": muestras
    }

    destino = carpeta / "recursos.json"
    destino.write_text(
        json.dumps(resultado, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print(f"\nRecursos guardados en: {destino}")
    print(f"RAM pico del equipo: {resultado['ram_pico_gib']:.3f} GiB")

    if cpu:
        print(f"CPU promedio del equipo: {resultado['cpu_promedio_pct']:.2f}%")

    return 0 if proceso.returncode == 0 else 1


if __name__ == "__main__":
    sys.exit(main())