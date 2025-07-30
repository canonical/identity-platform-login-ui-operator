# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

import re

from ops import Container, Unit
from ops.pebble import Error, Layer, LayerDict

from constants import (
    APPLICATION_NAME,
    APPLICATION_PORT,
    WORKLOAD_CONTAINER_NAME,
    WORKLOAD_RUN_COMMAND,
)
from exceptions import PebbleServiceError
from integrations import HydraEndpointData, KratosInfoData, TracingData


class WorkloadService:
    """Workload service abstraction running in a Juju unit."""

    def __init__(self, unit: Unit) -> None:
        self._version = ""

        self._unit: Unit = unit
        self._container: Container = unit.get_container(WORKLOAD_CONTAINER_NAME)

    @property
    def version(self) -> str:
        cmd = [APPLICATION_NAME, "version"]
        try:
            process = self._container.exec(cmd)
            stdout, _ = process.wait_output()
        except Error:
            return ""

        out_re = r"App Version:\s*(.+)\s*$"
        versions = re.search(out_re, stdout)
        if versions:
            return versions[1]

        return ""

    def set_version(self) -> None:
        if version := self.version:
            self._unit.set_workload_version(version)


class PebbleService:
    def __init__(self, unit):
        self._unit: Unit = unit
        self._container: Container = unit.get_container(WORKLOAD_CONTAINER_NAME)

    def _restart_service(self, restart: bool = False) -> None:
        if restart:
            self._container.restart(WORKLOAD_CONTAINER_NAME)
        elif not self._container.get_service(WORKLOAD_CONTAINER_NAME).is_running():
            self._container.start(WORKLOAD_CONTAINER_NAME)
        else:
            self._container.replan()

    def can_connect(self) -> bool:
        return self._container.can_connect()

    def render_pebble_layer(
        self,
        domain_url: str,
        cookie_encryption_key: str,
        log_level: str,
        support_email: str,
        hydra_endpoint: HydraEndpointData,
        kratos_info: KratosInfoData,
        tracing_data: TracingData,
    ) -> Layer:
        container = {
            "override": "replace",
            "summary": "identity platform login ui",
            "command": WORKLOAD_RUN_COMMAND,
            "startup": "disabled",
            "environment": {
                "HYDRA_ADMIN_URL": hydra_endpoint.admin_endpoint,
                "KRATOS_PUBLIC_URL": kratos_info.public_endpoint,
                "KRATOS_ADMIN_URL": kratos_info.admin_endpoint,
                "PORT": str(APPLICATION_PORT),
                "BASE_URL": domain_url,
                "COOKIES_ENCRYPTION_KEY": cookie_encryption_key,
                "TRACING_ENABLED": False,
                "AUTHORIZATION_ENABLED": False,
                "LOG_LEVEL": log_level,
                "SUPPORT_EMAIL": support_email,
                "DEBUG": log_level == "DEBUG",
            },
        }

        if kratos_info.is_ready:
            container["environment"]["MFA_ENABLED"] = kratos_info.mfa_enabled
            container["environment"]["OIDC_WEBAUTHN_SEQUENCING_ENABLED"] = (
                kratos_info.oidc_webauthn_sequencing_enabled
            )

        if tracing_data.is_ready:
            container["environment"]["OTEL_HTTP_ENDPOINT"] = tracing_data.http_endpoint
            container["environment"]["OTEL_GRPC_ENDPOINT"] = tracing_data.grpc_endpoint
            container["environment"]["TRACING_ENABLED"] = True

        # Define Pebble layer configuration
        pebble_layer: LayerDict = {
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

    def plan(self, layer: Layer) -> None:
        self._container.add_layer(WORKLOAD_CONTAINER_NAME, layer, combine=True)

        try:
            self._restart_service()
        except Exception as e:
            raise PebbleServiceError(f"Pebble failed to restart the workload service. Error: {e}")
