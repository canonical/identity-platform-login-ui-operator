#!/usr/bin/env python3
# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.
#
# Learn more at: https://juju.is/docs/sdk

"""A Juju charm for Identity Platform Login UI."""
import logging
from pathlib import Path
from typing import Optional

from charms.hydra.v0.hydra_endpoints import (
    HydraEndpointsRelationDataMissingError,
    HydraEndpointsRelationMissingError,
    HydraEndpointsRequirer,
)
from charms.identity_platform_login_ui_operator.v0.login_ui_endpoints import (
    LoginUIEndpointsProvider,
    LoginUINonLeaderOperationError,
)
from charms.kratos.v0.kratos_endpoints import (
    KratosEndpointsRelationDataMissingError,
    KratosEndpointsRequirer,
)
from charms.loki_k8s.v0.loki_push_api import LogProxyConsumer, PromtailDigestError
from charms.observability_libs.v0.kubernetes_service_patch import KubernetesServicePatch
from charms.prometheus_k8s.v0.prometheus_scrape import MetricsEndpointProvider
from charms.traefik_k8s.v1.ingress import (
    IngressPerAppReadyEvent,
    IngressPerAppRequirer,
    IngressPerAppRevokedEvent,
)
from ops.charm import CharmBase, ConfigChangedEvent, HookEvent, RelationEvent, WorkloadEvent
from ops.main import main
from ops.model import ActiveStatus, BlockedStatus, MaintenanceStatus, WaitingStatus
from ops.pebble import ChangeError, Layer

from utils import normalise_url



APPLICATION_PORT = "8080"


logger = logging.getLogger(__name__)


