#!/usr/bin/env python3
# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.
#
# Learn more at: https://juju.is/docs/sdk

"""A Juju charm for Identity Platform Login UI."""
import logging
from typing import Optional

from charms.hydra.v0.hydra_endpoints import (
    HydraEndpointsRelationDataMissingError,
    HydraEndpointsRequirer,
)
from charms.identity_platform_login_ui_operator.v0.login_ui_endpoints import (
    LoginUIEndpointsProvider,
)
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
from ops.charm import CharmBase, ConfigChangedEvent, HookEvent, RelationEvent, WorkloadEvent
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
        self._hydra_relation_name = "endpoint-info"
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
        self.hydra_endpoints = HydraEndpointsRequirer(
            self, relation_name=self._hydra_relation_name
        )
        self.endpoints_provider = LoginUIEndpointsProvider(self)

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
        self._update_pebble_layer(event)
        self._update_login_ui_endpoint_relation_data(event)

    def _on_ingress_revoked(self, event: IngressPerAppRevokedEvent) -> None:
        if self.unit.is_leader():
            logger.info("This app no longer has ingress")
        self._update_pebble_layer(event)
        self._update_login_ui_endpoint_relation_data(event)

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
                        "HYDRA_ADMIN_URL": self._get_hydra_endpoint_info(),
                        "KRATOS_PUBLIC_URL": self._get_kratos_endpoint_info(),
                        "PORT": APPLICATION_PORT,
                    },
                }
            },
        }
        return Layer(pebble_layer)

    def _get_kratos_endpoint_info(self) -> Optional[str]:
        if self.model.relations[self._kratos_relation_name]:
            try:
                kratos_endpoints = self.kratos_endpoints.get_kratos_endpoints()
                kratos_public_url = kratos_endpoints["public_endpoint"]
                return kratos_public_url
            except KratosEndpointsRelationDataMissingError:
                logger.info("No kratos-endpoint-info relation data found")
                return None
        return None

    def _update_login_ui_endpoint_relation_data(self, event: RelationEvent) -> None:
        endpoint = (self.ingress.url if self.ingress.is_ready() else "")

        logger.info(f"Sending login ui endpoint info: endpoint - {endpoint[0]}")

        self.endpoint_provider.send_endpoints_relation_data(endpoint[0])

    def _get_hydra_endpoint_info(self) -> Optional[str]:
        if self.model.relations[self._hydra_relation_name]:
            try:
                hydra_endpoints = self.hydra_endpoints.get_hydra_endpoints()
                hydra_url = hydra_endpoints["public_endpoint"]
                return hydra_url
            except HydraEndpointsRelationDataMissingError:
                logger.info("No hydra endpoint-info relation data found")
                return None
        return None


if __name__ == "__main__":  # pragma: nocover
    main(IdentityPlatformLoginUiOperatorCharm)
