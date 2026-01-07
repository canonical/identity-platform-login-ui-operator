#!/usr/bin/env python3
# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

import logging
from pathlib import Path
from typing import Callable

import jubilant
import pytest
import requests
from integration.conftest import integrate_dependencies
from integration.constants import (
    APP_NAME,
    LOGIN_UI_IMAGE,
    PUBLIC_INGRESS_DOMAIN,
    PUBLIC_ROUTE_INTEGRATION_NAME,
    TRAEFIK_CHARM,
    TRAEFIK_PUBLIC_APP,
)
from integration.utils import (
    StatusPredicate,
    all_active,
    and_,
    any_error,
    get_unit_address,
    is_active,
    remove_integration,
    unit_number,
)

logger = logging.getLogger(__name__)


@pytest.mark.setup
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

    juju.deploy(
        str(local_charm),
        app=APP_NAME,
        resources={"oci-image": LOGIN_UI_IMAGE},
        base="ubuntu@22.04",
        trust=True,
    )

    # Integrate with dependencies
    integrate_dependencies(juju)

    juju.wait(
        ready=all_active(APP_NAME, TRAEFIK_PUBLIC_APP),
        error=any_error(APP_NAME, TRAEFIK_PUBLIC_APP),
        timeout=10 * 60,
    )


def test_app_health(
    juju: jubilant.Juju,
    http_client: requests.Session,
) -> None:
    public_address = get_unit_address(juju, app_name=APP_NAME, unit_num=0)

    resp = http_client.get(f"http://{public_address}:8080/api/v0/status")

    resp.raise_for_status()


def test_has_ingress(
    juju: jubilant.Juju, public_address: str, http_client: requests.Session
) -> None:
    """Test that the login UI is accessible via ingress."""
    # Get the traefik address and try to reach identity-platform-login-ui
    resp = http_client.get(f"http://{public_address}/ui/login")

    assert resp.status_code == 200


def test_scaling_up(juju: jubilant.Juju) -> None:
    """Test scaling up."""
    juju.cli("scale-application", APP_NAME, "2")
    juju.wait(
        ready=and_(
            all_active(APP_NAME),
            unit_number(app=APP_NAME, expected_num=2),
        ),
        error=any_error(APP_NAME),
        timeout=10 * 60,
    )


@pytest.mark.parametrize(
    "remote_app_name,integration_name,is_status",
    [
        (TRAEFIK_PUBLIC_APP, PUBLIC_ROUTE_INTEGRATION_NAME, is_active),
    ],
)
def test_remove_integration(
    juju: jubilant.Juju,
    remote_app_name: str,
    integration_name: str,
    is_status: Callable[[str], StatusPredicate],
) -> None:
    """Test removing and re-adding integration."""
    with remove_integration(juju, remote_app_name, integration_name):
        juju.wait(
            ready=is_status(APP_NAME),
            error=any_error(APP_NAME),
            timeout=10 * 60,
        )
    juju.wait(
        ready=all_active(APP_NAME, remote_app_name),
        error=any_error(APP_NAME, remote_app_name),
        timeout=10 * 60,
    )


def test_scaling_down(juju: jubilant.Juju) -> None:
    """Test scaling down."""
    juju.cli("scale-application", APP_NAME, "1")
    juju.wait(
        ready=and_(
            all_active(APP_NAME),
            unit_number(app=APP_NAME, expected_num=1),
        ),
        error=any_error(APP_NAME),
        timeout=10 * 60,
    )


@pytest.mark.teardown
def test_remove_application(juju: jubilant.Juju) -> None:
    """Test removing the application."""
    juju.remove_application(APP_NAME, force=True, destroy_storage=True)
    juju.wait(lambda s: APP_NAME not in s.apps, timeout=10 * 60)
