# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Test functions for unit testing Identity Platform Login UI Operator."""

from dataclasses import replace
from unittest.mock import patch

import ops.testing
import pytest
from ops import ActiveStatus, BlockedStatus, WaitingStatus

from constants import COOKIES_KEY, WORKLOAD_CONTAINER_NAME, WORKLOAD_RUN_COMMAND
from exceptions import PebbleServiceError

from .conftest import create_state


class TestPebbleReadyEvent:
    """Tests for identity-platform-login-ui-pebble-ready event handling."""

    def test_pebble_ready_can_connect(
        self,
        context: ops.testing.Context,
        peer_relation: ops.testing.PeerRelation,
    ) -> None:
        """Test installation with connection."""
        state_in = create_state(relations=[peer_relation])
        container = state_in.get_container(WORKLOAD_CONTAINER_NAME)

        state_out = context.run(context.on.pebble_ready(container), state_in)

        assert state_out.unit_status == ActiveStatus()

    def test_pebble_ready_cannot_connect(
        self,
        context: ops.testing.Context,
        peer_relation: ops.testing.PeerRelation,
    ) -> None:
        """Test installation with connection."""
        state_in = create_state(can_connect=False, relations=[peer_relation])
        container = state_in.get_container(WORKLOAD_CONTAINER_NAME)

        state_out = context.run(context.on.pebble_ready(container), state_in)

        assert state_out.unit_status == WaitingStatus("Waiting to connect to Login_UI container")

    def test_pebble_ready_missing_peer_relation(
        self,
        context: ops.testing.Context,
    ) -> None:
        state_in = create_state()
        container = state_in.get_container(WORKLOAD_CONTAINER_NAME)

        state_out = context.run(context.on.pebble_ready(container), state_in)

        assert state_out.unit_status == WaitingStatus("Waiting for peer relation")

    def test_pebble_ready_layer_configuration(
        self,
        context: ops.testing.Context,
        peer_relation: ops.testing.PeerRelation,
    ) -> None:
        """Test Pebble Layer after updates."""
        state_in = create_state(relations=[peer_relation])
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


class TestConfigChangedEvent:
    """Tests for config-changed event handling."""

    def test_config_changed_can_connect(
        self,
        context: ops.testing.Context,
        peer_relation: ops.testing.PeerRelation,
    ) -> None:
        state_in = create_state(relations=[peer_relation])
        state_out = context.run(context.on.config_changed(), state_in)
        assert state_out.unit_status == ActiveStatus()

    def test_config_changed_cannot_connect(
        self,
        context: ops.testing.Context,
        peer_relation: ops.testing.PeerRelation,
    ) -> None:
        state_in = create_state(can_connect=False, relations=[peer_relation])

        state_out = context.run(context.on.config_changed(), state_in)
        assert state_out.unit_status == WaitingStatus("Waiting to connect to Login_UI container")


class TestKratosRelationEvents:
    """Tests for kratos-info relation event handling."""

    def test_layer_env_updated_with_kratos_info(
        self,
        context: ops.testing.Context,
        peer_relation: ops.testing.PeerRelation,
        kratos_relation: ops.testing.Relation,
    ) -> None:
        """Test Pebble Layer when kratos relation data is in place."""
        state_in = create_state(relations=[peer_relation, kratos_relation])
        container = state_in.get_container(WORKLOAD_CONTAINER_NAME)
        state_out = context.run(context.on.pebble_ready(container), state_in)

        container_out = state_out.get_container(WORKLOAD_CONTAINER_NAME)
        layer = container_out.layers[WORKLOAD_CONTAINER_NAME]
        env = layer.services[WORKLOAD_CONTAINER_NAME].environment

        kratos_data = kratos_relation.remote_app_data

        assert env["KRATOS_PUBLIC_URL"] == kratos_data["public_endpoint"]
        assert env["KRATOS_ADMIN_URL"] == kratos_data["admin_endpoint"]
        assert str(env["MFA_ENABLED"]) == kratos_data["mfa_enabled"]
        assert str(env["VERIFICATION_ENABLED"]) == kratos_data["verification_enabled"]
        assert (
            str(env["OIDC_WEBAUTHN_SEQUENCING_ENABLED"])
            == kratos_data["oidc_webauthn_sequencing_enabled"]
        )
        assert env["FEATURE_FLAGS"] == kratos_data["feature_flags"]


