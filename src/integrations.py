# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

import logging
from dataclasses import dataclass
from typing import Mapping, TypeAlias, Union
from urllib.parse import urlparse

from charms.hydra.v0.hydra_endpoints import (
    HydraEndpointsRelationDataMissingError,
    HydraEndpointsRelationMissingError,
    HydraEndpointsRequirer,
)
from charms.kratos.v0.kratos_info import KratosInfoRelationDataMissingError, KratosInfoRequirer
from charms.tempo_k8s.v2.tracing import TracingEndpointRequirer
from charms.traefik_k8s.v2.ingress import IngressPerAppRequirer
from httpcore import URL

from config import ServiceConfigs

EnvVars: TypeAlias = Mapping[str, Union[str, bool]]

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class PublicIngressData:
    """The data source from the public-ingress integration."""

    url: URL = URL()

    def to_service_configs(self) -> ServiceConfigs:
        return {"public_url": str(self.url)}

    @classmethod
    def load(cls, requirer: IngressPerAppRequirer) -> "PublicIngressData":
        return cls(url=URL(requirer.url)) if requirer.is_ready() else cls()  # type: ignore[arg-type]


@dataclass(frozen=True, slots=True)
class HydraEndpointData:
    """The data source from the hydra integration."""

    admin_endpoint: str = ""

    @classmethod
    def load(cls, requirer: HydraEndpointsRequirer) -> "HydraEndpointData":
        hydra_url = ""
        try:
            hydra_endpoints = requirer.get_hydra_endpoints()
            hydra_url = hydra_endpoints["admin_endpoint"]
        except HydraEndpointsRelationDataMissingError:
            logger.info("No hydra-endpoint-info relation data found")
        except HydraEndpointsRelationMissingError:
            logger.info("No hydra-endpoint-info relation found")

        return cls(admin_endpoint=hydra_url)


@dataclass(frozen=True, slots=True)
class KratosInfoData:
    """The data source from the kratos integration."""

    public_endpoint: str = ""
    admin_endpoint: str = ""
    mfa_enabled: bool = False
    oidc_webauthn_sequencing_enabled: bool = False
    is_ready: bool = False

    @classmethod
    def load(cls, requirer: KratosInfoRequirer) -> "KratosInfoData":
        if not requirer.is_ready():
            return cls()

        info = {}
        try:
            info = requirer.get_kratos_info()
        except KratosInfoRelationDataMissingError:
            logger.info("No kratos-info relation data found")

        return cls(
            public_endpoint=info.get("public_endpoint"),
            admin_endpoint=info.get("admin_endpoint"),
            mfa_enabled=info.get("mfa_enabled"),
            oidc_webauthn_sequencing_enabled=info.get("oidc_webauthn_sequencing_enabled"),
            is_ready=requirer.is_ready(),
        )


@dataclass(frozen=True, slots=True)
class TracingData:
    """The data source from the tracing integration."""

    is_ready: bool = False
    http_endpoint: str = ""
    grpc_endpoint: str = ""

    def to_env_vars(self) -> EnvVars:
        if not self.is_ready:
            return {}

        return {
            "TRACING_ENABLED": True,
            "TRACING_PROVIDER": "otel",
            "TRACING_PROVIDERS_OTLP_SERVER_URL": self.http_endpoint,
            "TRACING_PROVIDERS_OTLP_INSECURE": "true",
            "TRACING_PROVIDERS_OTLP_SAMPLING_SAMPLING_RATIO": "1.0",
        }

    @classmethod
    def load(cls, requirer: TracingEndpointRequirer) -> "TracingData":
        if not (is_ready := requirer.is_ready()):
            return cls()

        http_endpoint = urlparse(requirer.get_endpoint("otlp_http"))
        grpc_endpoint = urlparse(requirer.get_endpoint("otlp_grpc"))

        return cls(
            is_ready=is_ready,
            http_endpoint=http_endpoint.geturl(),
            grpc_endpoint=grpc_endpoint.geturl(),
        )
