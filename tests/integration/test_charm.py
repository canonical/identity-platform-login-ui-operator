#!/usr/bin/env python3
# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

import logging
from pathlib import Path

import jubilant
import pytest
import requests
from conftest import integrate_dependencies
from integration.constants import (
    LOGIN_UI_APP,
    LOGIN_UI_IMAGE,
    PUBLIC_INGRESS_DOMAIN,
    TRAEFIK_CHARM,
    TRAEFIK_PUBLIC_APP,
)
from integration.utils import wait_for_active_idle

logger = logging.getLogger(__name__)


@pytest.mark.skip_if_deployed
def test_build_and_deploy(juju: jubilant.Juju, local_charm: Path) -> None:
    """Build the charm-under-test and deploy it together with related charms.

    Assert on the unit status before any relations/configurations take place.
    """
    # Deploy dependencies
    juju.deploy(
        TRAEFIK_CHARM,
        app=TRAEFIK_PUBLIC_APP,
        channel="latest/edge",  # using edge to take advantage of the raw args in traefik route
        config={"external_hostname": PUBLIC_INGRESS_DOMAIN},
        trust=True,
    )
    # juju.integrate(f"{TRAEFIK_PUBLIC_APP}:certificates", f"{CA_APP}:certificates")

    juju.deploy(
        str(local_charm),
        app=LOGIN_UI_APP,
        resources={"oci-image": LOGIN_UI_IMAGE},
        base="ubuntu@22.04",
        trust=True,
    )

    # Integrate with dependencies
    integrate_dependencies(juju)

    wait_for_active_idle(juju, apps=[LOGIN_UI_APP], timeout=5 * 60)


def test_ingress_relation(juju: jubilant.Juju) -> None:
    """Test that the ingress relation is properly set up."""
    wait_for_active_idle(
        juju,
        apps=[TRAEFIK_PUBLIC_APP],
        timeout=5 * 60,
    )


def test_has_ingress(juju: jubilant.Juju, public_address: str) -> None:
    """Test that the login UI is accessible via ingress."""
    # Get the traefik address and try to reach identity-platform-login-ui
    resp = requests.get(f"http://{public_address}/ui/login")

    assert resp.status_code == 200