class TestHydraRelationEvents:
    """Tests for hydra-endpoint-info relation event handling."""

    def test_layer_updated_with_hydra_endpoint_info(
        self,
        context: ops.testing.Context,
        peer_relation: ops.testing.PeerRelation,
        hydra_relation: ops.testing.Relation,
    ) -> None:
        """Test Pebble Layer when relation data is in place."""
        state_in = create_state(relations=[peer_relation, hydra_relation])
        container = state_in.get_container(WORKLOAD_CONTAINER_NAME)
        state_out = context.run(context.on.pebble_ready(container), state_in)

        container_out = state_out.get_container(WORKLOAD_CONTAINER_NAME)
        layer = container_out.layers[WORKLOAD_CONTAINER_NAME]
        env = layer.services[WORKLOAD_CONTAINER_NAME].environment

        assert env["HYDRA_ADMIN_URL"] == hydra_relation.remote_app_data["admin_endpoint"]


class TestTenantServiceRelationEvents:
    """Tests for tenant-service-info relation event handling."""

    def test_layer_env_updated_with_tenant_service_info(
        self,
        context: ops.testing.Context,
        peer_relation: ops.testing.PeerRelation,
        tenant_service_relation: ops.testing.Relation,
    ) -> None:
        """Test Pebble Layer includes multi-tenancy env vars when tenant-service relation is present."""
        state_in = create_state(relations=[peer_relation, tenant_service_relation])
        container = state_in.get_container(WORKLOAD_CONTAINER_NAME)
        state_out = context.run(context.on.pebble_ready(container), state_in)

        container_out = state_out.get_container(WORKLOAD_CONTAINER_NAME)
        layer = container_out.layers[WORKLOAD_CONTAINER_NAME]
        env = layer.services[WORKLOAD_CONTAINER_NAME].environment

        assert (
            env["TENANT_SERVICE_GRPC_ADDRESS"]
            == "tenant-service.namespace.svc.cluster.local:50051"
        )
        assert env["MULTI_TENANCY_ENABLED"] is True
        # v0.27.0 read TENANTS_SERVICE_URL; v0.28.0 replaced it with the gRPC address.
        assert "TENANTS_SERVICE_URL" not in env

    def test_layer_env_without_tenant_service_info(
        self,
        context: ops.testing.Context,
        peer_relation: ops.testing.PeerRelation,
    ) -> None:
        """Test Pebble Layer does not include multi-tenancy env vars without the relation."""
        state_in = create_state(relations=[peer_relation])
        container = state_in.get_container(WORKLOAD_CONTAINER_NAME)
        state_out = context.run(context.on.pebble_ready(container), state_in)

        container_out = state_out.get_container(WORKLOAD_CONTAINER_NAME)
        layer = container_out.layers[WORKLOAD_CONTAINER_NAME]
        env = layer.services[WORKLOAD_CONTAINER_NAME].environment

        assert "TENANTS_SERVICE_URL" not in env
        assert "TENANT_SERVICE_GRPC_ADDRESS" not in env
        assert "MULTI_TENANCY_ENABLED" not in env

    def test_tenant_service_relation_broken(
        self,
        context: ops.testing.Context,
        peer_relation: ops.testing.PeerRelation,
        tenant_service_relation: ops.testing.Relation,
    ) -> None:
        """Test that relation broken removes multi-tenancy env vars."""
        state_in = create_state(relations=[peer_relation, tenant_service_relation])
        state_out = context.run(context.on.relation_broken(tenant_service_relation), state_in)

        assert state_out.unit_status == ActiveStatus()


class TestTempoRelationEvents:
    """Tests for tempo relation event handling."""

    def test_layer_updated_with_tracing_endpoint_info(
        self,
        context: ops.testing.Context,
        peer_relation: ops.testing.PeerRelation,
        tempo_relation: ops.testing.Relation,
    ) -> None:
        """Test Pebble Layer when relation data is in place."""
        state_in = create_state(relations=[peer_relation, tempo_relation])
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


