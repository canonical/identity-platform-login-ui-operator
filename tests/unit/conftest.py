# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Unit test configuration."""
import ops.testing
import pytest

from charm import IdentityPlatformLoginUiOperatorCharm

ops.testing.SIMULATE_CAN_CONNECT = True


@pytest.fixture()
def harness(mocked_kubernetes_service_patcher):
    """Initialize harness with Charm."""
    harness = ops.testing.Harness(IdentityPlatformLoginUiOperatorCharm)
    harness.set_model_name("testing")
    harness.begin()
    return harness


@pytest.fixture()
def mocked_kubernetes_service_patcher(mocker):
    mocked_service_patcher = mocker.patch("charm.KubernetesServicePatch")
    mocked_service_patcher.return_value = lambda x, y: None
    yield mocked_service_patcher
