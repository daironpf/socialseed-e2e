#!/usr/bin/env python3
"""
generate-tests.py - Generador automático de tests para apps del playground.

Este script analiza el archivo BUGS.md de una aplicación y genera tests
de SocialSeed E2E que detecten cada bug documentado.

Uso:
    python generate-tests.py <app-name> [opciones]

Ejemplos:
    python generate-tests.py auth-service-broken
    python generate-tests.py payment-service-broken --output ./tests
    python generate-tests.py ecommerce-broken --bug 15,16,17
"""

import argparse
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional


def parse_bugs_md(file_path: str) -> List[Dict]:
    """
    Parsear archivo BUGS.md y extraer información estructurada.

    Returns:
        Lista de diccionarios con información de cada bug:
        {
            "number": int,
            "title": str,
            "location": str,
            "problem": str,
            "impact": str,
            "solution": str,
            "category": str  # crítico, medio, funcional
        }
    """
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    bugs = []

    # Patrón para extraer bugs
    # Busca patrones como: ### BUG #1: Título
    pattern = r"###\s*BUG\s*#(\d+):\s*(.+?)(?=###|\Z)"

    for match in re.finditer(pattern, content, re.DOTALL):
        bug_num = int(match.group(1))
        bug_content = match.group(2)

        # Extraer campos
        title = bug_content.split("\n")[0].strip()

        location_match = re.search(r"\*\*Ubicación:\*\*\s*(.+?)(?=\n|$)", bug_content)
        location = location_match.group(1).strip() if location_match else ""

        problem_match = re.search(
            r"\*\*Problema:\*\*\s*(.+?)(?=\n\*\*|$)", bug_content, re.DOTALL
        )
        problem = problem_match.group(1).strip() if problem_match else ""

        impact_match = re.search(
            r"\*\*Impacto:\*\*\s*(.+?)(?=\n\*\*|$)", bug_content, re.DOTALL
        )
        impact = impact_match.group(1).strip() if impact_match else ""

        solution_match = re.search(
            r"\*\*Solución:\*\*\s*(.+?)(?=\n\*\*|$)", bug_content, re.DOTALL
        )
        solution = solution_match.group(1).strip() if solution_match else ""

        # Determinar categoría basada en el contexto
        category = "funcional"  # default
        if "🔴" in content[max(0, match.start() - 500) : match.start()]:
            category = "crítico"
        elif "🟠" in content[max(0, match.start() - 500) : match.start()]:
            category = "medio"
        elif "🟡" in content[max(0, match.start() - 500) : match.start()]:
            category = "funcional"

        bugs.append(
            {
                "number": bug_num,
                "title": title,
                "location": location,
                "problem": problem,
                "impact": impact,
                "solution": solution,
                "category": category,
            }
        )

    return bugs


def extract_endpoints(app_code: str) -> List[Dict]:
    """
    Extraer endpoints Flask del código de la aplicación.
    """
    endpoints = []

    # Patrón para @app.route
    pattern = r'@app\.route\(["\'](.+?)["\'](?:,\s*methods=\[(.+?)\])?\)'

    for match in re.finditer(pattern, app_code):
        path = match.group(1)
        methods_str = match.group(2) if match.group(2) else "'GET'"
        methods = [m.strip().strip("\"'") for m in methods_str.split(",")]

        endpoints.append({"path": path, "methods": methods})

    return endpoints


def generate_test_for_bug(bug: Dict, endpoints: List[Dict]) -> str:
    """
    Generar código de test para un bug específico.
    """
    bug_num = bug["number"]
    title = bug["title"]
    problem = bug["problem"]
    category = bug["category"]

    # Determinar el tipo de test basado en el problema
    test_code = f'''async def run(page):
    """
    Test Bug #{bug_num}: {title}
    
    Categoría: {category}
    Problema: {problem[:100]}...
    """
    # TODO: Implementar test específico para este bug
    
    # Arrange: Preparar datos de prueba
    
    # Act: Ejecutar operación que debería fallar
    
    # Assert: Verificar que el bug está presente
    # assert condition, "BUG #{bug_num}: {title}"
    
    raise NotImplementedError("Test no implementado para BUG #{bug_num}")
'''

    return test_code


def generate_page_object(app_name: str, endpoints: List[Dict]) -> str:
    """
    Generar Page Object para la aplicación.
    """
    class_name = (
        "".join(word.capitalize() for word in app_name.replace("-", "_").split("_"))
        + "Page"
    )

    methods = []
    for endpoint in endpoints:
        if endpoint["path"] == "/health":
            continue

        # Generar nombre de método
        path_parts = endpoint["path"].strip("/").split("/")
        method_name = "_".join(
            part.replace("-", "_") for part in path_parts if not part.startswith("<")
        )
        if not method_name:
            method_name = "index"

        for method in endpoint["methods"]:
            func_name = f"{method.lower()}_{method_name}"
            methods.append(f'''
    async def {func_name}(self, **kwargs):
        """{method} {endpoint["path"]}"""
        response = await self.page.request.{method.lower()}(
            f"{{self.base_url}}{endpoint["path"]}",
            data=kwargs
        )
        return response
''')

    page_object = f'''"""
Page Object para {app_name}.

Auto-generado por generate-tests.py
"""

from socialseed_e2e import BasePage


class {class_name}(BasePage):
    """Page Object para {app_name}."""
    
    async def check_health(self):
        """Verificar que el servicio está saludable."""
        response = await self.page.request.get(f"{{self.base_url}}/health")
        return response.status == 200
'''

    for method in methods:
        page_object += method

    return page_object


