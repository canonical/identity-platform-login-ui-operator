# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.
#
# Learn more about testing at: https://juju.is/docs/sdk/testing

"""Test functions for unit testing Identity Platform Login UI Operator."""

import json
from typing import Tuple

from charms.identity_platform_login_ui_operator.v0.login_ui_endpoints import LoginUIProviderData
from ops.model import ActiveStatus, WaitingStatus
from ops.testing import Harness
from pytest_mock import MockerFixture

from constants import WORKLOAD_RUN_COMMAND

CONTAINER_NAME = "login-ui"
TEST_PORT = "8080"


def setup_peer_relation(harness: Harness) -> Tuple[int, str]:
    app_name = "identity-platform-login-ui"
    relation_id = harness.add_relation("identity-platform-login-ui", app_name)
    return relation_id, app_name


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
    relation_id = harness.add_relation("kratos-info", "kratos")
    harness.add_relation_unit(relation_id, "kratos/0")
    harness.update_relation_data(
        relation_id,
        "kratos",
        {
            "admin_endpoint": f"http://kratos-admin-url:80/{harness.model.name}-kratos",
            "public_endpoint": f"http://kratos-public-url:80/{harness.model.name}-kratos",
            "mfa_enabled": "True",
            "oidc_webauthn_sequencing_enabled": "False",
        },
    )
    return relation_id


def setup_hydra_relation(harness: Harness) -> int:
    relation_id = harness.add_relation("hydra-endpoint-info", "hydra")
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


def setup_loki_relation(harness: Harness) -> None:
    relation_id = harness.add_relation("logging", "loki-k8s")
    harness.add_relation_unit(relation_id, "loki-k8s/0")
    databag = {
        "promtail_binary_zip_url": json.dumps({
            "amd64": {
                "filename": "promtail-static-amd64",
                "zipsha": "543e333b0184e14015a42c3c9e9e66d2464aaa66eca48b29e185a6a18f67ab6d",
                "binsha": "17e2e271e65f793a9fbe81eab887b941e9d680abe82d5a0602888c50f5e0cac9",
                "url": "https://github.com/canonical/loki-k8s-operator/releases/download/promtail-v2.5.0/promtail-static-amd64.gz",
            }
        }),
    }
    unit_databag = {
        "endpoint": json.dumps({
            "url": "http://loki-k8s-0.loki-k8s-endpoints.model0.svc.cluster.local:3100/loki/api/v1/push"
        })
    }
    harness.update_relation_data(
        relation_id,
        "loki-k8s/0",
        unit_databag,
    )
    harness.update_relation_data(
        relation_id,
        "loki-k8s",
        databag,
    )


