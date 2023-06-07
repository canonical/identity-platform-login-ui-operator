# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Unit test configuration."""
from unittest.mock import MagicMock

import ops.testing
import pytest
from pytest_mock import MockerFixture

from charm import IdentityPlatformLoginUiOperatorCharm


@pytest.fixture()
def harness(mocked_kubernetes_service_patcher: MagicMock) -> ops.testing.Harness:
    """Initialize harness with Charm."""
    harness = ops.testing.Harness(IdentityPlatformLoginUiOperatorCharm)
    harness.set_model_name("testing")
    harness.begin()
    return harness


@pytest.fixture()
def mocked_kubernetes_service_patcher(mocker: MockerFixture) -> MagicMock:
    mocked_service_patcher = mocker.patch("charm.KubernetesServicePatch")
    mocked_service_patcher.return_value = lambda x, y: None
    return mocked_service_patcher