class TestPublicRouteRelationEvents:
    """Tests for public-ingress relation event handling."""

    def test_istio_route_integration(
        self,
        context: ops.testing.Context,
        peer_relation: ops.testing.PeerRelation,
        public_route_relation: ops.testing.Relation,
    ) -> None:
        """Test integration with Istio ingress."""
        state_in = create_state(relations=[peer_relation, public_route_relation])
        container = state_in.get_container(WORKLOAD_CONTAINER_NAME)
        state_out = context.run(context.on.pebble_ready(container), state_in)

        assert state_out.unit_status == ActiveStatus()

    def test_public_route_broken(
        self,
        context: ops.testing.Context,
        peer_relation: ops.testing.PeerRelation,
        public_route_relation: ops.testing.Relation,
    ) -> None:
        state_in = create_state(relations=[peer_relation, public_route_relation])
        state_out = context.run(context.on.relation_broken(public_route_relation), state_in)
        assert state_out.unit_status == ActiveStatus()

    def test_public_route_changed(
        self,
        context: ops.testing.Context,
        peer_relation: ops.testing.PeerRelation,
        public_route_relation: ops.testing.Relation,
    ) -> None:
        state_in = create_state(relations=[peer_relation, public_route_relation])
        state_out = context.run(context.on.relation_changed(public_route_relation), state_in)
        assert state_out.unit_status == ActiveStatus()

    def test_domain_url_is_http_when_tls_disabled(
        self,
        context: ops.testing.Context,
        peer_relation: ops.testing.PeerRelation,
        public_route_relation: ops.testing.Relation,
    ) -> None:
        """Test that _domain_url uses HTTP when tls_enabled is False."""
        state_in = create_state(relations=[peer_relation, public_route_relation])
        container = state_in.get_container(WORKLOAD_CONTAINER_NAME)

        state_out = context.run(context.on.pebble_ready(container), state_in)

        container_out = state_out.get_container(WORKLOAD_CONTAINER_NAME)
        env = container_out.layers[WORKLOAD_CONTAINER_NAME].services[WORKLOAD_CONTAINER_NAME].environment
        assert env["BASE_URL"] == "http://login.example.com"

    def test_domain_url_is_https_when_tls_enabled(
        self,
        context: ops.testing.Context,
        peer_relation: ops.testing.PeerRelation,
        public_route_relation_tls: ops.testing.Relation,
    ) -> None:
        """Test that _domain_url uses HTTPS when tls_enabled is True."""
        state_in = create_state(relations=[peer_relation, public_route_relation_tls])
        container = state_in.get_container(WORKLOAD_CONTAINER_NAME)

        state_out = context.run(context.on.pebble_ready(container), state_in)

        container_out = state_out.get_container(WORKLOAD_CONTAINER_NAME)
        env = container_out.layers[WORKLOAD_CONTAINER_NAME].services[WORKLOAD_CONTAINER_NAME].environment
        assert env["BASE_URL"] == "https://login.example.com"

    def test_domain_url_is_none_when_no_external_host(
        self,
        context: ops.testing.Context,
        peer_relation: ops.testing.PeerRelation,
        public_route_relation_no_host: ops.testing.Relation,
    ) -> None:
        """Test that _domain_url is None when external_host is empty."""
        state_in = create_state(relations=[peer_relation, public_route_relation_no_host])
        container = state_in.get_container(WORKLOAD_CONTAINER_NAME)

        state_out = context.run(context.on.pebble_ready(container), state_in)

        container_out = state_out.get_container(WORKLOAD_CONTAINER_NAME)
        env = container_out.layers[WORKLOAD_CONTAINER_NAME].services[WORKLOAD_CONTAINER_NAME].environment
        assert env["BASE_URL"] is None

    def test_submit_config_called_with_all_routes(
        self,
        context: ops.testing.Context,
        peer_relation: ops.testing.PeerRelation,
        public_route_relation: ops.testing.Relation,
    ) -> None:
        """Test that submit_config is called with 2 HTTPRoutes covering all paths."""
        from charmlibs.interfaces.istio_ingress_route import IstioIngressRouteConfig

        submitted_configs = []

        def capture_submit(config: IstioIngressRouteConfig) -> None:
            submitted_configs.append(config)

        state_in = create_state(relations=[peer_relation, public_route_relation])

        with patch(
            "charmlibs.interfaces.istio_ingress_route.IstioIngressRouteRequirer.submit_config",
            side_effect=capture_submit,
        ):
            context.run(context.on.relation_changed(public_route_relation), state_in)

        assert len(submitted_configs) == 1
        config = submitted_configs[0]
        assert isinstance(config, IstioIngressRouteConfig)
        assert {r.name for r in config.http_routes} == {"self-service", "api-and-ui"}

        api_and_ui = next(r for r in config.http_routes if r.name == "api-and-ui")
        matched_paths = {m.path.value for m in api_and_ui.matches if m.path}
        assert matched_paths == {
            "/api/device",
            "/api/consent",
            "/api/v0/app-config",
            "/api/v0/tenants/resolve",
            "/api/v0/tenants",
            "/api/v0/auth/tenant",
            "/api/v0/sso/complete",
            "/ui",
        }

    def test_submit_config_uses_port_443_when_tls_enabled(
        self,
        context: ops.testing.Context,
        peer_relation: ops.testing.PeerRelation,
        public_route_relation_tls: ops.testing.Relation,
    ) -> None:
        """Test that submit_config uses port 443 for the listener when TLS is enabled."""
        from charmlibs.interfaces.istio_ingress_route import IstioIngressRouteConfig

        submitted_configs = []

        def capture_submit(config: IstioIngressRouteConfig) -> None:
            submitted_configs.append(config)

        state_in = create_state(relations=[peer_relation, public_route_relation_tls])

        with patch(
            "charmlibs.interfaces.istio_ingress_route.IstioIngressRouteRequirer.submit_config",
            side_effect=capture_submit,
        ):
            context.run(context.on.relation_changed(public_route_relation_tls), state_in)

        assert len(submitted_configs) == 1
        config = submitted_configs[0]
        listener_ports = {r.listener.port for r in config.http_routes}
        assert listener_ports == {443}

    def test_submit_config_uses_port_80_when_tls_disabled(
        self,
        context: ops.testing.Context,
        peer_relation: ops.testing.PeerRelation,
        public_route_relation: ops.testing.Relation,
    ) -> None:
        """Test that submit_config uses port 80 for the listener when TLS is disabled."""
        from charmlibs.interfaces.istio_ingress_route import IstioIngressRouteConfig

        submitted_configs = []

        def capture_submit(config: IstioIngressRouteConfig) -> None:
            submitted_configs.append(config)

        state_in = create_state(relations=[peer_relation, public_route_relation])

        with patch(
            "charmlibs.interfaces.istio_ingress_route.IstioIngressRouteRequirer.submit_config",
            side_effect=capture_submit,
        ):
            context.run(context.on.relation_changed(public_route_relation), state_in)

        assert len(submitted_configs) == 1
        config = submitted_configs[0]
        listener_ports = {r.listener.port for r in config.http_routes}
        assert listener_ports == {80}