def setup_tempo_relation(harness: Harness) -> int:
    relation_id = harness.add_relation("tracing", "tempo-k8s")
    harness.add_relation_unit(relation_id, "tempo-k8s/0")

    trace_databag = {
        "receivers": '[{"protocol": {"name": "otlp_http", "type": "http"},'
        '"url": "http://tempo-k8s-0.tempo-k8s-endpoints.namespace.svc.cluster.local:4318"},'
        '{"protocol": {"name": "otlp_grpc", "type": "grpc"},'
        '"url": "http://tempo-k8s-0.tempo-k8s-endpoints.namespace.svc.cluster.local:4317"}]',
    }
    harness.update_relation_data(
        relation_id,
        "tempo-k8s",
        trace_databag,
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
    setup_peer_relation(harness)
    harness.charm.on.login_ui_pebble_ready.emit(CONTAINER_NAME)

    assert harness.charm.unit.status == ActiveStatus()


def test_install_can_not_connect(harness: Harness) -> None:
    """Test installation with connection."""
    harness.set_leader(True)
    harness.set_can_connect(CONTAINER_NAME, False)
    harness.charm.on.login_ui_pebble_ready.emit(CONTAINER_NAME)

    assert harness.charm.unit.status == WaitingStatus("Waiting to connect to Login_UI container")


def test_missing_peer_relation_on_pebble_ready(harness: Harness) -> None:
    harness.set_leader(True)
    harness.set_can_connect(CONTAINER_NAME, True)
    harness.charm.on.login_ui_pebble_ready.emit(CONTAINER_NAME)

    assert harness.charm.unit.status == WaitingStatus("Waiting for peer relation")


def test_layer_updated_without_any_endpoint_info(harness: Harness) -> None:
    """Test Pebble Layer after updates."""
    harness.set_leader(True)
    harness.set_can_connect(CONTAINER_NAME, True)
    setup_peer_relation(harness)
    harness.charm.on.login_ui_pebble_ready.emit(CONTAINER_NAME)

    expected_layer = {
        "summary": "login_ui layer",
        "description": "pebble config layer for identity platform login ui",
        "services": {
            CONTAINER_NAME: {
                "override": "replace",
                "summary": "identity platform login ui",
                "command": WORKLOAD_RUN_COMMAND,
                "startup": "enabled",
                "environment": {
                    "HYDRA_ADMIN_URL": "",
                    "KRATOS_PUBLIC_URL": "",
                    "KRATOS_ADMIN_URL": "",
                    "PORT": TEST_PORT,
                    "BASE_URL": None,
                    "COOKIES_ENCRYPTION_KEY": harness.charm._cookie_encryption_key,
                    "TRACING_ENABLED": False,
                    "AUTHORIZATION_ENABLED": False,
                    "LOG_LEVEL": harness.charm._log_level,
                    "DEBUG": False,
                },
            }
        },
        "checks": {
            "login-ui-alive": {
                "override": "replace",
                "http": {"url": f"http://localhost:{TEST_PORT}/api/v0/status"},
            },
        },
    }

    assert harness.charm._login_ui_layer.to_dict() == expected_layer
    assert len(harness.charm._cookie_encryption_key) == 32


def test_layer_updated_with_tracing_endpoint_info(harness: Harness) -> None:
    """Test Pebble Layer when relation data is in place."""
    harness.set_leader(True)
    harness.set_can_connect(CONTAINER_NAME, True)
    setup_peer_relation(harness)
    harness.charm.on.login_ui_pebble_ready.emit(CONTAINER_NAME)
    setup_tempo_relation(harness)

    pebble_env = harness.charm._login_ui_layer.to_dict()["services"][CONTAINER_NAME]["environment"]

    assert (
        pebble_env["OTEL_HTTP_ENDPOINT"]
        == "http://tempo-k8s-0.tempo-k8s-endpoints.namespace.svc.cluster.local:4318"
    )
    assert (
        pebble_env["OTEL_GRPC_ENDPOINT"]
        == "http://tempo-k8s-0.tempo-k8s-endpoints.namespace.svc.cluster.local:4317"
    )
    assert pebble_env["TRACING_ENABLED"]


def test_layer_env_updated_with_kratos_info(harness: Harness) -> None:
    """Test Pebble Layer when kratos relation data is in place."""
    harness.set_leader(True)
    harness.set_can_connect(CONTAINER_NAME, True)
    setup_peer_relation(harness)
    harness.charm.on.login_ui_pebble_ready.emit(CONTAINER_NAME)
    kratos_relation_id = setup_kratos_relation(harness)

    assert (
        harness.charm._login_ui_layer.to_dict()["services"][CONTAINER_NAME]["environment"][
            "KRATOS_PUBLIC_URL"
        ]
        == harness.get_relation_data(kratos_relation_id, "kratos")["public_endpoint"]
    )

    assert (
        harness.charm._login_ui_layer.to_dict()["services"][CONTAINER_NAME]["environment"][
            "KRATOS_ADMIN_URL"
        ]
        == harness.get_relation_data(kratos_relation_id, "kratos")["admin_endpoint"]
    )
    assert (
        str(
            harness.charm._login_ui_layer.to_dict()["services"][CONTAINER_NAME]["environment"][
                "MFA_ENABLED"
            ]
        )
        == harness.get_relation_data(kratos_relation_id, "kratos")["mfa_enabled"]
    )
    assert (
        str(
            harness.charm._login_ui_layer.to_dict()["services"][CONTAINER_NAME]["environment"][
                "OIDC_WEBAUTHN_SEQUENCING_ENABLED"
            ]
        )
        == harness.get_relation_data(kratos_relation_id, "kratos")[
            "oidc_webauthn_sequencing_enabled"
        ]
    )


def test_layer_updated_with_hydra_endpoint_info(harness: Harness) -> None:
    """Test Pebble Layer when relation data is in place."""
    harness.set_leader(True)
    harness.set_can_connect(CONTAINER_NAME, True)
    setup_peer_relation(harness)
    harness.charm.on.login_ui_pebble_ready.emit(CONTAINER_NAME)
    hydra_relation_id = setup_hydra_relation(harness)

    assert (
        harness.charm._login_ui_layer.to_dict()["services"][CONTAINER_NAME]["environment"][
            "HYDRA_ADMIN_URL"
        ]
        == harness.get_relation_data(hydra_relation_id, "hydra")["admin_endpoint"]
    )


# TODO @shipperizer evaluate if this test brings anything to the plate given it's a
# composite of the 2 tests above
def test_layer_updated_with_endpoint_info(harness: Harness) -> None:
    """Test Pebble Layer when relation data is in place."""
    harness.set_leader(True)
    harness.set_can_connect(CONTAINER_NAME, True)
    setup_peer_relation(harness)
    harness.charm.on.login_ui_pebble_ready.emit(CONTAINER_NAME)
    hydra_relation_id = setup_hydra_relation(harness)
    kratos_relation_id = setup_kratos_relation(harness)

    assert (
        harness.charm._login_ui_layer.to_dict()["services"][CONTAINER_NAME]["environment"][
            "KRATOS_PUBLIC_URL"
        ]
        == harness.get_relation_data(kratos_relation_id, "kratos")["public_endpoint"]
    )
    assert (
        harness.charm._login_ui_layer.to_dict()["services"][CONTAINER_NAME]["environment"][
            "HYDRA_ADMIN_URL"
        ]
        == harness.get_relation_data(hydra_relation_id, "hydra")["admin_endpoint"]
    )


def test_layer_updated_with_ingress_ready(harness: Harness) -> None:
    harness.set_leader(True)
    harness.set_can_connect(CONTAINER_NAME, True)
    setup_peer_relation(harness)
    harness.charm.on.login_ui_pebble_ready.emit(CONTAINER_NAME)
    _, url = setup_ingress_relation(harness)

    assert harness.charm._login_ui_layer.to_dict()["services"][CONTAINER_NAME]["environment"][
        "BASE_URL"
    ] == url.replace("http", "https").replace(":80", "")


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

    url = url.replace("http", "https").replace(":80", "")
    mocked_service_patcher.assert_called_with(
        LoginUIProviderData(
            consent_url=f"{url}/ui/consent",
            error_url=f"{url}/ui/error",
            login_url=f"{url}/ui/login",
            oidc_error_url=f"{url}/ui/oidc_error",
            device_verification_url=f"{url}/ui/device_code",
            post_device_done_url=f"{url}/ui/device_complete",
            recovery_url=f"{url}/ui/reset_email",
            settings_url=f"{url}/ui/reset_password",
            webauthn_settings_url=f"{url}/ui/setup_passkey",
        )
    )


def test_ui_endpoint_info_relation_databag(harness: Harness) -> None:
    harness.set_can_connect(CONTAINER_NAME, True)
    _, url = setup_ingress_relation(harness)
    url = url.replace("http", "https").replace(":80", "")

    relation_id = harness.add_relation("ui-endpoint-info", "requirer")
    harness.add_relation_unit(relation_id, "requirer/0")

    expected_data = {
        "consent_url": f"{url}/ui/consent",
        "error_url": f"{url}/ui/error",
        "login_url": f"{url}/ui/login",
        "oidc_error_url": f"{url}/ui/oidc_error",
        "device_verification_url": f"{url}/ui/device_code",
        "post_device_done_url": f"{url}/ui/device_complete",
        "recovery_url": f"{url}/ui/reset_email",
        "settings_url": f"{url}/ui/reset_password",
        "webauthn_settings_url": f"{url}/ui/setup_passkey",
    }

    relation_data = harness.get_relation_data(relation_id, harness.model.app.name)

    assert relation_data == expected_data


def test_on_pebble_ready_with_loki(harness: Harness) -> None:
    harness.set_leader(True)
    harness.set_can_connect(CONTAINER_NAME, True)
    setup_peer_relation(harness)
    container = harness.model.unit.get_container(CONTAINER_NAME)
    harness.charm.on.login_ui_pebble_ready.emit(container)
    setup_loki_relation(harness)

    assert harness.model.unit.status == ActiveStatus()
