# Identity Platform Login UI Operator

[![CharmHub Badge](https://charmhub.io/identity-platform-login-ui-operator/badge.svg)](https://charmhub.io/identity-platform-login-ui-operator)
[![Juju](https://img.shields.io/badge/Juju%20-3.0+-%23E95420)](https://github.com/juju/juju)
[![License](https://img.shields.io/github/license/canonical/identity-platform-login-ui-operator?label=License)](https://github.com/canonical/identity-platform-login-ui-operator/blob/main/LICENSE)

[![Continuous Integration Status](https://github.com/canonical/identity-platform-login-ui-operator/actions/workflows/on_push.yaml/badge.svg?branch=main)](https://github.com/canonical/identity-platform-login-ui-operator/actions?query=branch%3Amain)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)
[![Conventional Commits](https://img.shields.io/badge/Conventional%20Commits-1.0.0-%23FE5196.svg)](https://conventionalcommits.org)

## Description

This repository hosts the Kubernetes Python Operator for Identity Platform Login
UI. For more details,
visit [Identity Platform Login UI](https://github.com/canonical/identity-platform-login-ui).

## Usage

The Identity Platform Login UI Operator may be deployed using with the following
commands:

```shell
juju deploy identity-platform-login-ui-operator
```

## Integrations

### Hydra

This charm offers integration
with [hydra-operator](https://github.com/canonical/hydra-operator). To integrate
them, run:

```shell
juju integrate hydra:hydra-endpoint-info identity-platform-login-ui-operator:hydra-endpoint-info
juju integrate hydra:ui-endpoint-info identity-platform-login-ui-operator:ui-endpoint-info
```

### Kratos

This charm offers integration
with [kratos-operator](https://github.com/canonical/kratos-operator). To
integrate them, run:

```shell
juju integrate kratos:kratos-info identity-platform-login-ui-operator:kratos-info
juju integrate kratos:ui-endpoint-info identity-platform-login-ui-operator:ui-endpoint-info
```

### Ingress

The Identity Platform Login UI Operator offers integration with
the [traefik-k8s-operator](https://github.com/canonical/traefik-k8s-operator)
for ingress.

If you have a traefik deployed you can provide ingress with the following
command:

```shell
juju integrate traefik-admin identity-platform-login-ui-operator:ingress
```

## OCI Images

The image used by this charm is hosted
on [GitHub container registry](ghcr.io/canonical/identity-platform-login-ui) and
maintained by Canonical Identity Team.

### Security

Security issues in IAM stack can be reported
through [LaunchPad](https://wiki.ubuntu.com/DebuggingSecurity#How%20to%20File).
Please do not file GitHub issues about security issues.

## Contributing

Please see the [Juju SDK docs](https://juju.is/docs/sdk) for guidelines on
enhancements to this charm following best practice guidelines,
and [CONTRIBUTING.md](https://github.com/canonical/identity-platform-login-ui-operator)
for developer guidance.