class IdentityPlatformLoginUiOperatorCharm(CharmBase):
    """Charmed Identity Platform Login UI."""

    def __init__(self, *args):
        """Initialize Charm."""
        super().__init__(*args)
        self._container_name = "login-ui"
        self._container = self.unit.get_container(self._container_name)
        self._hydra_relation_name = "endpoint-info"
        self._kratos_relation_name = "kratos-endpoint-info"
        self._prometheus_scrape_relation_name = "metrics-endpoint"
        self._loki_push_api_relation_name = "logging"
        self._login_ui_service_command = "identity_platform_login_ui"
        self._log_dir = Path("/var/log/ui")
        self._log_path = self._log_dir / "ui.log"

        self.service_patcher = KubernetesServicePatch(
            self, [("identity-platform-login-ui", int(APPLICATION_PORT))]
        )
        self.ingress = IngressPerAppRequirer(
            self,
            relation_name="ingress",
            port=APPLICATION_PORT,
            strip_prefix=True,
        )

        self.kratos_endpoints = KratosEndpointsRequirer(
            self, relation_name=self._kratos_relation_name
        )
        self.hydra_endpoints = HydraEndpointsRequirer(
            self, relation_name=self._hydra_relation_name
        )
        self.endpoints_provider = LoginUIEndpointsProvider(self)

        self.metrics_endpoint = MetricsEndpointProvider(
            self,
            relation_name=self._prometheus_scrape_relation_name,
            jobs=[
                {
                    "metrics_path": "/api/v0/metrics",
                    "static_configs": [
                        {
                            "targets": [f"*:{APPLICATION_PORT}"],
                        }
                    ],
                }
            ],
        )

        self.loki_consumer = LogProxyConsumer(
            self,
            log_files=[str(self._log_path)],
            relation_name=self._loki_push_api_relation_name,
            container_name=self._container_name,
        )

        self.framework.observe(self.on.login_ui_pebble_ready, self._on_login_ui_pebble_ready)
        self.framework.observe(self.on.config_changed, self._on_config_changed)
        self.framework.observe(
            self.on[self._kratos_relation_name].relation_changed, self._update_pebble_layer
        )
        self.framework.observe(
            self.endpoints_provider.on.ready, self._update_login_ui_endpoint_relation_data
        )
        self.framework.observe(
            self.on[self._hydra_relation_name].relation_changed, self._update_pebble_layer
        )
        self.framework.observe(self.ingress.on.ready, self._on_ingress_ready)
        self.framework.observe(self.ingress.on.revoked, self._on_ingress_revoked)

        self.framework.observe(
            self.loki_consumer.on.promtail_digest_error,
            self._promtail_error,
        )

    def _on_login_ui_pebble_ready(self, event: WorkloadEvent) -> None:
        """Define and start a workload using the Pebble API."""
        # Necessary directory for log forwarding
        if not self._container.can_connect():
            event.defer()
            self.unit.status = WaitingStatus("Waiting to connect to Login_UI container")
            return
        if not self._container.isdir(str(self._log_dir)):
            self._container.make_dir(path=str(self._log_dir), make_parents=True)
            logger.info(f"Created directory {self._log_dir}")

        self._update_pebble_layer(event)

    def _on_config_changed(self, event: ConfigChangedEvent) -> None:
        """Handle changed configuration."""
        self._update_pebble_layer(event)

    def _update_pebble_layer(self, event: HookEvent) -> None:
        if not self._container.can_connect():
            event.defer()
            logger.info("Cannot connect to Login_UI container. Deferring the event.")
            self.unit.status = WaitingStatus("Waiting to connect to Login_UI container")
            return

        self.unit.status = MaintenanceStatus("Configuration in progress")

        self._container.add_layer(self._container_name, self._login_ui_layer, combine=True)
        logger.info("Pebble plan updated with new configuration, replanning")
        try:
            self._container.replan()
        except ChangeError as err:
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
    def _log_level(self) -> str:
        return self.config["log_level"]

    @property
    def _tracing_enabled(self) -> bool:
        return self.config["tracing_enabled"]

    @property
    def _domain_url(self) -> Optional[str]:
        return normalise_url(self.ingress.url) if self.ingress.is_ready() else None

    @property
    def _login_ui_layer(self) -> Layer:
        # Define Pebble layer configuration
        pebble_layer = {
            "summary": "login_ui layer",
            "description": "pebble config layer for identity platform login ui",
            "services": {
                self._container_name: {
                    "override": "replace",
                    "summary": "identity platform login ui",
                    "command": "identity-platform-login-ui",
                    "startup": "enabled",
                    "environment": {
                        "HYDRA_ADMIN_URL": self._get_hydra_endpoint_info(),
                        "KRATOS_PUBLIC_URL": self._get_kratos_endpoint_info(),
                        "PORT": APPLICATION_PORT,
                        "BASE_URL": self._domain_url,
                        "JAEGER_ENDPOINT": "", # TODO @shipperizer this will be populated when tempo is setup by COS and passed via the integration 
                        "TRACING_ENABLED": self._tracing_enabled,
                        "LOG_LEVEL": self._log_level,
                        "LOG_FILE": self._log_path,
                    },
                }
            },
            "checks": {
                "login-ui-alive": {
                    "override": "replace",
                    "http": {"url": f"http://localhost:{APPLICATION_PORT}/health/alive"},
                },
            },
        }
        return Layer(pebble_layer)

    def _get_kratos_endpoint_info(self) -> str:
        if self.model.relations[self._kratos_relation_name]:
            try:
                kratos_endpoints = self.kratos_endpoints.get_kratos_endpoints()
                kratos_public_url = kratos_endpoints["public_endpoint"]
                return kratos_public_url
            except KratosEndpointsRelationDataMissingError:
                logger.info("No kratos-endpoint-info relation data found")
                return ""
        return ""

    def _update_login_ui_endpoint_relation_data(self, event: RelationEvent) -> None:
        endpoint = self._domain_url or ""
        try:
            self.endpoints_provider.send_endpoints_relation_data(endpoint)
            logger.info(f"Sending login ui endpoint info: endpoint - {endpoint}")
        except LoginUINonLeaderOperationError:
            logger.info("Non-leader unit can't update relation data")

    def _get_hydra_endpoint_info(self) -> str:
        hydra_url = ""
        try:
            hydra_endpoints = self.hydra_endpoints.get_hydra_endpoints()
            hydra_url = hydra_endpoints["admin_endpoint"]
        except HydraEndpointsRelationDataMissingError:
            logger.info("No hydra endpoint-info relation data found")
        except HydraEndpointsRelationMissingError:
            logger.info("No hydra endpoint-info relation found")
        return hydra_url

    def _promtail_error(self, event: PromtailDigestError) -> None:
        logger.error(event.message)


if __name__ == "__main__":  # pragma: nocover
    main(IdentityPlatformLoginUiOperatorCharm)
