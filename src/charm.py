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
from charms.observability_libs.v0.kubernetes_service_patch import KubernetesServicePatch
from charms.prometheus_k8s.v0.prometheus_scrape import MetricsEndpointProvider
from charms.tempo_k8s.v2.tracing import TracingEndpointRequirer
from charms.traefik_k8s.v2.ingress import (
    IngressPerAppReadyEvent,
    IngressPerAppRequirer,
    IngressPerAppRevokedEvent,
)
from ops.charm import (
    CharmBase,
    ConfigChangedEvent,
    HookEvent,
    InstallEvent,
    RelationEvent,
    WorkloadEvent,
)
from ops.main import main
from ops.model import ActiveStatus, BlockedStatus, MaintenanceStatus, Relation, WaitingStatus
from ops.pebble import Layer

from certificate_transfer_integration import CertTransfer
from config import CharmConfig
from constants import (
    APPLICATION_NAME,
    APPLICATION_PORT,
    CERTIFICATE_TRANSFER_NAME,
    COOKIES_KEY,
    GRAFANA_RELATION_NAME,
    HYDRA_RELATION_NAME,
    INGRESS_RELATION_NAME,
    KRATOS_RELATION_NAME,
    LOGGING_RELATION_NAME,
    PEER,
    PROMETHEUS_RELATION_NAME,
    TRACING_RELATION_NAME,
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
        self.charm_config = CharmConfig(self.config)

        self._workload_service = WorkloadService(self.unit)
        self._pebble_service = PebbleService(self.unit)

        self.service_patcher = KubernetesServicePatch(self, [(APPLICATION_NAME, APPLICATION_PORT)])

        # Ingress
        self.ingress = IngressPerAppRequirer(
            self,
            relation_name=INGRESS_RELATION_NAME,
            port=APPLICATION_PORT,
            strip_prefix=True,
            redirect_https=False,
        )

        # Kratos
        self._kratos_info = KratosInfoRequirer(self, relation_name=KRATOS_RELATION_NAME)
        # Hydra
        self.hydra_endpoints = HydraEndpointsRequirer(self, relation_name=HYDRA_RELATION_NAME)
        # Login UI
        self.endpoints_provider = LoginUIEndpointsProvider(self)

        # Tracing
        self.tracing = TracingEndpointRequirer(
            self, relation_name=TRACING_RELATION_NAME, protocols=["otlp_http", "otlp_grpc"]
        )

        self.metrics_endpoint = MetricsEndpointProvider(
            self,
            relation_name=PROMETHEUS_RELATION_NAME,
            jobs=[
                {
                    "metrics_path": "/api/v0/metrics",
                    "static_configs": [{"targets": [f"*:{APPLICATION_PORT}"]}],
                }
            ],
        )

        # Loki
        self._log_forwarder = LogForwarder(self, relation_name=LOGGING_RELATION_NAME)

        # Grafana
        self._grafana_dashboards = GrafanaDashboardProvider(
            self, relation_name=GRAFANA_RELATION_NAME
        )

        # Certificate transfer
        self.cert_transfer = CertTransfer(
            self,
            WORKLOAD_CONTAINER_NAME,
            self._update_pebble_layer,
            CERTIFICATE_TRANSFER_NAME,
        )

        self.framework.observe(self.on.login_ui_pebble_ready, self._on_login_ui_pebble_ready)
        self.framework.observe(self.on.config_changed, self._on_config_changed)
        self.framework.observe(self.on.install, self._on_install)

        self.framework.observe(
            self.on[KRATOS_RELATION_NAME].relation_changed, self._update_pebble_layer
        )
        self.framework.observe(
            self.endpoints_provider.on.ready, self._update_login_ui_endpoint_relation_data
        )
        self.framework.observe(
            self.on[HYDRA_RELATION_NAME].relation_changed, self._update_pebble_layer
        )

        self.framework.observe(self.tracing.on.endpoint_changed, self._update_pebble_layer)
        self.framework.observe(self.tracing.on.endpoint_removed, self._update_pebble_layer)

        self.framework.observe(self.ingress.on.ready, self._on_ingress_ready)
        self.framework.observe(self.ingress.on.revoked, self._on_ingress_revoked)

    def _on_login_ui_pebble_ready(self, event: WorkloadEvent) -> None:
        """Define and start a workload using the Pebble API."""
        # Necessary directory for log forwarding
        if not self._pebble_service.can_connect():
            event.defer()
            self.unit.status = WaitingStatus("Waiting to connect to Login_UI container")
            return

        self._workload_service.set_version()
        self._update_pebble_layer(event)

    def _on_install(self, event: InstallEvent) -> None:
        if not self._pebble_service.can_connect():
            event.defer()
            logger.info("Cannot connect to Login_UI container. Deferring the event.")
            self.unit.status = WaitingStatus("Waiting to connect to Login_UI container")
            return

    def _on_config_changed(self, event: ConfigChangedEvent) -> None:
        """Handle changed configuration."""
        self._update_pebble_layer(event)

    def _update_pebble_layer(self, event: HookEvent) -> None:
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

        self.unit.status = MaintenanceStatus("Configuration in progress")
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
        if self.unit.is_leader():
            logger.info("This app's public ingress URL: %s", event.url)
        self._update_pebble_layer(event)
        self._update_login_ui_endpoint_relation_data(event)

    def _on_ingress_revoked(self, event: IngressPerAppRevokedEvent) -> None:
        if self.unit.is_leader():
            logger.info("This app no longer has ingress")
        self._update_pebble_layer(event)
        self._update_login_ui_endpoint_relation_data(event)

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
        return self.charm_config["log_level"]

    @property
    def _domain_url(self) -> Optional[str]:
        return normalise_url(self.ingress.url) if self.ingress.is_ready() else None

    @property
    def _login_ui_layer(self) -> Layer:
        return self._pebble_service.render_pebble_layer(
            self._domain_url,
            self._cookie_encryption_key,
            self._log_level,
            HydraEndpointData.load(self.hydra_endpoints),
            KratosInfoData.load(self._kratos_info),
            TracingData.load(self.tracing),
        )

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
