# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.
#
# Learn more about testing at: https://juju.is/docs/sdk/testing

"""Test functions for unit testing Identity Platform Login UI Operator."""
import json

from ops.model import ActiveStatus, WaitingStatus

CONTAINER_NAME = "login_ui"
TEST_PORT = "55555"
TEST_HYDRA_URL = "http://hydra:port"
TEST_KRATOS_URL = "http://kratos:port"


def setup_ingress_relation(harness):
    """Set up ingress relation."""
    relation_id = harness.add_relation("ingress", "traefik")
    harness.add_relation_unit(relation_id, "traefik/0")
    harness.update_relation_data(
        relation_id,
        "traefik",
        {
            "ingress": json.dumps(
                {
                    "url": f"http://ingress:80/{harness.model.name}-identity-platform-login-ui"
                }
            )
        },
    )
    return relation_id


def test_not_leader(harness):
    """Test with unit not being leader."""
    harness.set_leader(False)

    harness.charm.on.login_ui_pebble_ready.emit(CONTAINER_NAME)

    assert (
        "status_set",
        "waiting",
        "Waiting to connect to Login_UI container",
        {"is_app": False},
    ) in harness._get_backend_calls()


def test_install_can_connect(harness):
    """Test installation with connection."""
    harness.set_can_connect(CONTAINER_NAME, True)
    harness.charm.on.login_ui_pebble_ready.emit(CONTAINER_NAME)

    assert harness.charm.unit.status == ActiveStatus()


def test_install_can_not_connect(harness):
    """Test installation with connection."""
    harness.set_can_connect(CONTAINER_NAME, False)
    harness.charm.on.login_ui_pebble_ready.emit(CONTAINER_NAME)

    assert harness.charm.unit.status == WaitingStatus(
        "Waiting to connect to Login_UI container"
    )  # noqa:E501


def test_layer_updated(harness) -> None:
    """Test Pebble Layers after updates."""
    harness.set_can_connect(CONTAINER_NAME, True)
    harness.charm.on.login_ui_pebble_ready.emit(CONTAINER_NAME)

    harness.update_config({"hydra_url": TEST_HYDRA_URL})
    harness.update_config({"kratos_url": TEST_KRATOS_URL})
    harness.update_config({"port": TEST_PORT})

    expected_layer = {
        "summary": "login_ui layer",
        "description": "pebble config layer for identity platform login ui",
        "services": {
            CONTAINER_NAME: {
                "override": "replace",
                "summary": "identity platform login ui",
                "command": "/id/identity_platform_login_ui",
                "startup": "enabled",
                "environment": {
                    "HYDRA_ADMIN_URL": TEST_HYDRA_URL,
                    "KRATOS_PUBLIC_URL": TEST_KRATOS_URL,
                    "PORT": TEST_PORT,
                },
            }
        },
    }

    assert harness.charm._login_ui_layer.to_dict() == expected_layer


# finish test
def test_fetch_endpoint_with_ingress_relation_data(harness) -> None:
    """Test _fetch_endpoint function with ingress."""
    harness.set_can_connect(CONTAINER_NAME, True)

    setup_ingress_relation(harness)

    expected_data = "http://ingress:80/testing-identity-platform-login-ui"

    assert harness.charm._fetch_endpoint() == expected_data


# finish test
def test_fetch_endpoint_without_ingress_relation_data(harness) -> None:
    """Test _fetch_endpoint function without ingress."""
    harness.set_can_connect(CONTAINER_NAME, True)

    expected_data = (
        "identity-platform-login-ui-operator.testing.svc.cluster.local:8080"
    )

    assert harness.charm._fetch_endpoint() == expected_data
