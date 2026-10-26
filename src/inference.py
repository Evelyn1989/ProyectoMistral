import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import requests


def ejecutar_prompt(args, prueba):
    # Envia la pregunta al servidor local de Ollama.
    datos = {
        "model": args.modelo,
        "prompt": prueba["prompt"],
        "stream": True,
        "options": {
            "temperature": args.temperatura,
            "num_predict": args.max_tokens,
            "num_ctx": 4096,
            "seed": 42
        }
    }

    inicio = time.perf_counter()
    primer_token = None
    partes = []
    final = None

    with requests.post(
        args.servidor.rstrip("/") + "/api/generate",
        json=datos,
        stream=True,
        timeout=(10, 600)
    ) as respuesta:

        if respuesta.status_code == 404:
            raise RuntimeError(
                "Modelo no encontrado. Revisa el nombre con ollama list."
            )

        respuesta.raise_for_status()

        # Lee la respuesta por partes para medir el primer texto recibido.
        for linea in respuesta.iter_lines(chunk_size=1):
            if not linea:
                continue

            evento = json.loads(linea)

            if evento.get("error"):
                raise RuntimeError(evento["error"])

            texto = evento.get("response", "")

            if texto:
                if primer_token is None:
                    primer_token = time.perf_counter() - inicio
                partes.append(texto)
                print(texto, end="", flush=True)

            if evento.get("done"):
                final = evento
                break

    if final is None:
        raise RuntimeError("La respuesta se interrumpio antes de terminar.")

    tiempo_total = time.perf_counter() - inicio
    tokens = final.get("eval_count", 0)
    segundos_generacion = final.get("eval_duration", 0) / 1_000_000_000

    velocidad = (
        tokens / segundos_generacion
        if segundos_generacion > 0 else None
    )

    return {
        "id": prueba["id"],
        "categoria": prueba.get("categoria", "individual"),
        "modelo": args.modelo,
        "prompt": prueba["prompt"],
        "salida": "".join(partes),
        "temperatura": args.temperatura,
        "max_tokens": args.max_tokens,
        "contexto": 4096,
        "semilla": 42,
        "tokens_generados": tokens,
        "ttft_s": primer_token,
        "tiempo_total_s": tiempo_total,
        "tokens_por_segundo": velocidad,
        "motivo_fin": final.get("done_reason"),
        "fecha": datetime.now().astimezone().isoformat(),
        "calificacion": "",
        "justificacion": ""
    }


def main():
    parser = argparse.ArgumentParser(
        description="Pruebas de un modelo local con Ollama."
    )

    parser.add_argument(
        "--modelo",
        default="ministral-3:3b-instruct-2512-q4_K_M"
    )

    entrada = parser.add_mutually_exclusive_group(required=True)
    entrada.add_argument("--prompt", help="Pregunta para el modelo.")
    entrada.add_argument("--archivo", help="Archivo JSON con las pruebas.")

    parser.add_argument("--temperatura", type=float, default=0.2)
    parser.add_argument("--max-tokens", type=int, default=256)
    parser.add_argument("--salida", default="results")
    parser.add_argument(
        "--servidor",
        default=os.environ.get("OLLAMA_HOST", "http://localhost:11434")
    )

    args = parser.parse_args()

    if args.temperatura < 0 or args.max_tokens <= 0:
        parser.error("La temperatura debe ser >= 0 y max-tokens > 0.")

    try:
        if args.archivo:
            # utf-8-sig permite leer archivos con o sin marca BOM.
            pruebas = json.loads(
                Path(args.archivo).read_text(encoding="utf-8-sig")
            )
        else:
            pruebas = [{
                "id": "prueba_01",
                "categoria": "individual",
                "prompt": args.prompt
            }]

        if not isinstance(pruebas, list) or not pruebas:
            raise ValueError("La suite debe contener una lista de pruebas.")

        for prueba in pruebas:
            if not isinstance(prueba, dict):
                raise ValueError("Cada prueba debe ser un objeto JSON.")
            if "id" not in prueba or not isinstance(
                prueba.get("prompt"), str
            ):
                raise ValueError("Cada prueba necesita id y prompt.")
            if not prueba["prompt"].strip():
                raise ValueError("El prompt no puede estar vacio.")

        carpeta = Path(args.salida)
        carpeta.mkdir(parents=True, exist_ok=True)
        nombre = datetime.now().strftime("resultados_%Y%m%d_%H%M%S_%f.json")
        destino = carpeta / nombre
        resultados = []

        for numero, prueba in enumerate(pruebas, start=1):
            print(f"\n--- Prueba {numero}/{len(pruebas)}: {prueba['id']} ---")
            resultado = ejecutar_prompt(args, prueba)
            resultados.append(resultado)

            # Guarda cada prueba terminada para conservar el avance.
            destino.write_text(
                json.dumps(resultados, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )

            print("\n")
            ttft = resultado["ttft_s"]
            velocidad = resultado["tokens_por_segundo"]

            if ttft is not None:
                print(f"Tiempo al primer texto (TTFT): {ttft:.3f} s")
            if velocidad is not None:
                print(f"Velocidad: {velocidad:.2f} tokens/s")
            print(f"Tokens generados: {resultado['tokens_generados']}")
            print(f"Resultados guardados en: {destino}")

    except requests.exceptions.ConnectionError:
        print(
            "\nERROR: No se pudo conectar con Ollama. "
            "Comprueba que la aplicacion este abierta.",
            file=sys.stderr
        )
        return 1
    except requests.exceptions.Timeout:
        print(
            "\nERROR: Ollama tardo demasiado en responder.",
            file=sys.stderr
        )
        return 1
    except (requests.exceptions.RequestException,
            OSError, ValueError, RuntimeError) as error:
        print(f"\nERROR: {error}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())