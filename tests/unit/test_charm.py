# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.
#
# Learn more about testing at: https://juju.is/docs/sdk/testing

"""Test functions for unit testing Identity Platform Login UI Operator."""
import json
from unittest.mock import MagicMock

import pytest
from ops.model import ActiveStatus, WaitingStatus
from ops.testing import Harness

CONTAINER_NAME = "login-ui"
TEST_PORT = "8080"


def setup_ingress_relation(harness: Harness) -> int:
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
    return relation_id


def setup_hydra_relation(harness: Harness) -> int:
    relation_id = harness.add_relation("endpoint-info", "hydra")
    harness.add_relation_unit(relation_id, "hydra/0")
    harness.update_relation_data(
        relation_id,
        "hydra",
        {
            "admin_endpoint": "http://hydra-admin-url:80/testing-hydra",
            "public_endpoint": "http://hydra-public-url:80/testing-hydra",
        },
    )
    return relation_id


def setup_kratos_relation(harness: Harness) -> int:
    relation_id = harness.add_relation("kratos-endpoint-info", "kratos")
    harness.add_relation_unit(relation_id, "kratos/0")
    harness.update_relation_data(
        relation_id,
        "kratos",
        {
            "admin_endpoint": "http://kratos-admin-url:80/testing-kratos",
            "public_endpoint": "http://kratos-public-url:80/testing-kratos",
        },
    )
    return relation_id


def test_not_leader(harness) -> None:
    """Test with unit not being leader."""
    harness.set_leader(False)

    harness.charm.on.login_ui_pebble_ready.emit(CONTAINER_NAME)

    assert (
        "status_set",
        "maintenance",
        "Configuration in progress",
        {"is_app": False},
    ) in harness._get_backend_calls()


def test_install_can_connect(harness) -> None:
    """Test installation with connection."""
    harness.set_leader(True)
    harness.set_can_connect(CONTAINER_NAME, True)
    harness.charm.on.login_ui_pebble_ready.emit(CONTAINER_NAME)

    assert harness.charm.unit.status == ActiveStatus()


def test_install_can_not_connect(harness) -> None:
    """Test installation with connection."""
    harness.set_leader(True)
    harness.set_can_connect(CONTAINER_NAME, False)
    harness.charm.on.login_ui_pebble_ready.emit(CONTAINER_NAME)

    assert harness.charm.unit.status == WaitingStatus("Waiting to connect to Login_UI container")


def test_layer_updated(harness) -> None:
    """Test Pebble Layers after updates."""
    harness.set_leader(True)
    harness.set_can_connect(CONTAINER_NAME, True)
    harness.charm.on.login_ui_pebble_ready.emit(CONTAINER_NAME)

    setup_hydra_relation(harness)
    setup_kratos_relation(harness)

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
                    "HYDRA_ADMIN_URL": "http://hydra-public-url:80/testing-hydra",
                    "KRATOS_PUBLIC_URL": "http://kratos-public-url:80/testing-kratos",
                    "PORT": TEST_PORT,
                },
            }
        },
    }

    assert harness.charm._login_ui_layer.to_dict() == expected_layer


@pytest.mark.parametrize("port", ["8080"])
def test_ingress_relation_created(harness: Harness, mocked_fqdn: MagicMock, port: int) -> None:
    relation_id = setup_ingress_relation(harness)
    app_data = harness.get_relation_data(relation_id, harness.charm.app)

    assert app_data == {
        "host": mocked_fqdn.return_value,
        "model": harness.model.name,
        "name": "identity-platform-login-ui-operator",
        "port": port,
        "strip-prefix": "true",
    }


def test_login_ui_endpoint_info_relation_data_without_ingress_relation_data(
    harness: Harness,
) -> None:
    # set ingress relations without data
    public_ingress_relation_id = harness.add_relation("ingress", "traefik")
    harness.add_relation_unit(public_ingress_relation_id, "traefik/0")

    endpoint_info_relation_id = harness.add_relation("ui-endpoint-info", "hydra")
    harness.add_relation_unit(endpoint_info_relation_id, "hydra/0")

    expected_data = {
        "endpoint": "identity-platform-login-ui-operator.login-ui-model.svc.cluster.local:8080",
    }

    assert (
        harness.get_relation_data(endpoint_info_relation_id, "identity-platform-login-ui-operator")
        == expected_data
    )


def test_kratos_endpoint_info_relation_data_with_ingress_relation_data(harness: Harness) -> None:
    # set ingress relations with data
    setup_ingress_relation(harness)

    endpoint_info_relation_id = harness.add_relation("ui-endpoint-info", "hydra")
    harness.add_relation_unit(endpoint_info_relation_id, "hydra/0")

    expected_data = {
        "endpoint": "http://ingress:80/login-ui-model-identity-platform-login-ui",
    }

    assert (
        harness.get_relation_data(endpoint_info_relation_id, "identity-platform-login-ui-operator")
        == expected_data
    )
