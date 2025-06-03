import logging

from django import template

logger = logging.getLogger(__name__)

register = template.Library()

@register.simple_tag
def dash_grid(dash_name, dash_grid, **kwargs):
    """
    Returns the grid for a given dashboard name.
    """
    if dash_name in dash_grid:
        grid = dash_grid[dash_name]

        g = grid(**kwargs) if callable(grid) else grid
        g = str(g)
        return g
    else:
        logger.error(f"Dashboard '{dash_name}' not found in the provided grid.")
        return None
