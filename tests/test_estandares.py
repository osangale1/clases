import ast
import inspect
import re
import sys
from pathlib import Path

from app import config
from app.graph import nodo_analista, nodo_investigador, nodo_sintesis, nodo_supervisor
from app.worker import aprobar_tarea, ejecutar_tarea

RAIZ = Path(__file__).resolve().parent.parent
CODIGO = [p for carpeta in ("app", "scripts") for p in (RAIZ / carpeta).rglob("*.py")]


def test_python_312_o_superior():
    assert sys.version_info >= (3, 12)
    assert 'requires-python = ">=3.12"' in (RAIZ / "pyproject.toml").read_text()


def test_no_se_usa_la_libreria_requests_sincrona():
    for archivo in CODIGO:
        arbol = ast.parse(archivo.read_text())
        for nodo in ast.walk(arbol):
            if isinstance(nodo, ast.Import):
                assert all(a.name.split(".")[0] != "requests" for a in nodo.names), archivo
            if isinstance(nodo, ast.ImportFrom):
                assert (nodo.module or "").split(".")[0] != "requests", archivo


def test_los_nodos_y_el_worker_son_async():
    for funcion in (nodo_supervisor, nodo_investigador, nodo_analista, nodo_sintesis, ejecutar_tarea, aprobar_tarea):
        assert inspect.iscoroutinefunction(funcion), funcion.__name__


def test_los_endpoints_de_la_api_son_async():
    arbol = ast.parse((RAIZ / "app" / "main.py").read_text())
    endpoints = [
        n
        for n in ast.walk(arbol)
        if isinstance(n, (ast.AsyncFunctionDef, ast.FunctionDef))
        and any("app." in ast.unparse(d) for d in n.decorator_list)
    ]
    assert endpoints
    assert all(isinstance(n, ast.AsyncFunctionDef) for n in endpoints)


def test_no_hay_llamadas_bloqueantes_en_funciones_async():
    for archivo in CODIGO:
        arbol = ast.parse(archivo.read_text())
        for funcion in (n for n in ast.walk(arbol) if isinstance(n, ast.AsyncFunctionDef)):
            for nodo in ast.walk(funcion):
                if isinstance(nodo, ast.Call):
                    assert ast.unparse(nodo.func) != "time.sleep", f"{archivo}:{nodo.lineno}"


def test_nada_hardcodeado_los_ids_salen_de_variables_de_entorno():
    assert config.INDEX_NAME == "curso-rag-index" or config.INDEX_NAME
    for archivo in (p for p in CODIGO if p.name != "config.py"):
        codigo = archivo.read_text()
        assert not re.search(r'index_name\s*=\s*"', codigo), archivo
        assert not re.search(r'model\s*=\s*"(gpt|claude|text-embedding)', codigo), archivo


def test_hay_archivos_de_entorno_y_despliegue():
    for nombre in (".env.example", "requirements.txt", "Dockerfile", "docker-compose.yml", "run.sh", "README.md"):
        assert (RAIZ / nombre).exists(), nombre
    assert not (RAIZ / ".env").exists() or ".env" in (RAIZ / ".gitignore").read_text()
