#!/usr/bin/env python3
# Copyright 2023 nikos
# See LICENSE file for licensing details.
#
# Learn more at: https://juju.is/docs/sdk

import logging

from charms.traefik_k8s.v1.ingress import (
    IngressPerAppRequirer,
)
from charms.observability_libs.v0.kubernetes_service_patch import KubernetesServicePatch
from ops.charm import CharmBase
from ops.main import main
from ops.model import ActiveStatus, MaintenanceStatus

# Log messages can be retrieved using juju debug-log
logger = logging.getLogger(__name__)

VALID_LOG_LEVELS = ["info", "debug", "warning", "error", "critical"]


class KratosUiOperatorCharm(CharmBase):
    """Charm the service."""

    def __init__(self, *args):
        super().__init__(*args)
        self._container_name = "kratos-ui"
        self.service_patcher = KubernetesServicePatch(
            self, [("api", 3000)]
        )
        self.ingress = IngressPerAppRequirer(
            self,
            relation_name="ingress",
            port=3000,
            strip_prefix=True,
        )

        self.framework.observe(self.on.kratos_ui_pebble_ready, self._on_kratos_ui_pebble_ready)
        self.framework.observe(self.on.config_changed, self._on_config_changed)
        self.framework.observe(self.ingress.on.ready, self._on_ingress_ready)

    @property
    def _container(self):
        return self.unit.get_container(self._container_name)

    def _on_kratos_ui_pebble_ready(self, event):
        """Define and start a workload using the Pebble API.
        """
        self._container.add_layer("kratos_ui", self._pebble_layer, combine=True)
        self._container.replan()
        self.unit.status = ActiveStatus()

    def _on_config_changed(self, event):
        """Handle changed configuration.
        """
        # Fetch the new config value
        log_level = self.model.config["log-level"].lower()

        self.unit.status = MaintenanceStatus("Applying configuration")
        self._on_kratos_ui_pebble_ready(None)

    @property
    def _pebble_layer(self):
        """Return a dictionary representing a Pebble layer."""
        return {
            "summary": "kratos ui layer",
            "description": "pebble config layer for kratos_ui",
            "services": {
                "kratos_ui": {
                    "override": "replace",
                    "summary": "kratos ui",
                    "command": "npm run dev",
                    "startup": "enabled",
                    "environment": {
                        "ORY_SDK_URL": self.config["sdk_url"]
                    },
                },
            },
        }

    def _on_ingress_ready(self, event) -> None:
        if self.unit.is_leader():
            logger.info("This app's public ingress URL: %s", event.url)


if __name__ == "__main__":  # pragma: nocover
    main(KratosUiOperatorCharm)