def main():
    parser = argparse.ArgumentParser(
        description="Generador automático de tests para apps del playground",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  %(prog)s auth-service-broken
  %(prog)s payment-service-broken --output ./my-tests
  %(prog)s ecommerce-broken --bug 15,16,17 --only-critical
        """,
    )

    parser.add_argument("app", help="Nombre de la app (ej: auth-service-broken)")
    parser.add_argument(
        "-o",
        "--output",
        default="./generated-tests",
        help="Directorio de salida (default: ./generated-tests)",
    )
    parser.add_argument(
        "-b", "--bug", type=str, help="Números de bugs específicos (ej: 1,2,3)"
    )
    parser.add_argument(
        "--only-critical",
        action="store_true",
        help="Solo generar tests para bugs críticos",
    )
    parser.add_argument(
        "--page-object", action="store_true", help="Solo generar Page Object"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="No escribir archivos, solo mostrar output",
    )

    args = parser.parse_args()

    # Encontrar la app
    playground_dir = Path(__file__).parent.parent
    app_dir = playground_dir / "broken-apps" / args.app

    if not app_dir.exists():
        print(f"❌ Error: App no encontrada: {args.app}")
        print(f"   Buscado en: {app_dir}")
        print(f"\nApps disponibles:")
        broken_apps_dir = playground_dir / "broken-apps"
        if broken_apps_dir.exists():
            for app in broken_apps_dir.iterdir():
                if app.is_dir():
                    print(f"   - {app.name}")
        sys.exit(1)

    # Leer BUGS.md
    bugs_file = app_dir / "BUGS.md"
    if not bugs_file.exists():
        print(f"❌ Error: No se encontró BUGS.md en {app_dir}")
        sys.exit(1)

    print(f"📖 Leyendo bugs de: {bugs_file}")
    bugs = parse_bugs_md(str(bugs_file))
    print(f"   Encontrados {len(bugs)} bugs\n")

    # Filtrar bugs si se especificó
    if args.bug:
        bug_numbers = [int(n.strip()) for n in args.bug.split(",")]
        bugs = [b for b in bugs if b["number"] in bug_numbers]
        print(f"   Filtrado a {len(bugs)} bugs específicos\n")

    if args.only_critical:
        bugs = [b for b in bugs if b["category"] == "crítico"]
        print(f"   Filtrado a {len(bugs)} bugs críticos\n")

    # Leer código de la app
    app_file = app_dir / "app.py"
    if app_file.exists():
        with open(app_file, "r", encoding="utf-8") as f:
            app_code = f.read()
        endpoints = extract_endpoints(app_code)
        print(f"📡 Encontrados {len(endpoints)} endpoints\n")
    else:
        endpoints = []
        print(f"⚠️  No se encontró app.py\n")

    # Generar Page Object
    if args.page_object or not args.dry_run:
        page_object = generate_page_object(args.app, endpoints)

        if args.dry_run:
            print("=" * 60)
            print("PAGE OBJECT:")
            print("=" * 60)
            print(page_object)
            print()
        else:
            output_dir = Path(args.output)
            output_dir.mkdir(parents=True, exist_ok=True)

            page_object_file = output_dir / f"{args.app}_page.py"
            with open(page_object_file, "w", encoding="utf-8") as f:
                f.write(page_object)
            print(f"✅ Page Object guardado: {page_object_file}")

    # Generar tests
    print(f"🧪 Generando {len(bugs)} tests...\n")

    for bug in bugs:
        test_code = generate_test_for_bug(bug, endpoints)

        if args.dry_run:
            print("=" * 60)
            print(f"TEST BUG #{bug['number']}: {bug['title']}")
            print("=" * 60)
            print(test_code)
            print()
        else:
            output_dir = Path(args.output)
            output_dir.mkdir(parents=True, exist_ok=True)

            test_file = output_dir / f"test_bug_{bug['number']:02d}.py"
            with open(test_file, "w", encoding="utf-8") as f:
                f.write(test_code)
            print(f"✅ Test guardado: {test_file}")

    if not args.dry_run:
        print(f"\n🎉 Generación completada!")
        print(f"   Tests guardados en: {args.output}")
        print(f"\nPróximos pasos:")
        print(f"   1. Revisa los tests generados")
        print(f"   2. Implementa la lógica específica en cada test")
        print(f"   3. Ejecuta: e2e run")


if __name__ == "__main__":
    main()
