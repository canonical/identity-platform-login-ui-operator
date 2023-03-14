#!/usr/bin/env python3
# Copyright 2023 bence
# See LICENSE file for licensing details.
#
# Learn more at: https://juju.is/docs/sdk

import logging
from charms.observability_libs.v0.kubernetes_service_patch import KubernetesServicePatch
from charms.traefik_k8s.v1.ingress import (
    IngressPerAppReadyEvent,
    IngressPerAppRequirer,
    IngressPerAppRevokedEvent,
)
from ops.charm import (
    CharmBase,
    ConfigChangedEvent,
    HookEvent,
    WorkloadEvent,
)
from ops.main import main
from ops.model import ActiveStatus, BlockedStatus, MaintenanceStatus, ModelError, WaitingStatus
from ops.pebble import ChangeError, Layer

logger = logging.getLogger(__name__)


class IdentityPlatformLoginUiOperatorCharm(CharmBase):
    """Charm the service."""

    def __init__(self, *args):
        super().__init__(*args)
        self._container_name = "login_ui"
        self._container = self.unit.get_container(self._container_name)
        """Init attributes"""
        self._hydra_url = None
        self._kratos_url = None
        self._port = None
        self._reconfigure()
        """New vars should come here"""

        self.service_patcher = KubernetesServicePatch(
            self, [("Identity-Platform-Login-UI", self._port)]
        )
        self.public_ingress = IngressPerAppRequirer(
            self,
            relation_name="public-ingress",
            port=self._port,
            strip_prefix=True,
        )

        self.framework.observe(self.on.login_ui_pebble_ready, self._on_login_ui_pebble_ready)
        self.framework.observe(self.on.config_changed, self._on_config_changed)
        self.framework.observe(self.public_ingress.on.ready, self._on_public_ingress_ready)
        self.framework.observe(self.public_ingress.on.revoked, self._on_ingress_revoked)

    def _on_login_ui_pebble_ready(self, event: WorkloadEvent) -> None:
        """Define and start a workload using the Pebble API.
        """
        self._handle_status_update_config(event)

    def _on_config_changed(self, event: ConfigChangedEvent) -> None:
        """Handle changed configuration.
        """
        self._handle_status_update_config(event)

    def _reconfigure(self) -> None:
        self._hydra_url = self.config.get('hydra_url', '')
        logger.info("New value of hydra_url %s", self._hydra_url)
        self._kratos_url = self.config.get('kratos_url', '')
        logger.info("New value of kratos_url %s", self._kratos_url)
        self._port = self.config.get('port', '')
        logger.info("New value of port %s", self._port)

    def _handle_status_update_config(self, event: HookEvent) -> None:
        if not self._container.can_connect():
            event.defer()
            logger.info("Cannot connect to Login_UI container. Deferring the event.")
            self.unit.status = WaitingStatus("Waiting to connect to Login_UI container")
            return

        self.unit.status = MaintenanceStatus("Configuration in progress")

        self._reconfigure()
        current_layer = self._container.get_plan()
        new_layer = self._login_ui_layer
        if current_layer.services != new_layer.services:
            self._container.add_layer(self._container_name, self._login_ui_layer, combine=True)
            logger.info("Pebble plan updated with new configuration, replanning")
            try:
                self._container.replan()
            except ChangeError as err:
                logger.error(str(err))
                self.unit.status = BlockedStatus("Failed to replan, please consult the logs")
                return

        if not self._service_is_created:
            event.defer()
            self.unit.status = WaitingStatus("Waiting for Login_UI service")
            logger.info("Login_UI service is absent. Deferring the event.")
            return

        self._container.restart(self._container_name)
        self.unit.status = ActiveStatus()

    def _on_public_ingress_ready(self, event: IngressPerAppReadyEvent) -> None:
        if self.unit.is_leader():
            logger.info("This app's public ingress URL: %s", event.url)

        self._handle_status_update_config(event)

    def _on_ingress_revoked(self, event: IngressPerAppRevokedEvent) -> None:
        if self.unit.is_leader():
            logger.info("This app no longer has ingress")

        self._handle_status_update_config(event)
    
    def _fetch_endpoint(self) -> str:
        endpoint = (
            self.public_ingress.url
            if self.public_ingress.is_ready()
            else f"{self.app.name}.{self.model.name}.svc.cluster.local:{self._port}",
        )

        logger.info(
            f"Sending endpoints info: {endpoint[0]}"
        )
        return endpoint[0]

    @property
    def _login_ui_layer(self) -> Layer:
        # Define an initial Pebble layer configuration
        pebble_layer = {
            "summary": "login_ui layer",
            "description": "pebble config layer for identity platform login ui",
            "services": {
                self._container_name: {
                    "override": "replace",
                    "summary": "identity platform login ui",
                    "command": "/id/identity_platform_login_ui",
                    "startup": "enabled",
                    "environment": {
                        'HYDRA_ADMIN_URL': self._hydra_url,
                        'KRATOS_PUBLIC_URL': self._kratos_url,
                        'PORT': self._port
                    },
                }
                #version, health and readiness checks will come here, once they're supported in login_ui
            },
        }
        return Layer(pebble_layer)

    def _service_is_created(self) -> bool:
        try:
            self._container.get_service(self._container_name)
        except (ModelError, RuntimeError):
            return False
        return True


if __name__ == "__main__":  # pragma: nocover
    main(IdentityPlatformLoginUiOperatorCharm)
