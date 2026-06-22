# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

import logging
from dataclasses import dataclass, field
from typing import Optional
from urllib.parse import urlparse

from charmlibs.interfaces.istio_ingress_route import (
    BackendRef,
    HTTPPathMatch,
    HTTPPathMatchType,
    HTTPRoute,
    HTTPRouteMatch,
    IstioIngressRouteConfig,
    IstioIngressRouteRequirer,
    Listener,
    PathModifier,
    PathModifierType,
    ProtocolType,
    URLRewriteFilter,
    URLRewriteSpec,
)
from charms.hydra.v0.hydra_endpoints import (
    HydraEndpointsRelationDataMissingError,
    HydraEndpointsRelationMissingError,
    HydraEndpointsRequirer,
)
from charms.kratos.v0.kratos_info import KratosInfoRelationDataMissingError, KratosInfoRequirer
from charms.tempo_k8s.v2.tracing import TracingEndpointRequirer
from charms.tenant_service.v0.tenant_service_info import TenantServiceInfoRequirer
from yarl import URL

from constants import APPLICATION_PORT, INGRESS_HTTP_PORT, INGRESS_HTTPS_PORT

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
    verification_enabled: bool = False
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
            verification_enabled=info.get("verification_enabled"),
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

    url: URL = field(default_factory=URL)
    config: IstioIngressRouteConfig = field(
        default_factory=lambda: IstioIngressRouteConfig(model="")
    )

    @classmethod
    def load(cls, requirer: IstioIngressRouteRequirer) -> "PublicRouteData":
        """Build PublicRouteData from the IstioIngressRouteRequirer."""
        external_host = requirer.external_host
        if not external_host:
            logger.debug("External hostname is not yet set by the istio ingress provider")
            return cls()

        scheme = "https" if requirer.tls_enabled else "http"
        app_name = requirer._charm.app.name
        model_name = requirer._charm.model.name
        backend = BackendRef(service=app_name, port=APPLICATION_PORT)
        ingress_port = INGRESS_HTTPS_PORT if requirer.tls_enabled else INGRESS_HTTP_PORT
        listener = Listener(port=ingress_port, protocol=ProtocolType.HTTP)

        http_routes = [
            HTTPRoute(
                name="self-service",
                listener=listener,
                matches=[
                    HTTPRouteMatch(
                        path=HTTPPathMatch(
                            type=HTTPPathMatchType.PathPrefix, value="/self-service"
                        )
                    )
                ],
                filters=[
                    URLRewriteFilter(
                        urlRewrite=URLRewriteSpec(
                            path=PathModifier(
                                type=PathModifierType.ReplacePrefixMatch,
                                value="/api/kratos/self-service",
                            )
                        )
                    )
                ],
                backends=[backend],
            ),
            HTTPRoute(
                name="api-and-ui",
                listener=listener,
                matches=[
                    HTTPRouteMatch(
                        path=HTTPPathMatch(type=HTTPPathMatchType.Exact, value="/api/device")
                    ),
                    HTTPRouteMatch(
                        path=HTTPPathMatch(type=HTTPPathMatchType.Exact, value="/api/consent")
                    ),
                    HTTPRouteMatch(
                        path=HTTPPathMatch(
                            type=HTTPPathMatchType.Exact, value="/api/v0/app-config"
                        )
                    ),
                    HTTPRouteMatch(
                        path=HTTPPathMatch(
                            type=HTTPPathMatchType.Exact, value="/api/v0/tenants/resolve"
                        )
                    ),
                    HTTPRouteMatch(
                        path=HTTPPathMatch(
                            type=HTTPPathMatchType.Exact, value="/api/v0/tenants"
                        )
                    ),
                    HTTPRouteMatch(
                        path=HTTPPathMatch(
                            type=HTTPPathMatchType.Exact, value="/api/v0/auth/tenant"
                        )
                    ),
                    HTTPRouteMatch(
                        path=HTTPPathMatch(type=HTTPPathMatchType.PathPrefix, value="/ui")
                    ),
                ],
                backends=[backend],
            ),
        ]

        config = IstioIngressRouteConfig(
            model=model_name,
            listeners=[listener],
            http_routes=http_routes,
        )

        return cls(
            url=URL(f"{scheme}://{external_host}"),
            config=config,
        )

    @property
    def secured(self) -> bool:
        """Whether the public URL uses HTTPS."""
        return self.url.scheme == "https"


@dataclass(frozen=True, slots=True)
class TenantServiceInfoData:
    """The data source from the tenant-service-info integration."""

    service_url: str = ""
    grpc_url: str = ""
    is_ready: bool = False

    @classmethod
    def load(cls, requirer: TenantServiceInfoRequirer) -> "TenantServiceInfoData":
        """Load tenant-service info from the relation."""
        if not requirer.is_ready():
            return cls()
        service_url = requirer.get_service_url() or ""
        grpc_url = requirer.get_grpc_url() or ""

        is_ready = False
        if service_url:
            parsed = URL(service_url)
            is_ready = parsed.scheme in ("http", "https") and bool(parsed.host)

        return cls(service_url=service_url, grpc_url=grpc_url, is_ready=is_ready)
