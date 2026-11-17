#!/usr/bin/env python3
# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.
#
# Learn more at: https://juju.is/docs/sdk

"""A Juju charm for Identity Platform Login UI."""

import logging
import secrets
from typing import Optional

from charmlibs.interfaces.istio_ingress_route import IstioIngressRouteRequirer
from charms.grafana_k8s.v0.grafana_dashboard import GrafanaDashboardProvider
from charms.hydra.v0.hydra_endpoints import (
    HydraEndpointsRequirer,
)
from charms.identity_platform_login_ui_operator.v0.login_ui_endpoints import (
    LoginUIEndpointsProvider,
    LoginUIProviderData,
)
from charms.kratos.v0.kratos_info import KratosInfoRequirer
from charms.loki_k8s.v1.loki_push_api import LogForwarder
from charms.observability_libs.v0.kubernetes_compute_resources_patch import (
    K8sResourcePatchFailedEvent,
    KubernetesComputeResourcesPatch,
    ResourceRequirements,
    adjust_resource_requirements,
)
from charms.prometheus_k8s.v0.prometheus_scrape import MetricsEndpointProvider
from charms.tempo_k8s.v2.tracing import TracingEndpointRequirer
from charms.tenant_service.v0.tenant_service_info import TenantServiceInfoRequirer
from ops import (
    ActiveStatus,
    BlockedStatus,
    CharmBase,
    ConfigChangedEvent,
    HookEvent,
    MaintenanceStatus,
    Relation,
    RelationEvent,
    StatusBase,
    WaitingStatus,
    WorkloadEvent,
    main,
)
from ops.pebble import Layer
from sso_service_info import SSOServiceInfoRequirer

from certificate_transfer_integration import CertTransfer
from constants import (
    APPLICATION_PORT,
    CERTIFICATE_TRANSFER_NAME,
    COOKIES_KEY,
    GRAFANA_INTEGRATION_NAME,
    HYDRA_INTEGRATION_NAME,
    KRATOS_INTEGRATION_NAME,
    LOGGING_INTEGRATION_NAME,
    PEER_INTEGRATION_NAME,
    PROMETHEUS_INTEGRATION_NAME,
    PUBLIC_ROUTE_INTEGRATION_NAME,
    SSO_SERVICE_INFO_INTEGRATION_NAME,
    TENANT_SERVICE_INFO_INTEGRATION_NAME,
    TRACING_INTEGRATION_NAME,
    WORKLOAD_CONTAINER_NAME,
)
from exceptions import PebbleServiceError
from integrations import (
    BYOSSOData,
    HydraEndpointData,
    KratosInfoData,
    PublicRouteData,
    SSOServiceInfoData,
    TenantServiceInfoData,
    TracingData,
)
from services import PebbleService, WorkloadService
from utils import is_true

logger = logging.getLogger(__name__)


