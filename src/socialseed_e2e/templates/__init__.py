"""Templates for code scaffolding.

This package contains template files used by the TemplateEngine
to generate code files and project scaffolding.

Available Templates:
    - e2e.conf.template: Default configuration file
    - service_page.py.template: Service page class
    - test_module.py.template: Test module structure
    - data_schema.py.template: Data transfer objects
    - config.py.template: Service configuration loader

Usage:
    Templates are loaded and rendered by the TemplateEngine class
    in socialseed_e2e.utils.template_engine.

Example:
    from socialseed_e2e.utils import TemplateEngine
    
    engine = TemplateEngine()
    content = engine.render('service_page.py', {
        'service_name': 'users-api',
        'class_name': 'UsersApi'
    })
"""

from pathlib import Path

# Get the templates directory
TEMPLATES_DIR = Path(__file__).parent

__all__ = ["TEMPLATES_DIR"]
