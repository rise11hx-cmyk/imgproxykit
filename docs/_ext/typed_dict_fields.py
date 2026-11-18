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

_TABLE_HEADER = (
    '.. list-table::',
    '   :header-rows: 1',
    '   :widths: 30 25 45',
    '',
    '   * - Field',
    '     - Value type',
    '     - Option class',
)


def _import_target(target: str) -> Any:
    """Import the class named by a dotted path."""
    module_name, _, class_name = target.rpartition('.')
    if not module_name or not class_name:
        raise ValueError(f'expected a dotted path to a class, got {target!r}')
    return getattr(import_module(module_name), class_name)


def _describe(annotation: Any) -> tuple[str, str]:
    """Render ``Annotated[value_type, Option]`` as a value type and a role."""
    args = get_args(annotation) if get_origin(annotation) is Annotated else ()
    value_type = args[0] if args else annotation
    module = getattr(value_type, '__module__', '')
    name = getattr(value_type, '__qualname__', None)
    if module in {'', 'builtins'} or name is None:
        value = f'``{getattr(value_type, "__name__", value_type)}``'
    else:
        value = f':class:`~{module}.{name}`'
    if len(args) < 2 or not isinstance(args[1], type):
        return value, ''
    return value, f':class:`~{args[1].__module__}.{args[1].__qualname__}`'


def field_rows(typed_dict: Any) -> list[tuple[str, str, str]]:
    """Return ``(field, value type, option class)`` for every field."""
    hints = get_type_hints(typed_dict, include_extras=True)
    return [
        (field, *_describe(annotation)) for field, annotation in hints.items()
    ]


def _table(rows: list[tuple[str, str, str]]) -> ViewList:
    """Turn the rows into a ``list-table`` body."""
    lines = ViewList()
    for header_line in _TABLE_HEADER:
        lines.append(header_line, source='')
    for field, value_type, option_role in rows:
        lines.append(f'   * - ``{field}``', source='')
        lines.append(f'     - {value_type}', source='')
        lines.append(f'     - {option_role}', source='')
    return lines


class TypedDictFields(SphinxDirective):
    """Render the fields of a ``TypedDict`` subclass as a list-table."""

    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = False
    has_content = False

    def run(self) -> list[nodes.Node]:
        """Render the table for the class named in the directive argument."""
        rows = field_rows(_import_target(self.arguments[0]))
        node = nodes.section()
        self.state.nested_parse(_table(rows), self.content_offset, node)
        return list(node.children)


def setup(app: Any) -> dict[str, Any]:
    """Register the directive."""
    app.add_directive('typed-dict-fields', TypedDictFields)
    return {'parallel_read_safe': True}