class IdentityPlatformLoginUiOperatorCharm(CharmBase):
    """Charmed Identity Platform Login UI."""

    def __init__(self, *args):
        """Initialize Charm."""
        super().__init__(*args)

        self._workload_service = WorkloadService(self.unit)
        self._pebble_service = PebbleService(self.unit)

        # public route via istio ingress routing configuration
        self.public_route = IstioIngressRouteRequirer(
            self,
            relation_name=PUBLIC_ROUTE_INTEGRATION_NAME,
        )

        # Kratos
        self._kratos_info = KratosInfoRequirer(self, relation_name=KRATOS_INTEGRATION_NAME)
        # Hydra
        self.hydra_endpoints = HydraEndpointsRequirer(self, relation_name=HYDRA_INTEGRATION_NAME)
        # Login UI
        self.endpoints_provider = LoginUIEndpointsProvider(self)
        # Tenant service
        self._tenant_service_info = TenantServiceInfoRequirer(
            self, relation_name=TENANT_SERVICE_INFO_INTEGRATION_NAME
        )
        self._sso_service_info = SSOServiceInfoRequirer(
            self, relation_name=SSO_SERVICE_INFO_INTEGRATION_NAME
        )

        # Tracing
        self.tracing = TracingEndpointRequirer(
            self, relation_name=TRACING_INTEGRATION_NAME, protocols=["otlp_http", "otlp_grpc"]
        )

        self.metrics_endpoint = MetricsEndpointProvider(
            self,
            relation_name=PROMETHEUS_INTEGRATION_NAME,
            jobs=[
                {
                    "metrics_path": "/api/v0/metrics",
                    "static_configs": [{"targets": [f"*:{APPLICATION_PORT}"]}],
                }
            ],
        )

        # Loki
        self._log_forwarder = LogForwarder(self, relation_name=LOGGING_INTEGRATION_NAME)

        # Grafana
        self._grafana_dashboards = GrafanaDashboardProvider(
            self, relation_name=GRAFANA_INTEGRATION_NAME
        )

        # Certificate transfer
        self.cert_transfer = CertTransfer(
            self,
            WORKLOAD_CONTAINER_NAME,
            self._holistic_handler,
            CERTIFICATE_TRANSFER_NAME,
        )

        self.resources_patch = KubernetesComputeResourcesPatch(
            self,
            WORKLOAD_CONTAINER_NAME,
            resource_reqs_func=self._resource_reqs_from_config,
        )

        self.framework.observe(self.on.login_ui_pebble_ready, self._on_login_ui_pebble_ready)
        self.framework.observe(self.on.config_changed, self._on_config_changed)
        self.framework.observe(self.on.update_status, self._holistic_handler)

        self.framework.observe(
            self.on[KRATOS_INTEGRATION_NAME].relation_changed, self._holistic_handler
        )
        self.framework.observe(
            self.on[TENANT_SERVICE_INFO_INTEGRATION_NAME].relation_changed,
            self._holistic_handler,
        )
        self.framework.observe(
            self.on[TENANT_SERVICE_INFO_INTEGRATION_NAME].relation_broken,
            self._holistic_handler,
        )
        self.framework.observe(
            self.on[SSO_SERVICE_INFO_INTEGRATION_NAME].relation_changed,
            self._holistic_handler,
        )
        self.framework.observe(
            self.on[SSO_SERVICE_INFO_INTEGRATION_NAME].relation_broken,
            self._holistic_handler,
        )
        self.framework.observe(
            self.endpoints_provider.on.ready, self._update_login_ui_endpoint_relation_data
        )
        self.framework.observe(
            self.on[HYDRA_INTEGRATION_NAME].relation_changed, self._holistic_handler
        )

        self.framework.observe(self.tracing.on.endpoint_changed, self._holistic_handler)
        self.framework.observe(self.tracing.on.endpoint_removed, self._holistic_handler)

        # peers
        self.framework.observe(
            self.on[PEER_INTEGRATION_NAME].relation_created, self._holistic_handler
        )
        self.framework.observe(
            self.on[PEER_INTEGRATION_NAME].relation_changed, self._holistic_handler
        )

        # public route
        self.framework.observe(
            self.public_route.on.ready,
            self._on_public_route_ready,
        )

        # resource patching
        self.framework.observe(
            self.resources_patch.on.patch_failed, self._on_resource_patch_failed
        )

    def _on_login_ui_pebble_ready(self, event: WorkloadEvent) -> None:
        """Define and start a workload using the Pebble API."""
        self.unit.status = MaintenanceStatus("Configuring resources")
        # Necessary directory for log forwarding
        if not self._pebble_service.can_connect():
            self.unit.status = WaitingStatus("Waiting to connect to Login_UI container")
            return

        self._workload_service.open_port()

        self._workload_service.set_version()
        self._holistic_handler(event)

    def _on_config_changed(self, event: ConfigChangedEvent) -> None:
        """Handle changed configuration."""
        self.unit.status = MaintenanceStatus("Configuring resources")
        self._holistic_handler(event)

    def _holistic_handler(self, event: HookEvent) -> None:
        if not self._pebble_service.can_connect():
            self.unit.status = WaitingStatus("Waiting to connect to Login_UI container")
            return

        if not self._peers:
            self.unit.status = WaitingStatus("Waiting for peer relation")
            return

        if self.unit.is_leader() and not self._cookie_encryption_key:
            self._peers.data[self.app][COOKIES_KEY] = secrets.token_hex(16)

        if (
            self.unit.is_leader()
            and self.public_route.is_ready()
        ):
            public_route_config = PublicRouteData.load(self.public_route).config
            self.public_route.submit_config(public_route_config)

        if status := self._byosso_status():
            self.unit.status = status
            return

        self.cert_transfer.push_ca_certs()

        logger.info("Pebble plan updated with new configuration, replanning")
        try:
            self._pebble_service.plan(self._login_ui_layer)
        except PebbleServiceError as err:
            logger.error(str(err))
            self.unit.status = BlockedStatus("Failed to replan, please consult the logs")
            return

        self._update_byosso_relation_data()
        self.unit.status = ActiveStatus()

    def _byosso_status(self) -> Optional[StatusBase]:
        """Why "Bring Your Own SSO" cannot be applied, or None when it can.

        login-ui refuses to start when BYOSSO_ENABLED lacks what it needs, and with the feature
        off it would not enforce the tenants' sign-in policies. So the charm plans neither: it
        reports what is missing and leaves the running layer.
        """
        if not self._byosso_enabled:
            return None

        kratos_info = KratosInfoData.load(self._kratos_info)
        requirements = (
            (
                TENANT_SERVICE_INFO_INTEGRATION_NAME,
                TenantServiceInfoData.load(self._tenant_service_info).is_ready,
            ),
            (
                SSO_SERVICE_INFO_INTEGRATION_NAME,
                SSOServiceInfoData.load(self._sso_service_info).is_ready,
            ),
            (KRATOS_INTEGRATION_NAME, kratos_info.is_ready),
        )
        for integration, is_ready in requirements:
            if status := self._integration_status(integration, is_ready):
                return status

        # login-ui has to apply the same privileged session age as Kratos.
        if not kratos_info.privileged_session_max_age:
            return BlockedStatus("byosso_enabled needs a newer Kratos charm: refresh it")

        if is_true(kratos_info.oidc_webauthn_sequencing_enabled):
            return BlockedStatus("byosso_enabled conflicts with Kratos OIDC-WebAuthn sequencing")

        # Kratos's charm refuses the feature without it, and would be left unconfigured.
        if not is_true(kratos_info.verification_enabled):
            return BlockedStatus("byosso_enabled requires Kratos's enable_verification")

        return None

    def _integration_status(self, integration: str, is_ready: bool) -> Optional[StatusBase]:
        if not self.model.get_relation(integration):
            return BlockedStatus(f"Missing integration {integration}")

        if not is_ready:
            return WaitingStatus(f"Waiting for {integration} data")

        return None

    def _on_public_route_ready(self, event: RelationEvent) -> None:
        self.unit.status = MaintenanceStatus("Configuring resources")
        self._holistic_handler(event)
        self._update_login_ui_endpoint_relation_data(event)

    def _on_resource_patch_failed(self, event: K8sResourcePatchFailedEvent) -> None:
        logger.error(f"Failed to patch resource constraints: {event.message}")
        self.unit.status = BlockedStatus(event.message)

    @property
    def _peers(self) -> Optional[Relation]:
        """The peer relation."""
        return self.model.get_relation(PEER_INTEGRATION_NAME)

    @property
    def _cookie_encryption_key(self) -> Optional[str]:
        """The cookie encryption key from the peer data bucket."""
        if not self._peers:
            return None
        return self._peers.data[self.app].get(COOKIES_KEY, None)

    @property
    def _log_level(self) -> str:
        return self.config.get("log_level")

    @property
    def _support_email(self) -> str:
        return self.config.get("support_email")

    @property
    def _byosso_enabled(self) -> bool:
        return bool(self.config.get("byosso_enabled"))

    @property
    def _byosso_data(self) -> Optional[BYOSSOData]:
        if not self._byosso_enabled:
            return None

        kratos_info = KratosInfoData.load(self._kratos_info)
        return BYOSSOData(
            sso_service_info=SSOServiceInfoData.load(self._sso_service_info),
            privileged_session_max_age=kratos_info.privileged_session_max_age,
        )

    @property
    def _domain_url(self) -> Optional[str]:
        if not self.public_route.is_ready():
            return None
        data = PublicRouteData.load(self.public_route)
        if not data.url.host:
            return None
        return str(data.url)

    @property
    def _login_ui_layer(self) -> Layer:
        return self._pebble_service.render_pebble_layer(
            self._domain_url,
            self._cookie_encryption_key,
            self._log_level,
            self._support_email,
            HydraEndpointData.load(self.hydra_endpoints),
            KratosInfoData.load(self._kratos_info),
            TracingData.load(self.tracing),
            TenantServiceInfoData.load(self._tenant_service_info),
            self._byosso_data,
        )

    def _resource_reqs_from_config(self) -> ResourceRequirements:
        limits = {"cpu": self.model.config.get("cpu"), "memory": self.model.config.get("memory")}
        requests = {"cpu": "100m", "memory": "200Mi"}
        return adjust_resource_requirements(limits, requests, adhere_to_requests=True)

    def _update_login_ui_endpoint_relation_data(self, _: RelationEvent) -> None:
        endpoint = self._domain_url or ""

        self.endpoints_provider.send_endpoints_relation_data(
            LoginUIProviderData(
                consent_url=f"{endpoint}/ui/consent",
                error_url=f"{endpoint}/ui/error",
                login_url=f"{endpoint}/ui/login",
                oidc_error_url=f"{endpoint}/ui/oidc_error",
                device_verification_url=f"{endpoint}/ui/device_code",
                post_device_done_url=f"{endpoint}/ui/device_complete",
                recovery_url=f"{endpoint}/ui/reset_email",
                registration_url=f"{endpoint}/ui/register",
                settings_url=f"{endpoint}/ui/manage_details",
                webauthn_settings_url=f"{endpoint}/ui/setup_passkey",
                account_linking_settings_url=f"{endpoint}/ui/manage_connected_accounts",
                verification_url=f"{endpoint}/ui/verification",
            )
        )
        # While the charm is blocked on the feature, what Kratos was told stays as it is.
        if not self._byosso_status():
            self._update_byosso_relation_data()

    def _update_byosso_relation_data(self) -> None:
        self.endpoints_provider.send_endpoints_relation_data(
            LoginUIProviderData(byosso_enabled="true" if self._byosso_enabled else "false")
        )


if __name__ == "__main__":  # pragma: nocover
    main(IdentityPlatformLoginUiOperatorCharm)