class TestHolisticHandler:
    """Tests for holistic event handling."""

    def test_all_ready_non_leader(
        self,
        context: ops.testing.Context,
        peer_relation: ops.testing.PeerRelation,
    ) -> None:
        """Test with unit not being leader."""
        state_in = create_state(leader=False, relations=[peer_relation])

        container = state_in.get_container(WORKLOAD_CONTAINER_NAME)
        state_out = context.run(context.on.pebble_ready(container), state_in)

        assert state_out.unit_status == ActiveStatus()

    def test_all_relations_established(
        self,
        context: ops.testing.Context,
        peer_relation: ops.testing.PeerRelation,
        kratos_relation: ops.testing.Relation,
        hydra_relation: ops.testing.Relation,
        tempo_relation: ops.testing.Relation,
        public_route_relation: ops.testing.Relation,
    ) -> None:
        """Test installation with all relations established."""
        state_in = create_state(
            relations=[
                peer_relation,
                kratos_relation,
                hydra_relation,
                tempo_relation,
                public_route_relation,
            ]
        )
        container = state_in.get_container(WORKLOAD_CONTAINER_NAME)

        state_out = context.run(context.on.pebble_ready(container), state_in)

        assert state_out.unit_status == ActiveStatus()


class TestStatusManagement:
    """Tests for status management and error handling."""

    def test_pebble_service_error_handling(
        self,
        context: ops.testing.Context,
        peer_relation: ops.testing.PeerRelation,
    ) -> None:
        state_in = create_state(relations=[peer_relation])
        container = state_in.get_container(WORKLOAD_CONTAINER_NAME)

        with patch("services.PebbleService.plan", side_effect=PebbleServiceError("Plan failed")):
            state_out = context.run(context.on.pebble_ready(container), state_in)

        assert state_out.unit_status == BlockedStatus("Failed to replan, please consult the logs")


