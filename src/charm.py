#!/usr/bin/env python3
# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.
#
# Learn more at: https://juju.is/docs/sdk

"""A Juju charm for Identity Platform Login UI."""
import logging
from typing import Optional

from charms.kratos.v0.kratos_endpoints import (
    KratosEndpointsRelationDataMissingError,
    KratosEndpointsRequirer,
)
from charms.observability_libs.v0.kubernetes_service_patch import KubernetesServicePatch
from charms.traefik_k8s.v1.ingress import (
    IngressPerAppReadyEvent,
    IngressPerAppRequirer,
    IngressPerAppRevokedEvent,
)
from ops.charm import CharmBase, ConfigChangedEvent, HookEvent, WorkloadEvent
from ops.main import main
from ops.model import ActiveStatus, BlockedStatus, MaintenanceStatus, WaitingStatus
from ops.pebble import ChangeError, Layer

APPLICATION_PORT = "8080"


logger = logging.getLogger(__name__)


class IdentityPlatformLoginUiOperatorCharm(CharmBase):
    """Charmed Identity Platform Login UI."""

    def __init__(self, *args):
        """Initialize Charm."""
        super().__init__(*args)
        self._container_name = "login-ui"
        self._container = self.unit.get_container(self._container_name)
        self._kratos_relation_name = "kratos-endpoint-info"

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

        self.framework.observe(self.on.login_ui_pebble_ready, self._on_login_ui_pebble_ready)
        self.framework.observe(self.on.config_changed, self._on_config_changed)
        self.framework.observe(
            self.on[self._kratos_relation_name].relation_changed, self._update_pebble_layer
        )
        self.framework.observe(self.ingress.on.ready, self._on_ingress_ready)
        self.framework.observe(self.ingress.on.revoked, self._on_ingress_revoked)

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

    def _on_ingress_ready(self, event: IngressPerAppReadyEvent) -> None:
        if self.unit.is_leader():
            logger.info("This app's public ingress URL: %s", event.url)

    def _on_ingress_revoked(self, event: IngressPerAppRevokedEvent) -> None:
        if self.unit.is_leader():
            logger.info("This app no longer has ingress")

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
                        "HYDRA_ADMIN_URL": self.config.get("hydra_url"),
                        "KRATOS_PUBLIC_URL": self._get_kratos_endpoint_info(),
                        "PORT": APPLICATION_PORT,
                    },
                }
            },
        }
        return Layer(pebble_layer)

    def _get_kratos_endpoint_info(self) -> Optional[str]:
        kratos_public_url = ""
        if self.model.relations[self._kratos_relation_name]:
            try:
                kratos_endpoints = self.kratos_endpoints.get_kratos_endpoints()
                kratos_public_url = kratos_endpoints["public_endpoint"]
            except KratosEndpointsRelationDataMissingError:
                logger.info("No kratos-endpoint-info relation data found")

        return kratos_public_url


if __name__ == "__main__":  # pragma: nocover
    main(IdentityPlatformLoginUiOperatorCharm)
