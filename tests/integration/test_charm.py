#!/usr/bin/env python3
# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

import asyncio
import logging
from pathlib import Path
from typing import Callable

import pytest
import requests
from conftest import (
    LOGIN_UI_APP,
    LOGIN_UI_IMAGE,
    PUBLIC_INGRESS_DOMAIN,
    TRAEFIK_CHARM,
    TRAEFIK_PUBLIC_APP,
    integrate_dependencies,
)
from pytest_operator.plugin import OpsTest

logger = logging.getLogger(__name__)


@pytest.mark.skip_if_deployed
@pytest.mark.abort_on_fail
async def test_build_and_deploy(ops_test: OpsTest, local_charm: Path) -> None:
    # Deploy dependencies
    await ops_test.model.deploy(
        TRAEFIK_CHARM,
        application_name=TRAEFIK_PUBLIC_APP,
        channel="latest/edge",  # using edge to take advantage of the raw args in traefik route
        config={"external_hostname": PUBLIC_INGRESS_DOMAIN},
        trust=True,
    )
    # await ops_test.model.integrate(f"{TRAEFIK_PUBLIC_APP}:certificates", f"{CA_APP}:certificates")

    await ops_test.model.deploy(
        application_name=LOGIN_UI_APP,
        entity_url=str(local_charm),
        resources={"oci-image": LOGIN_UI_IMAGE},
        series="jammy",
        trust=True,
    )

    # Integrate with dependencies
    await integrate_dependencies(ops_test)

    await asyncio.gather(
        ops_test.model.wait_for_idle(
            apps=[LOGIN_UI_APP],
            raise_on_blocked=False,
            status="active",
            timeout=5 * 60,
        ),
    )


async def test_ingress_relation(ops_test: OpsTest):
    await ops_test.model.wait_for_idle(
        apps=[TRAEFIK_PUBLIC_APP],
        raise_on_blocked=True,
        status="active",
        timeout=5 * 60,
    )


async def test_has_ingress(ops_test: OpsTest, public_address: Callable):
    # Get the traefik address and try to reach identity-platform-login-ui
    address = await public_address(ops_test)
    resp = requests.get(f"http://{address}/ui/login")

    assert resp.status_code == 200
