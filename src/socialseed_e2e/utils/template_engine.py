"""Template engine for code scaffolding.

This module provides a template engine for generating code files
and project scaffolding using Python's string.Template.
"""

import re
from pathlib import Path
from string import Template
from typing import Dict, Optional, Union


class TemplateEngine:
    """Template engine for code generation and scaffolding.
    
    This class provides methods to load and render templates with
    variable substitution. Templates are stored as files and can
    be rendered with custom variables.
    
    Attributes:
        template_dir: Directory containing template files
        
    Example:
        >>> engine = TemplateEngine()
        >>> result = engine.render('service_page.py', {
        ...     'service_name': 'users-api',
        ...     'class_name': 'UsersApi'
        ... })
    """
    
    def __init__(self, template_dir: Optional[Union[str, Path]] = None):
        """Initialize the template engine.
        
        Args:
            template_dir: Directory containing template files.
                         If None, uses the default templates directory.
        """
        if template_dir is None:
            # Use the templates directory in the package
            self.template_dir = Path(__file__).parent.parent / "templates"
        else:
            self.template_dir = Path(template_dir)
    
    def load_template(self, template_name: str) -> Template:
        """Load a template from file.
        
        Args:
            template_name: Name of the template file (with or without .template extension)
            
        Returns:
            Template: A string.Template instance
            
        Raises:
            FileNotFoundError: If template file doesn't exist
        """
        # Ensure .template extension
        if not template_name.endswith('.template'):
            template_name = f"{template_name}.template"
        
        template_path = self.template_dir / template_name
        
        if not template_path.exists():
            raise FileNotFoundError(
                f"Template not found: {template_path}\n"
                f"Available templates: {self.list_templates()}"
            )
        
        template_content = template_path.read_text(encoding='utf-8')
        return Template(template_content)
    
    def render(self, template_name: str, variables: Optional[Dict[str, str]] = None) -> str:
        """Render a template with variable substitution.
        
        Args:
            template_name: Name of the template file
            variables: Dictionary of variables for substitution
            
        Returns:
            str: Rendered template content
            
        Raises:
            FileNotFoundError: If template file doesn't exist
        """
        if variables is None:
            variables = {}
        
        template = self.load_template(template_name)
        return template.safe_substitute(variables)
    
    def render_to_file(
        self, 
        template_name: str, 
        variables: Optional[Dict[str, str]], 
        output_path: Union[str, Path],
        overwrite: bool = False
    ) -> Path:
        """Render a template and write to file.
        
        Args:
            template_name: Name of the template file
            variables: Dictionary of variables for substitution
            output_path: Path where to write the rendered content
            overwrite: If True, overwrite existing file
            
        Returns:
            Path: Path to the written file
            
        Raises:
            FileNotFoundError: If template file doesn't exist
            FileExistsError: If output file exists and overwrite=False
        """
        output_path = Path(output_path)
        
        if output_path.exists() and not overwrite:
            raise FileExistsError(
                f"File already exists: {output_path}. "
                f"Use overwrite=True to overwrite."
            )
        
        # Ensure parent directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        content = self.render(template_name, variables)
        output_path.write_text(content, encoding='utf-8')
        
        return output_path
    
    def list_templates(self) -> list:
        """List all available templates.
        
        Returns:
            list: List of template file names
        """
        if not self.template_dir.exists():
            return []
        
        return [
            f.name for f in self.template_dir.iterdir() 
            if f.is_file() and f.suffix == '.template'
        ]
    
    def get_template_variables(self, template_name: str) -> list:
        """Extract variable names from a template.
        
        Args:
            template_name: Name of the template file
            
        Returns:
            list: List of variable names used in the template
        """
        template = self.load_template(template_name)
        
        # Pattern to match ${var} or $var
        pattern = r'\$\{([^}]+)\}|\$([a-zA-Z_][a-zA-Z0-9_]*)'
        matches = re.findall(pattern, template.template)
        
        # Extract variable names from matches
        variables = []
        for match in matches:
            # match is a tuple (braced, unbraced)
            var = match[0] if match[0] else match[1]
            if var and var not in variables:
                variables.append(var)
        
        return variables
    
    def validate_variables(
        self, 
        template_name: str, 
        variables: Dict[str, str]
    ) -> tuple:
        """Validate that all required variables are provided.
        
        Args:
            template_name: Name of the template file
            variables: Dictionary of variables to validate
            
        Returns:
            tuple: (missing_vars, extra_vars)
                - missing_vars: List of variables in template but not in variables dict
                - extra_vars: List of variables in variables dict but not in template
        """
        template_vars = set(self.get_template_variables(template_name))
        provided_vars = set(variables.keys())
        
        missing = list(template_vars - provided_vars)
        extra = list(provided_vars - template_vars)
        
        return missing, extra


def to_class_name(name: str) -> str:
    """Convert a service name to a class name.
    
    Converts names like 'users-api' or 'users_api' to 'UsersApi'.
    
    Args:
        name: Service name (e.g., 'users-api', 'users_api')
        
    Returns:
        str: Class name (e.g., 'UsersApi')
        
    Example:
        >>> to_class_name('users-api')
        'UsersApi'
        >>> to_class_name('my_service')
        'MyService'
    """
    # Replace hyphens and underscores with spaces, title case, then remove spaces
    return name.replace('-', ' ').replace('_', ' ').title().replace(' ', '')


def to_snake_case(name: str) -> str:
    """Convert a service name to snake_case.
    
    Converts names like 'users-api' to 'users_api'.
    
    Args:
        name: Service name (e.g., 'users-api')
        
    Returns:
        str: Snake case name (e.g., 'users_api')
        
    Example:
        >>> to_snake_case('users-api')
        'users_api'
        >>> to_snake_case('MyService')
        'my_service'
    """
    # Replace hyphens with underscores and convert to lowercase
    return name.replace('-', '_').lower()


def to_camel_case(name: str) -> str:
    """Convert a service name to camelCase.
    
    Converts names like 'users-api' to 'usersApi'.
    
    Args:
        name: Service name (e.g., 'users-api')
        
    Returns:
        str: Camel case name (e.g., 'usersApi')
        
    Example:
        >>> to_camel_case('users-api')
        'usersApi'
        >>> to_camel_case('my_service')
        'myService'
    """
    class_name = to_class_name(name)
    return class_name[0].lower() + class_name[1:]
