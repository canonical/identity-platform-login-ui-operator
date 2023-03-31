# Identity Platform Login UI Operator

## Description

This repository hosts the Kubernetes Python Operator for Identity Platform Login UI.
For more details, visit [Identity Platform Login UI](https://github.com/canonical/identity-platform-login-ui).

## Usage

The Identity Platform Login UI Operator may be deployed using with the following commands:

```console
juju deploy identity-platform-login-ui-operator
```

## Interacting with Kratos and Hydra

To set the Ory Kratos endpoint to the UI server, do:

```console
juju relate identity-platform-login-ui-operator kratos
```

To set the Ory Hydra endpoint to the UI server, do:

```console
juju relate identity-platform-login-ui-operator hydra
```

To set the UI server's endpoint to Hydra and Kratos, do:

```console
juju relate hydra identity-platform-login-ui-operator
juju relate kratos identity-platform-login-ui-operator
```

### Ingress

The Identity Platform Login UI Operator offers integration with the [traefik-k8s-operator](https://github.com/canonical/traefik-k8s-operator) for ingress.

If you have a traefik deployed you can provide ingress with the following command:
```console
juju relate traefik-admin identity-platform-login-ui-operator:ingress
```

## OCI Images

The image used by this charm is hosted on [Github container registry](ghcr.io/canonical/identity-platform-login-ui) and maintained by Canonical Identity Team.

### Security
Security issues in IAM stack can be reported through [LaunchPad](https://wiki.ubuntu.com/DebuggingSecurity#How%20to%20File). Please do not file GitHub issues about security issues.

## Contributing

Please see the [Juju SDK docs](https://juju.is/docs/sdk) for guidelines on enhancements to this charm following best practice guidelines, and [CONTRIBUTING.md](https://github.com/canonical/identity-platform-login-ui-operator) for developer guidance.