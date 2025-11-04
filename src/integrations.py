# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

import json
import logging
from dataclasses import dataclass, field
from typing import Optional
from urllib.parse import urlparse

from charms.hydra.v0.hydra_endpoints import (
    HydraEndpointsRelationDataMissingError,
    HydraEndpointsRelationMissingError,
    HydraEndpointsRequirer,
)
from charms.kratos.v0.kratos_info import KratosInfoRelationDataMissingError, KratosInfoRequirer
from charms.tempo_k8s.v2.tracing import TracingEndpointRequirer
from charms.traefik_k8s.v0.traefik_route import TraefikRouteRequirer
from jinja2 import Template
from yarl import URL

from constants import APPLICATION_PORT as PUBLIC_PORT
from constants import (
    PUBLIC_ROUTE_INTEGRATION_NAME,
)

logger = logging.getLogger(__name__)


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
    feature_flags: Optional[list[str]] = None

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
            feature_flags=info.get("feature_flags", None),
        )


@dataclass(frozen=True, slots=True)
class TracingData:
    """The data source from the tracing integration."""

    is_ready: bool = False
    http_endpoint: str = ""
    grpc_endpoint: str = ""

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


@dataclass(frozen=True, slots=True)
class PublicRouteData:
    """The data source from the public-route integration."""

    url: URL = URL()
    config: dict = field(default_factory=dict)

    @classmethod
    def _external_host(cls, requirer: TraefikRouteRequirer) -> str:
        if not (relation := requirer._charm.model.get_relation(PUBLIC_ROUTE_INTEGRATION_NAME)):
            return
        if not relation.app:
            return
        return relation.data[relation.app].get("external_host", "")

    @classmethod
    def _scheme(cls, requirer: TraefikRouteRequirer) -> str:
        if not (relation := requirer._charm.model.get_relation(PUBLIC_ROUTE_INTEGRATION_NAME)):
            return
        if not relation.app:
            return
        return relation.data[relation.app].get("scheme", "")

    @classmethod
    def load(cls, requirer: TraefikRouteRequirer) -> "PublicRouteData":
        model, app = requirer._charm.model.name, requirer._charm.app.name
        external_host = cls._external_host(requirer)
        scheme = cls._scheme(requirer)

        external_endpoint = f"{scheme}://{external_host}"
        # template could have use PathPrefixRegexp but going for a simple one right now
        with open("templates/public-route.json.j2", "r") as file:
            template = Template(file.read())

        ingress_config = json.loads(
            template.render(
                model=model,
                app=app,
                public_port=PUBLIC_PORT,
                external_host=external_host,
            )
        )

        if not external_host:
            logger.error("External hostname is not set on the ingress provider")
            return cls()

        return cls(
            url=URL(external_endpoint),
            config=ingress_config,
        )

    @property
    def secured(self) -> bool:
        return self.url.scheme == "https"
