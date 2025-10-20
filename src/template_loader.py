"""
Template loading utility for agents
"""
from pathlib import Path
from typing import Dict


def load_template(template_name: str) -> str:
    """
    Load a template file from the templates directory

    :param template_name: Name of the template file (e.g., 'fastapi_main.py.template')
    :return: Template content as string
    :raises FileNotFoundError: If template file doesn't exist
    :raises IOError: If template file cannot be read
    """
    # Find project root by looking for templates directory
    current_file = Path(__file__)
    project_root = current_file.parent.parent  # src -> project root
    template_path = project_root / "templates" / template_name

    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")

    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()
    except (IOError, OSError) as e:
        raise IOError(f"Failed to read template {template_name}: {str(e)}")


def render_template(template_content: str, variables: Dict[str, str]) -> str:
    """
    Render a template by replacing placeholders with values

    :param template_content: Template string with {placeholder} markers
    :param variables: Dictionary mapping placeholder names to values
    :return: Rendered template string
    """
    result = template_content
    for key, value in variables.items():
        placeholder = "{" + key + "}"
        result = result.replace(placeholder, str(value))
    return result


def load_and_render_template(template_name: str, variables: Dict[str, str]) -> str:
    """
    Load and render a template in one step

    :param template_name: Name of the template file
    :param variables: Dictionary mapping placeholder names to values
    :return: Rendered template string
    """
    template_content = load_template(template_name)
    return render_template(template_content, variables)
