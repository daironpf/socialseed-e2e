"""
Test de validación para socialseed-e2e.

Este script verifica que todas las componentes del framework
funcionan correctamente después de la instalación.
"""

import sys
from pathlib import Path


def test_imports():
    """Verificar que todos los imports principales funcionan."""
    print("\n1. Verificando imports...")

    try:
        from socialseed_e2e import (
            ApiConfigLoader,
            BasePage,
            ModuleLoader,
            ServiceConfig,
            TestContext,
            TestOrchestrator,
            __version__,
        )

        print(f"   ✓ Versión: {__version__}")
        print("   ✓ Todos los imports funcionan")
        return True
    except ImportError as e:
        print(f"   ✗ Error de import: {e}")
        return False


def test_core_classes():
    """Verificar que las clases principales se instancian correctamente."""
    print("\n2. Verificando clases core...")

    try:
        from socialseed_e2e.core import (
            ApiConfigLoader,
            BasePage,
            ModuleLoader,
            TestOrchestrator,
        )
        from socialseed_e2e.core.models import ServiceConfig

        # Verificar BasePage
        page = BasePage("http://localhost:8080")
        assert page.base_url == "http://localhost:8080"
        print("   ✓ BasePage instancia correctamente")

        # Verificar ModuleLoader
        loader = ModuleLoader()
        print("   ✓ ModuleLoader instancia correctamente")

        # Verificar TestOrchestrator
        orch = TestOrchestrator()
        print("   ✓ TestOrchestrator instancia correctamente")

        # Verificar ServiceConfig
        config = ServiceConfig(name="test", base_url="http://test.com")
        assert config.name == "test"
        print("   ✓ ServiceConfig funciona correctamente")

        return True
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False


def test_config_loader():
    """Verificar que ApiConfigLoader carga configuración por defecto."""
    print("\n3. Verificando ApiConfigLoader...")

    try:
        from socialseed_e2e.core.config_loader import ApiConfigLoader

        # Intentar cargar (debería crear config por defecto si no existe)
        try:
            config = ApiConfigLoader.load()
            print(f"   ✓ Config cargada: {config.project_name}")
        except FileNotFoundError:
            print("   ⚠ No hay config file (esperado en nueva instalación)")

        return True
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False


def test_version():
    """Verificar información de versión."""
    print("\n4. Verificando versión...")

    try:
        from socialseed_e2e import (
            __author__,
            __license__,
            __version__,
            __version_info__,
        )

        print(f"   ✓ Versión: {__version__}")
        print(f"   ✓ Versión info: {__version_info__}")
        print(f"   ✓ Autor: {__author__}")
        print(f"   ✓ Licencia: {__license__}")

        assert __version__ == "0.1.4"
        assert __version_info__ == (0, 1, 4)

        return True
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False


def main():
    """Ejecutar todos los tests."""
    print("=" * 60)
    print("TEST DE VALIDACIÓN: socialseed-e2e")
    print("=" * 60)

    tests = [
        test_imports,
        test_core_classes,
        test_config_loader,
        test_version,
    ]

    results = []
    for test in tests:
        try:
            results.append(test())
        except Exception as e:
            print(f"\n   ✗ Test falló con excepción: {e}")
            results.append(False)

    print("\n" + "=" * 60)
    passed = sum(results)
    total = len(results)

    if passed == total:
        print(f"✅ TODOS LOS TESTS PASARON ({passed}/{total})")
        print("=" * 60)
        print("\nEl framework está correctamente instalado y listo para usar!")
        print("\nPróximos pasos:")
        print("  1. Crea un proyecto: mkdir my-api-tests && cd my-api-tests")
        print("  2. Inicializa: e2e init")
        print("  3. Configura tu API en e2e.conf")
        print("  4. Crea tests: e2e new-test mytest --service myapi")
        print("  5. Ejecuta: e2e run")
        return 0
    else:
        print(f"❌ ALGUNOS TESTS FALLARON ({passed}/{total})")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
