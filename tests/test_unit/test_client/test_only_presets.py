from typing import Final

import pytest
from inline_snapshot import snapshot

from imgproxykit import Client, Transform
from imgproxykit.options import Preset, Quality
from imgproxykit.signing import UrlSigner
from tests.fixtures.credentials import Credentials

_SOURCE: Final = 'https://example.com/photo.jpg'
_SOURCE_PATH: Final = 'aHR0cHM6Ly9leGFtcGxlLmNvbS9waG90by5qcGc'


def test_one_preset_is_one_name_segment() -> None:
    """Write a preset name where the server expects it, without its option."""
    client = Client('https://example.com', only_presets=True)

    assert client.url(
        _SOURCE,
        transform=Transform(Preset('thumbnail')),
    ) == snapshot(
        'https://example.com/unsafe/thumbnail/aHR0cHM6Ly9leGFtcGxlLmNvbS9waG90by5qcGc',
    )


def test_several_presets_share_one_segment() -> None:
    """Keep the order of the names when each comes from its own option."""
    client = Client('https://example.com', only_presets=True)
    transform = Transform(Preset('thumbnail'), Preset('watermarked'))

    assert client.url(_SOURCE, transform=transform) == snapshot(
        'https://example.com/unsafe/thumbnail:watermarked/'
        'aHR0cHM6Ly9leGFtcGxlLmNvbS9waG90by5qcGc',
    )


def test_a_custom_separator_separates_the_names() -> None:
    """Use the configured argument separator, which the server must match."""
    client = Client(
        'https://example.com',
        only_presets=True,
        argument_separator=',',
    )

    assert client.url(
        _SOURCE,
        transform=Transform(Preset('thumbnail', 'watermarked')),
    ) == snapshot(
        'https://example.com/unsafe/thumbnail,watermarked/'
        'aHR0cHM6Ly9leGFtcGxlLmNvbS9waG90by5qcGc',
    )


def test_signing_covers_the_presets_only_path(credentials: Credentials) -> None:
    """Sign the path as built, presets segment and source alike."""
    client = Client('https://example.com', only_presets=True, **credentials)
    signer = UrlSigner(
        key=credentials['key'],
        salt=credentials['salt'],
        signature_size=32,
        unsigned_marker='unsafe',
    )
    path = f'/thumbnail:watermarked/{_SOURCE_PATH}'

    assert (
        client.url(
            _SOURCE,
            transform=Transform(Preset('thumbnail'), Preset('watermarked')),
        )
        == f'https://example.com/{signer(path)}{path}'
    )


def test_other_option_is_rejected() -> None:
    """Refuse a transform the server would apply besides the presets."""
    client = Client('https://example.com', only_presets=True)

    with pytest.raises(
        TypeError,
        match=(
            'only_presets accepts Preset options only;'
            ' the transform also has Quality'
        ),
    ):
        client.url(
            _SOURCE, transform=Transform(Preset('thumbnail'), Quality(85))
        )


def test_default_urls_keep_the_preset_prefix() -> None:
    """Leave standard mode alone, where the option name precedes the names."""
    client = Client('https://example.com')

    assert client.url(
        _SOURCE,
        transform=Transform(Preset('thumbnail')),
    ) == snapshot(
        'https://example.com/unsafe/preset:thumbnail/'
        'aHR0cHM6Ly9leGFtcGxlLmNvbS9waG90by5qcGc',
    )
