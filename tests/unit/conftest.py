# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Unit test configuration."""
import ops.testing
import pytest

from charm import IdentityPlatformLoginUiOperatorCharm

ops.testing.SIMULATE_CAN_CONNECT = True


@pytest.fixture()
def harness():
    """Initialize harness with Charm."""
    harness = ops.testing.Harness(IdentityPlatformLoginUiOperatorCharm)
    harness.set_model_name("testing")
    harness.set_leader(True)
    harness.begin()
    return harness
