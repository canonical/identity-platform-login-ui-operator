# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Unit test configuration."""

import json
from unittest.mock import mock_open, patch

import ops.testing
import pytest
from pytest_mock import MockerFixture

from charm import IdentityPlatformLoginUiOperatorCharm
from constants import WORKLOAD_CONTAINER_NAME


@pytest.fixture(autouse=True)
def mocked_k8s_resource_patch(mocker: MockerFixture) -> None:
    mocker.patch(
        "charms.observability_libs.v0.kubernetes_compute_resources_patch.ResourcePatcher",
        autospec=True,
    )
    mocker.patch.multiple(
        "charm.KubernetesComputeResourcesPatch",
        _namespace="testing",
        _patch=lambda *a, **kw: True,
        is_ready=lambda *a, **kw: True,
    )


@pytest.fixture
def context() -> ops.testing.Context:
    """Initialize context with Charm."""
    return ops.testing.Context(IdentityPlatformLoginUiOperatorCharm)


@pytest.fixture
def container_can_connect() -> ops.testing.Container:
    """Workload container in connectable state."""
    return ops.testing.Container(
        name=WORKLOAD_CONTAINER_NAME,
        can_connect=True,
        execs={
            ops.testing.Exec(
                ["identity-platform-login-ui", "version"],
                return_code=0,
                stdout="App Version: 1.42.0",
            )
        },
    )


@pytest.fixture
def container_cannot_connect() -> ops.testing.Container:
    """Workload container in non-connectable state."""
    return ops.testing.Container(
        name=WORKLOAD_CONTAINER_NAME,
        can_connect=False,
    )


def create_state(
    *,
    leader: bool = True,
    can_connect: bool = True,
    container: ops.testing.Container | None = None,
    relations: list[ops.testing.Relation] | None = None,
) -> ops.testing.State:
    """Factory function to create charm state with explicit parameters.

    Args:
        leader: Whether this unit is the leader
        can_connect: Whether the workload container can connect (ignored if container provided)
        container: Custom container to use (overrides can_connect if provided)
        relations: List of relations to include in the state
    """
    if container is None:
        container = ops.testing.Container(
            name=WORKLOAD_CONTAINER_NAME,
            can_connect=can_connect,
            execs={
                ops.testing.Exec(
                    ["identity-platform-login-ui", "version"],
                    return_code=0,
                    stdout="App Version: 1.42.0",
                )
            } if can_connect else {},
        )

    return ops.testing.State(
        leader=leader,
        containers=[container],
        relations=relations or [],
    )


@pytest.fixture(autouse=True)
def patch_certificate_transfer_integration_file_open():
    with patch(
        "certificate_transfer_integration.open", new_callable=mock_open, read_data="data"
    ) as f:
        yield f


@pytest.fixture
def peer_relation() -> ops.testing.PeerRelation:
    return ops.testing.PeerRelation(
        endpoint="identity-platform-login-ui",
        interface="identity_platform_login_ui_peers",
    )


@pytest.fixture
def kratos_relation() -> ops.testing.Relation:
    return ops.testing.Relation(
        endpoint="kratos-info",
        interface="kratos_info",
        remote_app_name="kratos",
        remote_app_data={
            "admin_endpoint": "http://kratos-admin-url:80/testing-kratos",
            "public_endpoint": "http://kratos-public-url:80/testing-kratos",
            "mfa_enabled": "True",
            "oidc_webauthn_sequencing_enabled": "False",
            "feature_flags": "password,totp,webauthn,backup_codes,account_linking",
        },
    )


@pytest.fixture
def hydra_relation() -> ops.testing.Relation:
    return ops.testing.Relation(
        endpoint="hydra-endpoint-info",
        interface="hydra_endpoints",
        remote_app_name="hydra",
        remote_app_data={
            "admin_endpoint": "http://hydra-admin-url:80/testing-hydra",
            "public_endpoint": "http://hydra-public-url:80/testing-hydra",
        },
    )


@pytest.fixture
def tempo_relation() -> ops.testing.Relation:
    return ops.testing.Relation(
        endpoint="tracing",
        interface="tracing",
        remote_app_name="tempo-k8s",
        remote_app_data={
            "receivers": json.dumps([
                {
                    "protocol": {"name": "otlp_http", "type": "http"},
                    "url": "http://tempo-k8s-0.tempo-k8s-endpoints.namespace.svc.cluster.local:4318",
                },
                {
                    "protocol": {"name": "otlp_grpc", "type": "grpc"},
                    "url": "http://tempo-k8s-0.tempo-k8s-endpoints.namespace.svc.cluster.local:4317",
                },
            ])
        },
    )


@pytest.fixture
def public_route_relation() -> ops.testing.Relation:
    return ops.testing.Relation(
        endpoint="public-route",
        interface="traefik_route",
        remote_app_name="traefik-k8s",
    )
