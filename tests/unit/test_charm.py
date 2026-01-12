# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Test functions for unit testing Identity Platform Login UI Operator."""

from dataclasses import replace
from unittest.mock import patch

import ops.testing
from ops import ActiveStatus, BlockedStatus, WaitingStatus

from constants import COOKIES_KEY, WORKLOAD_CONTAINER_NAME, WORKLOAD_RUN_COMMAND
from exceptions import PebbleServiceError


def test_not_leader(
    context: ops.testing.Context,
    base_state: ops.testing.State,
    peer_relation: ops.testing.PeerRelation,
) -> None:
    """Test with unit not being leader."""
    state_in = replace(base_state, leader=False, relations=[peer_relation])

    container = state_in.get_container(WORKLOAD_CONTAINER_NAME)
    state_out = context.run(context.on.pebble_ready(container), state_in)

    assert state_out.unit_status == ActiveStatus()


def test_install_can_connect(
    context: ops.testing.Context,
    base_state: ops.testing.State,
    peer_relation: ops.testing.PeerRelation,
) -> None:
    """Test installation with connection."""
    state_in = replace(base_state, relations=[peer_relation])
    container = state_in.get_container(WORKLOAD_CONTAINER_NAME)
    state_out = context.run(context.on.pebble_ready(container), state_in)

    assert state_out.unit_status == ActiveStatus()


def test_install_can_not_connect(
    context: ops.testing.Context,
    base_state: ops.testing.State,
    peer_relation: ops.testing.PeerRelation,
) -> None:
    """Test installation with connection."""
    state_in = replace(base_state, relations=[peer_relation])

    original_container = state_in.get_container(WORKLOAD_CONTAINER_NAME)
    new_container = replace(original_container, can_connect=False)

    new_containers = [
        new_container if c.name == WORKLOAD_CONTAINER_NAME else c for c in state_in.containers
    ]
    state_in = replace(state_in, containers=new_containers)

    state_out = context.run(context.on.pebble_ready(new_container), state_in)

    assert state_out.unit_status == WaitingStatus("Waiting to connect to Login_UI container")


def test_missing_peer_relation_on_pebble_ready(
    context: ops.testing.Context, base_state: ops.testing.State
) -> None:

    container = base_state.get_container(WORKLOAD_CONTAINER_NAME)
    state_out = context.run(context.on.pebble_ready(container), base_state)

    assert state_out.unit_status == WaitingStatus("Waiting for peer relation")


def test_layer_updated_without_any_endpoint_info(
    context: ops.testing.Context,
    base_state: ops.testing.State,
    peer_relation: ops.testing.PeerRelation,
) -> None:
    """Test Pebble Layer after updates."""
    state_in = replace(base_state, relations=[peer_relation])
    container = state_in.get_container(WORKLOAD_CONTAINER_NAME)
    state_out = context.run(context.on.pebble_ready(container), state_in)

    container_out = state_out.get_container(WORKLOAD_CONTAINER_NAME)
    layer = container_out.layers[WORKLOAD_CONTAINER_NAME]
    service = layer.services[WORKLOAD_CONTAINER_NAME]
    env = service.environment

    assert service.command == WORKLOAD_RUN_COMMAND
    assert env["HYDRA_ADMIN_URL"] == ""
    assert env["KRATOS_PUBLIC_URL"] == ""
    assert env["LOG_LEVEL"] == "info"

    peer_rel = state_out.get_relations("identity-platform-login-ui")[0]

    assert len(peer_rel.local_app_data[COOKIES_KEY]) == 32


def test_layer_updated_with_tracing_endpoint_info(
    context: ops.testing.Context,
    base_state: ops.testing.State,
    peer_relation: ops.testing.PeerRelation,
    tempo_relation: ops.testing.Relation,
) -> None:
    """Test Pebble Layer when relation data is in place."""
    state_in = replace(base_state, relations=[peer_relation, tempo_relation])
    container = state_in.get_container(WORKLOAD_CONTAINER_NAME)
    state_out = context.run(context.on.pebble_ready(container), state_in)

    container_out = state_out.get_container(WORKLOAD_CONTAINER_NAME)
    layer = container_out.layers[WORKLOAD_CONTAINER_NAME]
    env = layer.services[WORKLOAD_CONTAINER_NAME].environment

    assert (
        env["OTEL_HTTP_ENDPOINT"]
        == "http://tempo-k8s-0.tempo-k8s-endpoints.namespace.svc.cluster.local:4318"
    )
    assert (
        env["OTEL_GRPC_ENDPOINT"]
        == "http://tempo-k8s-0.tempo-k8s-endpoints.namespace.svc.cluster.local:4317"
    )
    assert env["TRACING_ENABLED"] is True


