# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

import pytest
from ops.testing import Harness

from charm import IdentityPlatformLoginUiOperatorCharm


@pytest.fixture()
def harness(mocked_kubernetes_service_patcher):
    harness = Harness(IdentityPlatformLoginUiOperatorCharm)
    harness.set_model_name("testing")
    harness.set_leader(True)
    harness.begin()
    return harness


@pytest.fixture()
def mocked_kubernetes_service_patcher(mocker):
    mocked_service_patcher = mocker.patch("charm.KubernetesServicePatch")
    mocked_service_patcher.return_value = lambda x, y: None
    yield mocked_service_patcher
