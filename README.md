# Proyecto Mistral AI

Proyecto individual de Programación IV de la Universidad Central.

- Estudiante: Evelyn Johanna Fallas López
- Profesor: Gilder López
- Modelo evaluado: Ministral 3 3B de Mistral AI
- Configuraciones comparadas: Q4_K_M y Q8_0

## Objetivo

Ejecutar un modelo de lenguaje local mediante Ollama y un script en Python, evaluar sus respuestas y comparar el desempeño de dos cuantizaciones.

## Requisitos

- Windows con PowerShell.
- Python 3.12.
- Ollama instalado y en ejecución.
- Git.
- Docker Desktop con motor Linux y WSL 2 para ejecutar el contenedor.

Las mediciones se realizaron en una computadora con 16 GB de RAM. El rendimiento y la memoria necesaria dependen del equipo y de la configuración del modelo.

## Descargar el proyecto

```powershell
git clone https://github.com/Evelyn1989/ProyectoMistral.git
cd ProyectoMistral
```

## Preparar Python

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

No es necesario activar el entorno virtual si se utiliza directamente su ejecutable de Python.

## Descargar el modelo

Con Ollama abierto:

```powershell
ollama pull ministral-3:3b-instruct-2512-q4_K_M
ollama list
```

Para repetir la comparación con Q8, se debe descargar la variante Q8_0 y utilizar su nombre exacto, tal como aparece en `ollama list`.

## Ejecutar una consulta

```powershell
.\.venv\Scripts\python.exe src/inference.py --modelo ministral-3:3b-instruct-2512-q4_K_M --prompt "Explica en tres frases que es la inteligencia artificial." --temperatura 0.2 --max-tokens 150 --servidor http://localhost:11434
```

## Ejecutar la suite

```powershell
.\.venv\Scripts\python.exe src/inference.py --modelo ministral-3:3b-instruct-2512-q4_K_M --archivo prompts/suite.json --temperatura 0.2 --max-tokens 256 --salida results/reproduccion_q4 --servidor http://localhost:11434
```

La suite contiene diez pruebas en cinco categorías:

- Generación de texto.
- Resumen.
- Corrección y traducción.
- Código Python y SQL.
- Razonamiento y veracidad.

El script guarda las respuestas y las métricas en archivos JSON dentro de la carpeta de salida.

Para consultar los argumentos disponibles:

```powershell
.\.venv\Scripts\python.exe src/inference.py --help
```

## Comparar temperaturas de muestreo

```powershell
.\.venv\Scripts\python.exe src/inference.py --modelo ministral-3:3b-instruct-2512-q4_K_M --archivo prompts/temperatura.json --temperatura 0.2 --max-tokens 256 --salida results/temperatura_02
```

```powershell
.\.venv\Scripts\python.exe src/inference.py --modelo ministral-3:3b-instruct-2512-q4_K_M --archivo prompts/temperatura.json --temperatura 0.9 --max-tokens 256 --salida results/temperatura_09
```

La temperatura de muestreo controla la aleatoriedad de las respuestas; no representa la temperatura física del equipo.

## Ejecutar con Docker

Abrir Docker Desktop y mantener Ollama en ejecución en Windows.

Construir la imagen:

```powershell
docker build -t proyecto-mistral:1.0 .
```

Crear la carpeta de resultados si no existe:

```powershell
New-Item -ItemType Directory -Force results | Out-Null
```

Ejecutar una consulta desde el contenedor:

```powershell
docker run --rm --mount "type=bind,source=$($PWD.Path)\results,target=/app/results" proyecto-mistral:1.0 --modelo ministral-3:3b-instruct-2512-q4_K_M --servidor http://host.docker.internal:11434 --prompt "Explica en tres frases que es la inteligencia artificial." --temperatura 0.2 --max-tokens 150
```

Ejecutar la suite desde el contenedor:

```powershell
docker run --rm --mount "type=bind,source=$($PWD.Path)\results,target=/app/results" proyecto-mistral:1.0 --modelo ministral-3:3b-instruct-2512-q4_K_M --servidor http://host.docker.internal:11434 --archivo prompts/suite.json --temperatura 0.2 --max-tokens 256
```

El contenedor ejecuta el cliente Python. Ollama y el modelo permanecen en Windows. Los pesos no se incluyen en la imagen, lo que evita duplicar su descarga.

La dirección `host.docker.internal` permite acceder al equipo anfitrión desde Docker Desktop. Si la conexión falla, comprobar que Ollama esté abierto y que su API sea accesible desde el contenedor. Si se modifica su configuración de escucha, reiniciar Ollama y limitar el acceso mediante el firewall.

La imagen utiliza una base ligera con versión fija, instala primero las dependencias para aprovechar la caché y ejecuta el script con un usuario sin privilegios de administrador.

## Resultados obtenidos

Se realizaron tres corridas de la suite por cuantización.

| Métrica | Q4_K_M | Q8_0 |
|---|---:|---:|
| Tiempo medio hasta el primer texto | 6.981 s | 12.807 s |
| Velocidad media de generación | 6.125 tokens/s | 4.346 tokens/s |
| Promedio de los picos de RAM del equipo | 11.905 GiB | 13.150 GiB |
| Uso medio de CPU del equipo | 57.12 % | 58.94 % |

La memoria y el uso de CPU corresponden al equipo completo, no exclusivamente al modelo. Los tiempos hasta el primer texto pueden verse afectados por la carga inicial del modelo y otras actividades del sistema.

Ejemplo de la consulta ejecutada con Docker:

```text
Tiempo al primer texto (TTFT): 34.766 s
Velocidad: 5.62 tokens/s
Tokens generados: 104
```

Este ejemplo corresponde a una consulta individual y no al promedio de las tres corridas.

## Estructura

```text
ProyectoMistral/
├── README.md
├── requirements.txt
├── Dockerfile
├── .dockerignore
├── .gitignore
├── src/
│   ├── inference.py
│   └── monitor.py
├── prompts/
│   ├── suite.json
│   └── temperatura.json
├── results/
│   ├── q4_medido/
│   ├── q8_medido/
│   ├── temperatura_02/
│   └── temperatura_09/
└── docs/
    ├── docker-build.log
    ├── docker-images.log
    └── docker-run.log
```

Cada corrida medida contiene las respuestas y un archivo `recursos.json`. El script `monitor.py` se utilizó para registrar recursos del sistema.

## Limitaciones

Las respuestas pueden contener errores o información inventada y requieren revisión. Los resultados corresponden al equipo y a las condiciones de estas pruebas. No se ejecutaron pruebas de rendimiento en servicios de nube; sus costos se estimaron documentalmente en el informe.

## Uso de inteligencia artificial

Se utilizó ChatGPT como apoyo para organizar el trabajo, elaborar y explicar código, interpretar errores y preparar documentación. Las pruebas de inferencia se ejecutaron en la computadora de la estudiante. El informe incluye la declaración de uso de IA.