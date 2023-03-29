#!/usr/bin/env python3
# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.
#
# Learn more at: https://juju.is/docs/sdk

"""A Juju charm for Identity Platform Login UI."""
import logging

from charms.observability_libs.v0.kubernetes_service_patch import KubernetesServicePatch
from charms.traefik_k8s.v1.ingress import (
    IngressPerAppReadyEvent,
    IngressPerAppRequirer,
    IngressPerAppRevokedEvent,
)
from charms.identity_platform_login_ui.v0.hydra_login_ui import HydraLoginUIProvider, HydraLoginUIRelationMissingError
from ops.charm import CharmBase, ConfigChangedEvent, HookEvent, WorkloadEvent, RelationEvent
from ops.main import main
from ops.model import ActiveStatus, BlockedStatus, MaintenanceStatus, WaitingStatus
from ops.pebble import ChangeError, Layer

APPLICATION_PORT = "8080"
HYDRA_LOGIN_UI_RELATION_NAME = "ui-endpoint-info"

logger = logging.getLogger(__name__)


class IdentityPlatformLoginUiOperatorCharm(CharmBase):
    """Charmed Identity Platform Login UI."""

    def __init__(self, *args):
        """Initialize Charm."""
        super().__init__(*args)
        self._container_name = "login-ui"
        self._container = self.unit.get_container(self._container_name)

        self.service_patcher = KubernetesServicePatch(
            self, [("identity-platform-login-ui", int(APPLICATION_PORT))]
        )
        self.ingress = IngressPerAppRequirer(
            self,
            relation_name="ingress",
            port=APPLICATION_PORT,
            strip_prefix=True,
        )
        self.hydra_login_ui_provider = HydraLoginUIProvider(self)

        self.framework.observe(self.on.login_ui_pebble_ready, self._on_login_ui_pebble_ready)
        self.framework.observe(self.on.config_changed, self._on_config_changed)
        self.framework.observe(self.ingress.on.ready, self._on_ingress_ready)
        self.framework.observe(self.ingress.on.revoked, self._on_ingress_revoked)
        self.framework.observe(
            self.on[HYDRA_LOGIN_UI_RELATION_NAME].relation_changed, self._hydra_login_ui_relation_change
        )

    def _on_login_ui_pebble_ready(self, event: WorkloadEvent) -> None:
        """Define and start a workload using the Pebble API."""
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

    def _hydra_login_ui_relation_change(self, event: RelationEvent) -> None:
        self._update_pebble_layer(event)

    def _get_hydra_url(self) -> str:
        try:
            hydra_endpoint = self.hydra_login_ui_provider.get_hydra_endpoint()
            return hydra_endpoint.get("hydra_endpoint", self.config.get("hydra_url"))
        except HydraLoginUIRelationMissingError as err:
            logger.error(str(err))
            self.unit.status = BlockedStatus("Failed to Process updated Hydra API endpoint")
            return self.config.get("hydra_url")

    def _update_login_ui_endpoints_relation_data(self, event: RelationEvent) -> None:
        login_ui_endpoint = (
            self.ingress.url
            if self.ingress.is_ready()
            else f"{self.app.name}.{self.model.name}.svc.cluster.local:{APPLICATION_PORT}",
        )

        logger.info(
            f"Sending endpoints info: identity-platform-login-ui {login_ui_endpoint[0]}"
        )

        self.hydra_login_ui_provider.send_identity_platform_login_ui_endpoint(
            self.app, login_ui_endpoint[0]
        )

    def _on_ingress_ready(self, event: IngressPerAppReadyEvent) -> None:
        if self.unit.is_leader():
            logger.info("This app's public ingress URL: %s", event.url)
        self._update_login_ui_endpoints_relation_data(event)

    def _on_ingress_revoked(self, event: IngressPerAppRevokedEvent) -> None:
        if self.unit.is_leader():
            logger.info("This app no longer has ingress")
        self._update_login_ui_endpoints_relation_data(event)

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
                    "command": "identity_platform_login_ui",
                    "startup": "enabled",
                    "environment": {
                        "HYDRA_ADMIN_URL": self._get_hydra_url(),
                        "KRATOS_PUBLIC_URL": self.config.get("kratos_url"),
                        "PORT": APPLICATION_PORT,
                    },
                }
            },
        }
        return Layer(pebble_layer)


if __name__ == "__main__":  # pragma: nocover
    main(IdentityPlatformLoginUiOperatorCharm)
