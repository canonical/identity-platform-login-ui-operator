# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

output "app_name" {
  description = "The Juju application name"
  value       = juju_application.application.name
}

output "requires" {
  description = "The Juju integrations that the charm requires"
  value = {
    ingress             = "ingress"
    kratos-info         = "kratos-info"
    hydra-endpoint-info = "hydra-endpoint-info"
    logging             = "logging"
    tracing             = "tracing"
    receive-ca-cert     = "receive-ca-cert"
  }
}

output "provides" {
  description = "The Juju integrations that the charm provides"
  value = {
    ui-endpoint-info  = "ui-endpoint-info"
    metrics-endpoint  = "metrics-endpoint"
    grafana-dashboard = "grafana-dashboard"
  }
}
