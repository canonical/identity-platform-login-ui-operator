# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Unit test configuration."""
from typing import Generator
from unittest.mock import MagicMock

import ops.testing
import pytest
from ops.pebble import ExecError
from pytest_mock import MockerFixture

from charm import IdentityPlatformLoginUiOperatorCharm

ops.testing.SIMULATE_CAN_CONNECT = True


@pytest.fixture()
def harness(mocked_kubernetes_service_patcher: MagicMock) -> ops.testing.Harness:
    harness = ops.testing.Harness(IdentityPlatformLoginUiOperatorCharm)
    harness.set_model_name("login-ui-model")
    harness.set_can_connect("login-ui", True)
    harness.begin()
    return harness


@pytest.fixture()
def mocked_kubernetes_service_patcher(mocker: MockerFixture) -> Generator:
    mocked_service_patcher = mocker.patch("charm.KubernetesServicePatch")
    mocked_service_patcher.return_value = lambda x, y: None
    yield mocked_service_patcher


@pytest.fixture()
def mocked_fqdn(mocker: MockerFixture) -> Generator:
    mocked_fqdn = mocker.patch("socket.getfqdn")
    mocked_fqdn.return_value = "kratos"
    return mocked_fqdn


@pytest.fixture()
def mocked_container(harness: ops.testing.Harness, mocker: MockerFixture) -> Generator:
    container = harness.model.unit.get_container("kratos")
    container.restart = mocker.MagicMock()
    return container


@pytest.fixture()
def mocked_pebble_exec(mocker: MockerFixture) -> Generator:
    mocked_pebble_exec = mocker.patch("ops.model.Container.exec")
    yield mocked_pebble_exec


@pytest.fixture()
def mocked_pebble_exec_success(mocker: MockerFixture, mocked_pebble_exec: MagicMock) -> Generator:
    mocked_process = mocker.patch("ops.pebble.ExecProcess")
    mocked_process.wait_output.return_value = ("Success", None)
    mocked_pebble_exec.return_value = mocked_process
    yield mocked_pebble_exec


@pytest.fixture()
def mocked_pebble_exec_failed(mocked_pebble_exec: MagicMock) -> Generator:
    mocked_pebble_exec.side_effect = ExecError(
        exit_code=400, stderr="Failed to execute", stdout="Failed", command="test command"
    )
    yield
