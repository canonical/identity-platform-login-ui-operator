# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.
#
# Learn more about testing at: https://juju.is/docs/sdk/testing

"""Test functions for unit testing Identity Platform Login UI Operator."""
import json
from typing import Tuple

from ops.model import ActiveStatus, WaitingStatus
from ops.testing import Harness
from pytest_mock import MockerFixture

CONTAINER_NAME = "login-ui"
TEST_PORT = "8080"


def setup_ingress_relation(harness: Harness) -> Tuple[int, str]:
    """Set up ingress relation."""
    harness.set_leader(True)
    relation_id = harness.add_relation("ingress", "traefik")
    harness.add_relation_unit(relation_id, "traefik/0")
    url = f"http://ingress:80/{harness.model.name}-identity-platform-login-ui"
    harness.update_relation_data(
        relation_id,
        "traefik",
        {"ingress": json.dumps({"url": url})},
    )
    return relation_id, url


def setup_kratos_relation(harness: Harness) -> int:
    relation_id = harness.add_relation("kratos-endpoint-info", "kratos")
    harness.add_relation_unit(relation_id, "kratos/0")
    harness.update_relation_data(
        relation_id,
        "kratos",
        {
            "admin_endpoint": f"http://kratos-admin-url:80/{harness.model.name}-kratos",
            "public_endpoint": f"http://kratos-public-url:80/{harness.model.name}-kratos",
        },
    )
    return relation_id


def setup_hydra_relation(harness: Harness) -> int:
    relation_id = harness.add_relation("endpoint-info", "hydra")
    harness.add_relation_unit(relation_id, "hydra/0")
    harness.update_relation_data(
        relation_id,
        "hydra",
        {
            "admin_endpoint": f"http://hydra-admin-url:80/{harness.model.name}-hydra",
            "public_endpoint": f"http://hydra-public-url:80/{harness.model.name}-hydra",
        },
    )
    return relation_id


def test_not_leader(harness: Harness) -> None:
    """Test with unit not being leader."""
    harness.set_leader(False)

    harness.charm.on.login_ui_pebble_ready.emit(CONTAINER_NAME)

    assert (
        "status_set",
        "waiting",
        "Waiting to connect to Login_UI container",
        {"is_app": False},
    ) in harness._get_backend_calls()


def test_install_can_connect(harness: Harness) -> None:
    """Test installation with connection."""
    harness.set_leader(True)
    harness.set_can_connect(CONTAINER_NAME, True)
    harness.charm.on.login_ui_pebble_ready.emit(CONTAINER_NAME)

    assert harness.charm.unit.status == ActiveStatus()


def test_install_can_not_connect(harness: Harness) -> None:
    """Test installation with connection."""
    harness.set_leader(True)
    harness.set_can_connect(CONTAINER_NAME, False)
    harness.charm.on.login_ui_pebble_ready.emit(CONTAINER_NAME)

    assert harness.charm.unit.status == WaitingStatus("Waiting to connect to Login_UI container")


def test_layer_updated_without_any_endpoint_info(harness: Harness) -> None:
    """Test Pebble Layer after updates."""
    harness.set_leader(True)
    harness.set_can_connect(CONTAINER_NAME, True)
    harness.charm.on.login_ui_pebble_ready.emit(CONTAINER_NAME)

    expected_layer = {
        "summary": "login_ui layer",
        "description": "pebble config layer for identity platform login ui",
        "services": {
            CONTAINER_NAME: {
                "override": "replace",
                "summary": "identity platform login ui",
                "command": "identity_platform_login_ui",
                "startup": "enabled",
                "environment": {
                    "HYDRA_ADMIN_URL": "",
                    "KRATOS_PUBLIC_URL": "",
                    "PORT": TEST_PORT,
                    "BASE_URL": None,
                },
            }
        },
        "checks": {
            "login-ui-alive": {
                "override": "replace",
                "http": {"url": f"http://localhost:{TEST_PORT}/health/alive"},
            },
        },
    }

    assert harness.charm._login_ui_layer.to_dict() == expected_layer


def test_layer_updated_with_kratos_endpoint_info(harness: Harness) -> None:
    """Test Pebble Layer when relation data is in place."""
    harness.set_leader(True)
    harness.set_can_connect(CONTAINER_NAME, True)
    harness.charm.on.login_ui_pebble_ready.emit(CONTAINER_NAME)
    kratos_relation_id = setup_kratos_relation(harness)

    expected_layer = {
        "summary": "login_ui layer",
        "description": "pebble config layer for identity platform login ui",
        "services": {
            CONTAINER_NAME: {
                "override": "replace",
                "summary": "identity platform login ui",
                "command": "identity_platform_login_ui",
                "startup": "enabled",
                "environment": {
                    "HYDRA_ADMIN_URL": "",
                    "KRATOS_PUBLIC_URL": harness.get_relation_data(kratos_relation_id, "kratos")[
                        "public_endpoint"
                    ],
                    "PORT": TEST_PORT,
                    "BASE_URL": None,
                },
            }
        },
        "checks": {
            "login-ui-alive": {
                "override": "replace",
                "http": {"url": f"http://localhost:{TEST_PORT}/health/alive"},
            },
        },
    }

    assert harness.charm._login_ui_layer.to_dict() == expected_layer


