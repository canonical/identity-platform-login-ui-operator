# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Constants for the charm."""

# Charm constants
WORKLOAD_CONTAINER_NAME = "login-ui"

# Application constants
APPLICATION_NAME = f"identity-platform-{WORKLOAD_CONTAINER_NAME}"
APPLICATION_PORT = 8080
WORKLOAD_RUN_COMMAND = f"/usr/bin/{APPLICATION_NAME} serve"
COOKIES_KEY = "cookies_key"

# Integrations constants
PEER = APPLICATION_NAME
CERTIFICATE_TRANSFER_NAME = "receive-ca-cert"
TRACING_RELATION_NAME = "tracing"
GRAFANA_RELATION_NAME = "grafana-dashboard"
LOGGING_RELATION_NAME = "logging"
PROMETHEUS_RELATION_NAME = "metrics-endpoint"
KRATOS_RELATION_NAME = "kratos-info"
HYDRA_RELATION_NAME = "hydra-endpoint-info"
INGRESS_RELATION_NAME = "ingress"
