# Contributing

## Overview

This document explains the processes and practices recommended for contributing
enhancements to this operator.

- Generally, before developing bugs or enhancements to this charm, you
  should [open an issue](https://github.com/canonical/identity-platform-login-ui-operator/issues)
  explaining your use case.
- If you would like to chat with us about charm development, you can reach
  us
  at [Canonical Mattermost public channel](https://chat.charmhub.io/charmhub/channels/charm-dev)
  or [Discourse](https://discourse.charmhub.io/).
- Familiarising yourself with
  the [Charmed Operator Framework](https://juju.is/docs/sdk) library
  will help you a lot when working on new features or bug fixes.
- All enhancements require review before being merged. Code review typically
  examines
  - code quality
  - test coverage
  - user experience for Juju administrators of this charm.
- Please help us out in ensuring easy to review branches by rebasing your pull
  request branch onto the `main` branch. This also avoids merge commits and
  creates a linear Git commit history.

## Developing

You can use the environments created by `tox` for development. It helps install
`pre-commit`, `mypy` type checker, linting and formatting tools, as well as unit
and integration test dependencies.

```shell
tox devenv
source venv/bin/activate
```

## Testing

```shell
tox -e fmt           # update your code according to linting rules
tox -e lint          # code style
tox -e unit          # unit tests
tox                  # runs 'lint' and 'unit' environments
```

## Building

Build the charm using:

```shell
charmcraft pack
```

## Deploying

```bash
# Create a model
juju add-model dev
# Enable DEBUG logging
juju model-config logging-config="<root>=INFO;unit=DEBUG"
# Deploy identity-platform-login-ui charm
juju deploy ./identity-platform-login-ui-operator_ubuntu*.charm --resource oci-image=$(yq eval '.resources.oci-image.upstream-source' charmcraft.yaml) --trust
```

## Canonical Contributor Agreement

Canonical welcomes contributions to Charmed Identity Platform Login UI. Please
check out our [contributor agreement](https://ubuntu.com/legal/contributors) if
you're interested in contributing to the solution.
