#!/usr/bin/env python3
# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.
#
# Learn more at: https://juju.is/docs/sdk

"""A Juju charm for Identity Platform Login UI."""

import logging
import secrets
from typing import Optional

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
from charms.traefik_k8s.v2.ingress import (
    IngressPerAppReadyEvent,
    IngressPerAppRequirer,
    IngressPerAppRevokedEvent,
)
from ops import (
    ActiveStatus,
    BlockedStatus,
    CharmBase,
    ConfigChangedEvent,
    HookEvent,
    MaintenanceStatus,
    Relation,
    RelationEvent,
    WaitingStatus,
    WorkloadEvent,
    main,
)
from ops.pebble import Layer

from certificate_transfer_integration import CertTransfer
from constants import (
    APPLICATION_PORT,
    CERTIFICATE_TRANSFER_NAME,
    COOKIES_KEY,
    GRAFANA_INTEGRATION_NAME,
    HYDRA_INTEGRATION_NAME,
    INGRESS_INTEGRATION_NAME,
    KRATOS_INTEGRATION_NAME,
    LOGGING_INTEGRATION_NAME,
    PEER,
    PROMETHEUS_INTEGRATION_NAME,
    TRACING_INTEGRATION_NAME,
    WORKLOAD_CONTAINER_NAME,
)
from exceptions import PebbleServiceError
from integrations import HydraEndpointData, KratosInfoData, TracingData
from services import PebbleService, WorkloadService
from utils import normalise_url

logger = logging.getLogger(__name__)


class IdentityPlatformLoginUiOperatorCharm(CharmBase):
    """Charmed Identity Platform Login UI."""

    def __init__(self, *args):
        """Initialize Charm."""
        super().__init__(*args)

        self._workload_service = WorkloadService(self.unit)
        self._pebble_service = PebbleService(self.unit)

        # Ingress
        self.ingress = IngressPerAppRequirer(
            self,
            relation_name=INGRESS_INTEGRATION_NAME,
            port=APPLICATION_PORT,
            strip_prefix=True,
            redirect_https=False,
        )

        # Kratos
        self._kratos_info = KratosInfoRequirer(self, relation_name=KRATOS_INTEGRATION_NAME)
        # Hydra
        self.hydra_endpoints = HydraEndpointsRequirer(self, relation_name=HYDRA_INTEGRATION_NAME)
        # Login UI
        self.endpoints_provider = LoginUIEndpointsProvider(self)

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
            self.endpoints_provider.on.ready, self._update_login_ui_endpoint_relation_data
        )
        self.framework.observe(
            self.on[HYDRA_INTEGRATION_NAME].relation_changed, self._holistic_handler
        )

        self.framework.observe(self.tracing.on.endpoint_changed, self._holistic_handler)
        self.framework.observe(self.tracing.on.endpoint_removed, self._holistic_handler)

        self.framework.observe(self.ingress.on.ready, self._on_ingress_ready)
        self.framework.observe(self.ingress.on.revoked, self._on_ingress_revoked)

        # resource patching
        self.framework.observe(
            self.resources_patch.on.patch_failed, self._on_resource_patch_failed
        )

    def _on_login_ui_pebble_ready(self, event: WorkloadEvent) -> None:
        """Define and start a workload using the Pebble API."""
        self.unit.status = MaintenanceStatus("Configuring resources")
        # Necessary directory for log forwarding
        if not self._pebble_service.can_connect():
            event.defer()
            self.unit.status = WaitingStatus("Waiting to connect to Login_UI container")
            return

        self._workload_service.set_version()
        self._holistic_handler(event)

    def _on_config_changed(self, event: ConfigChangedEvent) -> None:
        """Handle changed configuration."""
        self.unit.status = MaintenanceStatus("Configuring resources")
        self._holistic_handler(event)

    def _holistic_handler(self, event: HookEvent) -> None:
        if not self._pebble_service.can_connect():
            event.defer()
            logger.info("Cannot connect to Login_UI container. Deferring the event.")
            self.unit.status = WaitingStatus("Waiting to connect to Login_UI container")
            return

        if not self._peers:
            self.unit.status = WaitingStatus("Waiting for peer relation")
            logger.info("Waiting for peer relation. Deferring the event.")
            event.defer()
            return

        if not self._cookie_encryption_key:
            self._peers.data[self.app][COOKIES_KEY] = secrets.token_hex(16)

        self.cert_transfer.push_ca_certs()

        logger.info("Pebble plan updated with new configuration, replanning")
        try:
            self._pebble_service.plan(self._login_ui_layer)
        except PebbleServiceError as err:
            logger.error(str(err))
            self.unit.status = BlockedStatus("Failed to replan, please consult the logs")
            return

        self.unit.status = ActiveStatus()

    def _on_ingress_ready(self, event: IngressPerAppReadyEvent) -> None:
        self.unit.status = MaintenanceStatus("Configuring resources")
        if self.unit.is_leader():
            logger.info("This app's public ingress URL: %s", event.url)
        self._holistic_handler(event)
        self._update_login_ui_endpoint_relation_data(event)

    def _on_ingress_revoked(self, event: IngressPerAppRevokedEvent) -> None:
        self.unit.status = MaintenanceStatus("Configuring resources")
        if self.unit.is_leader():
            logger.info("This app no longer has ingress")
        self._holistic_handler(event)
        self._update_login_ui_endpoint_relation_data(event)

    def _on_resource_patch_failed(self, event: K8sResourcePatchFailedEvent) -> None:
        logger.error(f"Failed to patch resource constraints: {event.message}")
        self.unit.status = BlockedStatus(event.message)

    @property
    def _peers(self) -> Optional[Relation]:
        """Fetch the peer relation."""
        return self.model.get_relation(PEER)

    @property
    def _cookie_encryption_key(self) -> Optional[str]:
        """Retrieve cookie encryption key from the peer data bucket."""
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
    def _domain_url(self) -> Optional[str]:
        return normalise_url(self.ingress.url) if self.ingress.is_ready() else None

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
                settings_url=f"{endpoint}/ui/reset_password",
                webauthn_settings_url=f"{endpoint}/ui/setup_passkey",
            )
        )


if __name__ == "__main__":  # pragma: nocover
    main(IdentityPlatformLoginUiOperatorCharm)