def test_layer_updated_with_hydra_endpoint_info(harness: Harness) -> None:
    """Test Pebble Layer when relation data is in place."""
    harness.set_leader(True)
    harness.set_can_connect(CONTAINER_NAME, True)
    harness.charm.on.login_ui_pebble_ready.emit(CONTAINER_NAME)
    hydra_relation_id = setup_hydra_relation(harness)

    expected_layer = {
        "summary": "login_ui layer",
        "description": "pebble config layer for identity platform login ui",
        "services": {
            CONTAINER_NAME: {
                "override": "replace",
                "summary": "identity platform login ui",
                "command": "identity_platform_login_ui",
                "startup": "enabled",
                "environment": {
                    "HYDRA_ADMIN_URL": harness.get_relation_data(hydra_relation_id, "hydra")[
                        "admin_endpoint"
                    ],
                    "KRATOS_PUBLIC_URL": "",
                    "PORT": TEST_PORT,
                    "BASE_URL": None,
                },
            }
        },
        "checks": {
            "login-ui-alive": {
                "override": "replace",
                "http": {"url": f"http://localhost:{TEST_PORT}/health/alive"},
            },
        },
    }

    assert harness.charm._login_ui_layer.to_dict() == expected_layer


def test_layer_updated_with_endpoint_info(harness: Harness) -> None:
    """Test Pebble Layer when relation data is in place."""
    harness.set_leader(True)
    harness.set_can_connect(CONTAINER_NAME, True)
    harness.charm.on.login_ui_pebble_ready.emit(CONTAINER_NAME)
    hydra_relation_id = setup_hydra_relation(harness)
    kratos_relation_id = setup_kratos_relation(harness)

    expected_layer = {
        "summary": "login_ui layer",
        "description": "pebble config layer for identity platform login ui",
        "services": {
            CONTAINER_NAME: {
                "override": "replace",
                "summary": "identity platform login ui",
                "command": "identity_platform_login_ui",
                "startup": "enabled",
                "environment": {
                    "HYDRA_ADMIN_URL": harness.get_relation_data(hydra_relation_id, "hydra")[
                        "admin_endpoint"
                    ],
                    "KRATOS_PUBLIC_URL": harness.get_relation_data(kratos_relation_id, "kratos")[
                        "public_endpoint"
                    ],
                    "PORT": TEST_PORT,
                    "BASE_URL": None,
                },
            }
        },
        "checks": {
            "login-ui-alive": {
                "override": "replace",
                "http": {"url": f"http://localhost:{TEST_PORT}/health/alive"},
            },
        },
    }

    assert harness.charm._login_ui_layer.to_dict() == expected_layer


def test_layer_updated_with_ingress_ready(harness: Harness) -> None:
    harness.set_leader(True)
    harness.set_can_connect(CONTAINER_NAME, True)
    harness.charm.on.login_ui_pebble_ready.emit(CONTAINER_NAME)
    hydra_relation_id = setup_hydra_relation(harness)
    kratos_relation_id = setup_kratos_relation(harness)
    _, url = setup_ingress_relation(harness)

    expected_layer = {
        "summary": "login_ui layer",
        "description": "pebble config layer for identity platform login ui",
        "services": {
            CONTAINER_NAME: {
                "override": "replace",
                "summary": "identity platform login ui",
                "command": "identity_platform_login_ui",
                "startup": "enabled",
                "environment": {
                    "HYDRA_ADMIN_URL": harness.get_relation_data(hydra_relation_id, "hydra")[
                        "admin_endpoint"
                    ],
                    "KRATOS_PUBLIC_URL": harness.get_relation_data(kratos_relation_id, "kratos")[
                        "public_endpoint"
                    ],
                    "PORT": TEST_PORT,
                    "BASE_URL": url.replace("http", "https").replace(":80", ""),
                },
            }
        },
    }

    assert harness.charm._login_ui_layer.to_dict() == expected_layer


def test_ui_endpoint_info(harness: Harness, mocker: MockerFixture) -> None:
    mocked_service_patcher = mocker.patch(
        "charm.LoginUIEndpointsProvider.send_endpoints_relation_data"
    )
    harness.set_leader(True)
    harness.set_can_connect(CONTAINER_NAME, True)
    _, url = setup_ingress_relation(harness)
    harness.charm.on.login_ui_pebble_ready.emit(CONTAINER_NAME)

    relation_id = harness.add_relation("ui-endpoint-info", "hydra")
    harness.add_relation_unit(relation_id, "hydra/0")

    mocked_service_patcher.assert_called_with(url.replace("http", "https").replace(":80", ""))
