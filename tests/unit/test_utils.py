# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

import pytest

from utils import is_true, normalise_url


def test_normalise_url_with_subpatch() -> None:
    url = "http://ingress:80/path/subpath"
    expected_url = "https://ingress/path/subpath"

    res_url = normalise_url(url)

    assert res_url == expected_url


def test_normalise_url_without_subpatch() -> None:
    url = "http://ingress:80/"
    expected_url = "https://ingress/"

    res_url = normalise_url(url)

    assert res_url == expected_url


def test_normalise_url_without_trailing_slash() -> None:
    url = "http://ingress:80"
    expected_url = "https://ingress"

    res_url = normalise_url(url)

    assert res_url == expected_url


@pytest.mark.parametrize("value, expected", [("True", True), ("true", True), (True, True)])
def test_is_true(value: object, expected: bool) -> None:
    assert is_true(value) is expected


@pytest.mark.parametrize("value", ["False", "false", False, None, ""])
def test_is_not_true(value: object) -> None:
    assert is_true(value) is False
