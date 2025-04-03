#!/usr/bin/env python3
# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.
#
# Learn more at: https://juju.is/docs/sdk

"""A Juju charm for Identity Platform Login UI."""

import logging
import re
import secrets
from ast import literal_eval
from typing import Dict, Optional

from charms.grafana_k8s.v0.grafana_dashboard import GrafanaDashboardProvider
from charms.hydra.v0.hydra_endpoints import (
    HydraEndpointsRelationDataMissingError,
    HydraEndpointsRelationMissingError,
    HydraEndpointsRequirer,
)
from charms.identity_platform_login_ui_operator.v0.login_ui_endpoints import (
    LoginUIEndpointsProvider,
    LoginUIProviderData,
)
from charms.kratos.v0.kratos_info import KratosInfoRelationDataMissingError, KratosInfoRequirer
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
from ops.pebble import ChangeError, Error, Layer

from certificate_transfer_integration import CertTransfer
from constants import (
    APPLICATION_PORT,
    CERTIFICATE_TRANSFER_NAME,
    COOKIES_KEY,
    PEER,
    WORKLOAD_CONTAINER_NAME,
)
from utils import normalise_url

logger = logging.getLogger(__name__)


class IdentityPlatformLoginUiOperatorCharm(CharmBase):
    """Charmed Identity Platform Login UI."""

    def __init__(self, *args):
        """Initialize Charm."""
        super().__init__(*args)
        self._container = self.unit.get_container(WORKLOAD_CONTAINER_NAME)
        self._hydra_relation_name = "hydra-endpoint-info"
        self._kratos_relation_name = "kratos-info"
        self._prometheus_scrape_relation_name = "metrics-endpoint"
        self._loki_push_api_relation_name = "logging"
        self._grafana_dashboard_relation_name = "grafana-dashboard"
        self._tracing_relation_name = "tracing"
        self._login_ui_service_command = "/usr/bin/identity-platform-login-ui serve"

        self.service_patcher = KubernetesServicePatch(
            self, [("identity-platform-login-ui", APPLICATION_PORT)]
        )
        self.ingress = IngressPerAppRequirer(
            self,
            relation_name="ingress",
            port=APPLICATION_PORT,
            strip_prefix=True,
            redirect_https=False,
        )

        self._kratos_info = KratosInfoRequirer(self, relation_name=self._kratos_relation_name)

        self.hydra_endpoints = HydraEndpointsRequirer(
            self, relation_name=self._hydra_relation_name
        )
        self.endpoints_provider = LoginUIEndpointsProvider(self)

        self.tracing = TracingEndpointRequirer(
            self,
            relation_name=self._tracing_relation_name,
            protocols=["otlp_http", "otlp_grpc"],
        )

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

        self._log_forwarder = LogForwarder(self, relation_name=self._loki_push_api_relation_name)

        self._grafana_dashboards = GrafanaDashboardProvider(
            self, relation_name=self._grafana_dashboard_relation_name
        )

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
            self.on[self._kratos_relation_name].relation_changed, self._update_pebble_layer
        )
        self.framework.observe(
            self.endpoints_provider.on.ready, self._update_login_ui_endpoint_relation_data
        )
        self.framework.observe(
            self.on[self._hydra_relation_name].relation_changed, self._update_pebble_layer
        )

        self.framework.observe(self.tracing.on.endpoint_changed, self._update_pebble_layer)
        self.framework.observe(self.tracing.on.endpoint_removed, self._update_pebble_layer)

        self.framework.observe(self.ingress.on.ready, self._on_ingress_ready)
        self.framework.observe(self.ingress.on.revoked, self._on_ingress_revoked)

    def _get_version(self) -> Optional[str]:
        cmd = ["identity-platform-login-ui", "version"]
        try:
            process = self._container.exec(cmd)
            stdout, _ = process.wait_output()
        except Error:
            return

        out_re = r"App Version:\s*(.+)\s*$"
        versions = re.search(out_re, stdout)
        if versions:
            return versions[1]

    def _set_version(self) -> None:
        if version := self._get_version():
            self.unit.set_workload_version(version)

    def _on_login_ui_pebble_ready(self, event: WorkloadEvent) -> None:
        """Define and start a workload using the Pebble API."""
        # Necessary directory for log forwarding
        if not self._container.can_connect():
            event.defer()
            self.unit.status = WaitingStatus("Waiting to connect to Login_UI container")
            return

        self._set_version()
        self._update_pebble_layer(event)

    def _on_install(self, event: InstallEvent) -> None:
        if not self._container.can_connect():
            event.defer()
            logger.info("Cannot connect to Login_UI container. Deferring the event.")
            self.unit.status = WaitingStatus("Waiting to connect to Login_UI container")
            return

    def _on_config_changed(self, event: ConfigChangedEvent) -> None:
        """Handle changed configuration."""
        self._update_pebble_layer(event)

    def _update_pebble_layer(self, event: HookEvent) -> None:
        if not self._container.can_connect():
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

        self._container.add_layer(WORKLOAD_CONTAINER_NAME, self._login_ui_layer, combine=True)
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
        return self.config["log_level"]

    @property
    def _domain_url(self) -> Optional[str]:
        return normalise_url(self.ingress.url) if self.ingress.is_ready() else None

    @property
    def _tracing_ready(self) -> bool:
        return self.tracing.is_ready()

    @property
    def _login_ui_layer(self) -> Layer:
        kratos_info = self._get_kratos_info()

        # Define container configuration
        container = {
            "override": "replace",
            "summary": "identity platform login ui",
            "command": self._login_ui_service_command,
            "startup": "enabled",
            "environment": {
                "HYDRA_ADMIN_URL": self._get_hydra_endpoint_info(),
                "KRATOS_PUBLIC_URL": kratos_info.get("public_endpoint", ""),
                "KRATOS_ADMIN_URL": kratos_info.get("admin_endpoint", ""),
                "PORT": str(APPLICATION_PORT),
                "BASE_URL": self._domain_url,
                "COOKIES_ENCRYPTION_KEY": self._cookie_encryption_key,
                "TRACING_ENABLED": False,
                "AUTHORIZATION_ENABLED": False,
                "LOG_LEVEL": self._log_level,
                "DEBUG": self._log_level == "DEBUG",
            },
        }

        if self._kratos_info.is_ready():
            container["environment"]["MFA_ENABLED"] = literal_eval(kratos_info.get("mfa_enabled"))
            container["environment"]["OIDC_WEBAUTHN_SEQUENCING_ENABLED"] = literal_eval(
                kratos_info.get("oidc_webauthn_sequencing_enabled")
            )

        if self._tracing_ready:
            container["environment"]["OTEL_HTTP_ENDPOINT"] = self.tracing.get_endpoint("otlp_http")
            container["environment"]["OTEL_GRPC_ENDPOINT"] = self.tracing.get_endpoint("otlp_grpc")
            container["environment"]["TRACING_ENABLED"] = True

        # Define Pebble layer configuration
        pebble_layer = {
            "summary": "login_ui layer",
            "description": "pebble config layer for identity platform login ui",
            "services": {WORKLOAD_CONTAINER_NAME: container},
            "checks": {
                "login-ui-alive": {
                    "override": "replace",
                    "http": {"url": f"http://localhost:{APPLICATION_PORT}/api/v0/status"},
                },
            },
        }
        return Layer(pebble_layer)

    def _get_kratos_info(self) -> Dict:
        kratos_info = {}
        if self._kratos_info.is_ready():
            try:
                kratos_info = self._kratos_info.get_kratos_info()
            except KratosInfoRelationDataMissingError:
                logger.info("No kratos-info relation data found")
        return kratos_info

    def _update_login_ui_endpoint_relation_data(self, event: RelationEvent) -> None:
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

    def _get_hydra_endpoint_info(self) -> str:
        hydra_url = ""
        try:
            hydra_endpoints = self.hydra_endpoints.get_hydra_endpoints()
            hydra_url = hydra_endpoints["admin_endpoint"]
        except HydraEndpointsRelationDataMissingError:
            logger.info("No hydra-endpoint-info relation data found")
        except HydraEndpointsRelationMissingError:
            logger.info("No hydra-endpoint-info relation found")
        return hydra_url


if __name__ == "__main__":  # pragma: nocover
    main(IdentityPlatformLoginUiOperatorCharm)
