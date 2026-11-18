from dataclasses import dataclass, make_dataclass
from re import escape
from typing import Annotated, Any, Final

import pytest

from imgproxykit import Transform
from imgproxykit.variants import DataclassVariantsResolver

_SMALL: Final = Transform(width=320)
_LARGE: Final = Transform(width=1280)
_Thumbnail = Annotated[str, _SMALL]

type _TypeStatementThumbnail = Annotated[str, _SMALL]
type _NestedTypeStatementThumbnail = _TypeStatementThumbnail
type _InvalidTypeStatementThumbnail = Annotated[int, _SMALL]


@dataclass
class _AliasVariants:
    """Reference a module-level alias through a string annotation."""

    small: '_Thumbnail'


@dataclass
class _TypeStatementVariants:
    """Declare fields with PEP 695 ``type`` aliases."""

    small: _TypeStatementThumbnail
    large: _NestedTypeStatementThumbnail


@dataclass
class _InvalidTypeStatementVariants:
    """Declare an invalid field through a PEP 695 ``type`` alias."""

    small: _InvalidTypeStatementThumbnail


def test_alias_and_forward_reference() -> None:
    """Resolve a string annotation referring to a module-level type alias."""
    assert DataclassVariantsResolver(model=_AliasVariants)() == {
        'small': _SMALL
    }


def test_type_statement_alias() -> None:
    """Resolve PEP 695 ``type`` aliases, including an alias of an alias."""
    assert DataclassVariantsResolver(model=_TypeStatementVariants)() == {
        'small': _SMALL,
        'large': _SMALL,
    }


def test_invalid_type_statement_alias() -> None:
    """Validate the resolved type rather than accepting any alias."""
    with pytest.raises(
        TypeError,
        match=escape('must be annotated with `Annotated[str, Transform(...)]`'),
    ) as exc_info:
        DataclassVariantsResolver(model=_InvalidTypeStatementVariants)()

    assert "Field 'small'" in str(exc_info.value)
    assert 'Annotated[int' in str(exc_info.value)


@pytest.mark.parametrize(
    ('annotation', 'message'),
    [
        (str, 'must be annotated with `Annotated[str, Transform(...)]`'),
        (
            Annotated[int, _SMALL],
            'must be annotated with `Annotated[str, Transform(...)]`',
        ),
        (Annotated[str, 'description'], 'got 0'),
        (Annotated[str, _SMALL, _LARGE], 'got 2'),
        (Annotated[str, _SMALL, _SMALL], 'got 2'),
    ],
)
def test_invalid_annotation(*, annotation: Any, message: str) -> None:
    """Reject invalid result types and missing or repeated transformations."""
    model = make_dataclass('InvalidVariants', [('small', annotation)])

    with pytest.raises(TypeError, match=escape(message)) as exc_info:
        DataclassVariantsResolver(model=model)()  # ty: ignore[invalid-argument-type]

    assert "Field 'small'" in str(exc_info.value)
    assert 'InvalidVariants' in str(exc_info.value)


def test_unresolved_forward_reference() -> None:
    """Propagate unresolved application annotations without hiding the name."""
    model = make_dataclass(
        'UnresolvedVariants',
        [('small', 'MissingThumbnail')],
    )

    with pytest.raises(NameError, match='MissingThumbnail'):
        DataclassVariantsResolver(model=model)()  # ty: ignore[invalid-argument-type]
