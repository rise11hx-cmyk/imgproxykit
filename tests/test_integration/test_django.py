# Optional integration tests require their framework.
import pytest

try:
    import django  # noqa: F401  # pyright: ignore[reportUnusedImport]
except ImportError:  # pragma: no cover
    pytest.skip(reason='django is not installed', allow_module_level=True)

from http import HTTPStatus

from django.conf import settings
from django.test import Client, override_settings
from pytest_django.asserts import assertContains

from imgproxykit import Transform
from imgproxykit.integrations.django.client import get_client
from imgproxykit.options import Preset


def test_image_page(client: Client) -> None:
    """Render image URLs using configured transforms and variants."""
    response = client.get(
        '/images/',
        {'source': 'https://example.com/photo.jpg'},
    )

    assert response.status_code == HTTPStatus.OK
    assertContains(response, '/width:640/format:webp/')
    assertContains(response, '/width:320/format:webp/')
    assertContains(response, '/width:1280/format:webp/')


def test_only_presets_setting_reaches_the_client() -> None:
    """Pass IMGPROXYKIT's client option through, for a presets-only server."""
    config = settings.IMGPROXYKIT  # type: ignore[attr-defined]
    client_config = {**config['client'], 'only_presets': True}

    with override_settings(IMGPROXYKIT={**config, 'client': client_config}):  # type: ignore[attr-defined]
        url = get_client().url(
            'https://example.com/photo.jpg',
            transform=Transform(Preset('thumbnail', 'watermarked')),
        )

    assert '/thumbnail:watermarked/' in url
    assert 'preset:' not in url