def test_layer_env_updated_with_kratos_info(
    context: ops.testing.Context,
    base_state: ops.testing.State,
    peer_relation: ops.testing.PeerRelation,
    kratos_relation: ops.testing.Relation,
) -> None:
    """Test Pebble Layer when kratos relation data is in place."""
    state_in = replace(base_state, relations=[peer_relation, kratos_relation])
    container = state_in.get_container(WORKLOAD_CONTAINER_NAME)
    state_out = context.run(context.on.pebble_ready(container), state_in)

    container_out = state_out.get_container(WORKLOAD_CONTAINER_NAME)
    layer = container_out.layers[WORKLOAD_CONTAINER_NAME]
    env = layer.services[WORKLOAD_CONTAINER_NAME].environment

    kratos_data = kratos_relation.remote_app_data

    assert env["KRATOS_PUBLIC_URL"] == kratos_data["public_endpoint"]
    assert env["KRATOS_ADMIN_URL"] == kratos_data["admin_endpoint"]
    assert str(env["MFA_ENABLED"]) == kratos_data["mfa_enabled"]
    assert (
        str(env["OIDC_WEBAUTHN_SEQUENCING_ENABLED"])
        == kratos_data["oidc_webauthn_sequencing_enabled"]
    )
    assert env["FEATURE_FLAGS"] == kratos_data["feature_flags"]


def test_layer_updated_with_hydra_endpoint_info(
    context: ops.testing.Context,
    base_state: ops.testing.State,
    peer_relation: ops.testing.PeerRelation,
    hydra_relation: ops.testing.Relation,
) -> None:
    """Test Pebble Layer when relation data is in place."""
    state_in = replace(base_state, relations=[peer_relation, hydra_relation])
    container = state_in.get_container(WORKLOAD_CONTAINER_NAME)
    state_out = context.run(context.on.pebble_ready(container), state_in)

    container_out = state_out.get_container(WORKLOAD_CONTAINER_NAME)
    layer = container_out.layers[WORKLOAD_CONTAINER_NAME]
    env = layer.services[WORKLOAD_CONTAINER_NAME].environment

    assert env["HYDRA_ADMIN_URL"] == hydra_relation.remote_app_data["admin_endpoint"]


def test_traefik_route_integration(
    context: ops.testing.Context,
    base_state: ops.testing.State,
    peer_relation: ops.testing.PeerRelation,
    public_route_relation: ops.testing.Relation,
) -> None:
    """Test integration with Traefik."""
    state_in = replace(base_state, relations=[peer_relation, public_route_relation])
    container = state_in.get_container(WORKLOAD_CONTAINER_NAME)
    state_out = context.run(context.on.pebble_ready(container), state_in)

    assert state_out.unit_status == ActiveStatus()


def test_config_changed(
    context: ops.testing.Context,
    base_state: ops.testing.State,
    peer_relation: ops.testing.PeerRelation,
) -> None:
    state_in = replace(base_state, relations=[peer_relation])
    state_out = context.run(context.on.config_changed(), state_in)
    assert state_out.unit_status == ActiveStatus()


def test_pebble_service_error_handling(
    context: ops.testing.Context,
    base_state: ops.testing.State,
    peer_relation: ops.testing.PeerRelation,
) -> None:
    state_in = replace(base_state, relations=[peer_relation])
    container = state_in.get_container(WORKLOAD_CONTAINER_NAME)

    with patch("services.PebbleService.plan", side_effect=PebbleServiceError("Plan failed")):
        state_out = context.run(context.on.pebble_ready(container), state_in)

    assert state_out.unit_status == BlockedStatus("Failed to replan, please consult the logs")


def test_public_route_broken(
    context: ops.testing.Context,
    base_state: ops.testing.State,
    peer_relation: ops.testing.PeerRelation,
    public_route_relation: ops.testing.Relation,
) -> None:
    state_in = replace(base_state, relations=[peer_relation, public_route_relation])
    state_out = context.run(context.on.relation_broken(public_route_relation), state_in)
    assert state_out.unit_status == ActiveStatus()


def test_config_changed_cannot_connect(
    context: ops.testing.Context,
    base_state: ops.testing.State,
    peer_relation: ops.testing.PeerRelation,
) -> None:
    state_in = replace(base_state, relations=[peer_relation])
    original_container = state_in.get_container(WORKLOAD_CONTAINER_NAME)
    new_container = replace(original_container, can_connect=False)
    # Reconstruct state
    new_containers = [
        new_container if c.name == WORKLOAD_CONTAINER_NAME else c for c in state_in.containers
    ]
    state_in = replace(state_in, containers=new_containers)

    state_out = context.run(context.on.config_changed(), state_in)
    assert state_out.unit_status == WaitingStatus("Waiting to connect to Login_UI container")


def test_public_route_changed(
    context: ops.testing.Context,
    base_state: ops.testing.State,
    peer_relation: ops.testing.PeerRelation,
    public_route_relation: ops.testing.Relation,
) -> None:
    state_in = replace(base_state, relations=[peer_relation, public_route_relation])
    state_out = context.run(context.on.relation_changed(public_route_relation), state_in)
    assert state_out.unit_status == ActiveStatus()
