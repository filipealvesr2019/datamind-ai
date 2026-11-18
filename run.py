"""Script Principal de Execução — DataMind AI
Inicializa a aplicação web com FastAPI e Uvicorn.
"""

import sys
from pathlib import Path
import uvicorn

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR / "backend" / "app"))

if __name__ == "__main__":
    print("=" * 60)
    print("Iniciando DataMind AI — Analista Empresarial Inteligente")
    print("Acesse no navegador: http://127.0.0.1:8080")
    print("=" * 60)
    uvicorn.run("main:app", host="127.0.0.1", port=8080, reload=True)
