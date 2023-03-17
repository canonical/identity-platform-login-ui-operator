#!/usr/bin/env python3
# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.
#
# Learn more at: https://juju.is/docs/sdk

"""A Juju charm for Identity Platform Login UI."""
import logging

from charms.traefik_k8s.v1.ingress import (
    IngressPerAppReadyEvent,
    IngressPerAppRequirer,
    IngressPerAppRevokedEvent,
)
from ops.charm import CharmBase, ConfigChangedEvent, HookEvent, WorkloadEvent
from ops.main import main
from ops.model import (ActiveStatus,
                       BlockedStatus,
                       MaintenanceStatus,
                       ModelError,
                       WaitingStatus)
from ops.pebble import ChangeError, Layer

logger = logging.getLogger(__name__)


class IdentityPlatformLoginUiOperatorCharm(CharmBase):
    """Charmed Identity Platform Login UI."""

    def __init__(self, *args):
        """Initialize Charm."""
        super().__init__(*args)
        self._container_name = "login_ui"
        self._container = self.unit.get_container(self._container_name)
        """New vars should come here"""

        self.unit.open_port("tcp", int(self.config.get("port")))
        self.ingress = IngressPerAppRequirer(
            self,
            relation_name="ingress",
            port=self.config.get("port"),
            strip_prefix=True,
        )

        self.framework.observe(self.on.login_ui_pebble_ready,
                               self._on_login_ui_pebble_ready)
        self.framework.observe(self.on.config_changed,
                               self._on_config_changed)
        self.framework.observe(self.ingress.on.ready,
                               self._on_ingress_ready)
        self.framework.observe(self.ingress.on.revoked,
                               self._on_ingress_revoked)

    def _on_login_ui_pebble_ready(self, event: WorkloadEvent) -> None:
        """Define and start a workload using the Pebble API."""
        self._handle_status_update_config(event)

    def _on_config_changed(self, event: ConfigChangedEvent) -> None:
        """Handle changed configuration."""
        self._handle_status_update_config(event)

    def _handle_status_update_config(self, event: HookEvent) -> None:
        if not self._container.can_connect():
            event.defer()
            logger.info("Cannot connect to Login_UI container. Deferring the event.")  # noqa:E501
            self.unit.status = WaitingStatus("Waiting to connect to Login_UI container")  # noqa:E501
            return

        self.unit.status = MaintenanceStatus("Configuration in progress")

        self._container.add_layer(self._container_name,
                                  self._login_ui_layer, combine=True)
        logger.info("Pebble plan updated with new configuration, replanning")
        try:
            self._container.replan()
        except ChangeError as err:
            logger.error(str(err))
            self.unit.status = BlockedStatus("Failed to replan, please consult the logs")  # noqa:E501
            return

        self.unit.status = ActiveStatus()

    def _on_ingress_ready(self, event: IngressPerAppReadyEvent) -> None:
        if self.unit.is_leader():
            logger.info("This app's public ingress URL: %s", event.url)

    def _on_ingress_revoked(self, event: IngressPerAppRevokedEvent) -> None:
        if self.unit.is_leader():
            logger.info("This app no longer has ingress")

    def _fetch_endpoint(self) -> str:
        port = self.config.get("port")
        endpoint = (
            self.ingress.url
            if self.ingress.is_ready()
            else f"{self.app.name}.{self.model.name}.svc.cluster.local:{port}",
        )

        logger.info(f"Sending endpoints info: {endpoint[0]}")
        return endpoint[0]

    @property
    def _login_ui_layer(self) -> Layer:
        # Define an initial Pebble layer configuration
        pebble_layer = {
            "summary": "login_ui layer",
            "description": "pebble config layer for identity platform login ui",  # noqa:E501
            "services": {
                self._container_name: {
                    "override": "replace",
                    "summary": "identity platform login ui",
                    "command": "/id/identity_platform_login_ui",
                    "startup": "enabled",
                    "environment": {
                        "HYDRA_ADMIN_URL": self.config.get("hydra_url"),
                        "KRATOS_PUBLIC_URL": self.config.get("kratos_url"),
                        "PORT": self.config.get("port"),
                    },
                }
                # version, health and readiness checks will come here, once they're supported in login_ui  # noqa:E501
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