BYOSSO_ENV_VARS = (
    "BYOSSO_ENABLED",
    "SSO_SERVICE_GRPC_ADDRESS",
    "KRATOS_PRIVILEGED_SESSION_MAX_AGE",
)


def _environment(state_out: ops.testing.State) -> dict:
    layer = state_out.get_container(WORKLOAD_CONTAINER_NAME).layers[WORKLOAD_CONTAINER_NAME]
    return layer.services[WORKLOAD_CONTAINER_NAME].environment


class TestBYOSSO:
    """Tests for the "Bring Your Own SSO" configuration and its integrations."""

    @pytest.fixture
    def byosso_relations(
        self,
        peer_relation: ops.testing.PeerRelation,
        kratos_relation: ops.testing.Relation,
        tenant_service_relation: ops.testing.Relation,
        sso_service_relation: ops.testing.Relation,
        ui_endpoint_relation: ops.testing.Relation,
    ) -> dict[str, ops.testing.Relation]:
        return {
            "identity-platform-login-ui": peer_relation,
            "kratos-info": kratos_relation,
            "tenant-service-info": tenant_service_relation,
            "sso-service-info": sso_service_relation,
            "ui-endpoint-info": ui_endpoint_relation,
        }

    @staticmethod
    def _published(state_out: ops.testing.State, relation: ops.testing.Relation) -> str | None:
        return state_out.get_relation(relation.id).local_app_data.get("byosso_enabled")

    def test_layer_without_byosso_by_default(
        self,
        context: ops.testing.Context,
        byosso_relations: dict[str, ops.testing.Relation],
    ) -> None:
        """Off, the integrations change nothing in the workload."""
        state_in = create_state(relations=list(byosso_relations.values()))
        container = state_in.get_container(WORKLOAD_CONTAINER_NAME)

        state_out = context.run(context.on.pebble_ready(container), state_in)

        env = _environment(state_out)
        assert not set(BYOSSO_ENV_VARS) & set(env)
        assert self._published(state_out, byosso_relations["ui-endpoint-info"]) == "false"
        assert state_out.unit_status == ActiveStatus()

    def test_layer_env_with_byosso(
        self,
        context: ops.testing.Context,
        byosso_relations: dict[str, ops.testing.Relation],
    ) -> None:
        state_in = create_state(
            relations=list(byosso_relations.values()), config={"byosso_enabled": True}
        )
        container = state_in.get_container(WORKLOAD_CONTAINER_NAME)

        state_out = context.run(context.on.pebble_ready(container), state_in)

        env = _environment(state_out)
        assert env["BYOSSO_ENABLED"] is True
        assert env["MULTI_TENANCY_ENABLED"] is True
        assert env["SSO_SERVICE_GRPC_ADDRESS"] == "sso-service.namespace.svc.cluster.local:50051"
        assert env["KRATOS_PRIVILEGED_SESSION_MAX_AGE"] == "1h"
        assert self._published(state_out, byosso_relations["ui-endpoint-info"]) == "true"
        assert state_out.unit_status == ActiveStatus()

    @pytest.mark.parametrize("missing", ["tenant-service-info", "sso-service-info", "kratos-info"])
    def test_byosso_missing_integration(
        self,
        context: ops.testing.Context,
        byosso_relations: dict[str, ops.testing.Relation],
        missing: str,
    ) -> None:
        """Without a requirement the charm plans nothing and says what is missing.

        What Kratos was told stays as it was.
        """
        ui_endpoint = replace(
            byosso_relations["ui-endpoint-info"], local_app_data={"byosso_enabled": "true"}
        )
        byosso_relations["ui-endpoint-info"] = ui_endpoint
        relations = [r for name, r in byosso_relations.items() if name != missing]
        state_in = create_state(relations=relations, config={"byosso_enabled": True})
        container = state_in.get_container(WORKLOAD_CONTAINER_NAME)

        state_out = context.run(context.on.pebble_ready(container), state_in)

        assert state_out.unit_status == BlockedStatus(f"Missing integration {missing}")
        assert (
            WORKLOAD_CONTAINER_NAME not in state_out.get_container(WORKLOAD_CONTAINER_NAME).layers
        )
        assert self._published(state_out, ui_endpoint) == "true"

    @pytest.mark.parametrize("pending", ["tenant-service-info", "sso-service-info", "kratos-info"])
    def test_byosso_waiting_for_integration_data(
        self,
        context: ops.testing.Context,
        byosso_relations: dict[str, ops.testing.Relation],
        pending: str,
    ) -> None:
        byosso_relations[pending] = replace(byosso_relations[pending], remote_app_data={})
        state_in = create_state(
            relations=list(byosso_relations.values()), config={"byosso_enabled": True}
        )
        container = state_in.get_container(WORKLOAD_CONTAINER_NAME)

        state_out = context.run(context.on.pebble_ready(container), state_in)

        assert state_out.unit_status == WaitingStatus(f"Waiting for {pending} data")
        assert (
            WORKLOAD_CONTAINER_NAME not in state_out.get_container(WORKLOAD_CONTAINER_NAME).layers
        )

    @pytest.mark.parametrize(
        "kratos_data, message",
        [
            (
                {"privileged_session_max_age": ""},
                "byosso_enabled needs a newer Kratos charm: refresh it",
            ),
            (
                {"oidc_webauthn_sequencing_enabled": "True"},
                "byosso_enabled conflicts with Kratos OIDC-WebAuthn sequencing",
            ),
            (
                {"verification_enabled": "False"},
                "byosso_enabled requires Kratos's enable_verification",
            ),
        ],
    )
    def test_byosso_refused_for_what_kratos_publishes(
        self,
        context: ops.testing.Context,
        byosso_relations: dict[str, ops.testing.Relation],
        kratos_data: dict,
        message: str,
    ) -> None:
        """login-ui and Kratos's charm refuse the feature on the same conditions."""
        kratos = byosso_relations["kratos-info"]
        byosso_relations["kratos-info"] = replace(
            kratos, remote_app_data={**kratos.remote_app_data, **kratos_data}
        )
        state_in = create_state(
            relations=list(byosso_relations.values()), config={"byosso_enabled": True}
        )

        state_out = context.run(context.on.config_changed(), state_in)

        assert state_out.unit_status == BlockedStatus(message)
        # Blocked on the feature: nothing is written.
        assert self._published(state_out, byosso_relations["ui-endpoint-info"]) is None

    def test_sso_service_relation_broken(
        self,
        context: ops.testing.Context,
        byosso_relations: dict[str, ops.testing.Relation],
    ) -> None:
        state_in = create_state(
            relations=list(byosso_relations.values()), config={"byosso_enabled": True}
        )

        state_out = context.run(
            context.on.relation_broken(byosso_relations["sso-service-info"]), state_in
        )

        assert state_out.unit_status == BlockedStatus("Missing integration sso-service-info")

    @pytest.mark.parametrize(
        "config, kratos_data, published",
        [
            ({"byosso_enabled": True}, {}, "true"),
            ({}, {}, "false"),
            # Blocked on the feature: what Kratos was told stays as it was.
            ({"byosso_enabled": True}, {"verification_enabled": "False"}, None),
        ],
    )
    def test_byosso_published_with_the_endpoints(
        self,
        context: ops.testing.Context,
        byosso_relations: dict[str, ops.testing.Relation],
        config: dict,
        kratos_data: dict,
        published: str | None,
    ) -> None:
        """A Kratos related later is told what the charm's configuration and relations say."""
        ui_endpoint = byosso_relations["ui-endpoint-info"]
        kratos = byosso_relations["kratos-info"]
        byosso_relations["kratos-info"] = replace(
            kratos, remote_app_data={**kratos.remote_app_data, **kratos_data}
        )
        state_in = create_state(relations=list(byosso_relations.values()), config=config)

        state_out = context.run(context.on.relation_created(ui_endpoint), state_in)

        assert self._published(state_out, ui_endpoint) == published
        assert "login_url" in state_out.get_relation(ui_endpoint.id).local_app_data
