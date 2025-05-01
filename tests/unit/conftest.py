# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Unit test configuration."""

from unittest.mock import mock_open, patch

import ops.testing
import pytest
from ops.testing import Harness

from charm import IdentityPlatformLoginUiOperatorCharm


@pytest.fixture()
def harness() -> ops.testing.Harness:
    """Initialize harness with Charm."""
    harness = ops.testing.Harness(IdentityPlatformLoginUiOperatorCharm)
    harness.set_model_name("testing")
    harness.begin()
    harness.add_network("10.0.0.10")
    return harness


@pytest.fixture(autouse=True)
def mock_get_version(harness: Harness):
    harness.handle_exec(
        "login-ui", ["identity-platform-login-ui", "--version"], result="App Version: 1.42.0"
    )


@pytest.fixture(autouse=True)
def patch_file_open():
    with patch("builtins.open", new_callable=mock_open, read_data="data") as f:
        yield f
