# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

import pytest
from ops.testing import Harness

from charm import IdentityPlatformLoginUiOperatorCharm


@pytest.fixture()
def harness():
    harness = Harness(IdentityPlatformLoginUiOperatorCharm)
    harness.set_model_name("testing")
    harness.set_leader(True)
    harness.begin()
    return harness
