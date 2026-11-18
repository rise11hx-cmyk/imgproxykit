"""Render a ``TypedDict``'s fields as a reference table.

``autoclass`` documents a ``TypedDict``'s docstring but not its fields: the
keys are annotations, not attributes, so a page that only uses ``autoclass``
shows the prose and hides the contract. This directive reads the annotations
at build time, so the table cannot drift away from the class it documents.

Usage::

    .. typed-dict-fields:: imgproxykit.transform.KeywordOptions
"""

from __future__ import annotations

from importlib import import_module
from typing import Annotated, Any, get_args, get_origin, get_type_hints

from docutils import nodes
from docutils.statemachine import ViewList
from sphinx.util.docutils import SphinxDirective


def _render_type(annotation: Any) -> str:
    """Render a value type as reStructuredText, with a link for real classes."""
    if isinstance(annotation, type):
        module = annotation.__module__ or ''
        if module in {'', 'builtins'}:
            return f'``{annotation.__name__}``'
        return f':class:`~{module}.{annotation.__qualname__}`'
    return f'``{annotation}``'


def _import_target(target: str) -> Any:
    module_name, _, class_name = target.rpartition('.')
    if not module_name or not class_name:
        raise ValueError(f'expected a dotted path to a class, got {target!r}')
    return getattr(import_module(module_name), class_name)


def _unwrap(annotation: Any) -> tuple[Any, type[Any] | None]:
    """Split ``Annotated[value_type, SomeOption]`` into its two parts."""
    if get_origin(annotation) is not Annotated:
        return annotation, None
    args = get_args(annotation)
    option = args[1] if len(args) > 1 else None
    return args[0], option if isinstance(option, type) else None


def field_rows(typed_dict: Any) -> list[tuple[str, str, str]]:
    """Return ``(field, value type, option class)`` for every field."""
    hints = get_type_hints(typed_dict, include_extras=True)
    rows = []
    for field, annotation in hints.items():
        value_type, option = _unwrap(annotation)
        option_name = (
            f':class:`~{option.__module__}.{option.__qualname__}`'
            if option is not None
            else ''
        )
        rows.append((field, _render_type(value_type), option_name))
    return rows


class TypedDictFields(SphinxDirective):
    """Render the fields of a ``TypedDict`` subclass as a list-table."""

    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = False
    has_content = False

    def run(self) -> list[nodes.Node]:
        """Render the table for the class named in the directive argument."""
        typed_dict = _import_target(self.arguments[0])
        rows = field_rows(typed_dict)
        lines = ViewList()
        lines.append('.. list-table::', source='')
        lines.append('   :header-rows: 1', source='')
        lines.append('   :widths: 30 25 45', source='')
        lines.append('', source='')
        lines.append('   * - Field', source='')
        lines.append('     - Value type', source='')
        lines.append('     - Option class', source='')
        for field, value_type, option_name in rows:
            lines.append(f'   * - ``{field}``', source='')
            lines.append(f'     - {value_type}', source='')
            lines.append(f'     - {option_name}', source='')
        node = nodes.section()
        self.state.nested_parse(lines, self.content_offset, node)
        return list(node.children)


def setup(app: Any) -> dict[str, Any]:
    """Register the directive."""
    app.add_directive('typed-dict-fields', TypedDictFields)
    return {'parallel_read_safe': True}
