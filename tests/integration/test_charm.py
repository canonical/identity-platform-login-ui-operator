#!/usr/bin/env python3
# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

import http
import json
import logging
from typing import Optional

import pytest
from httpx import AsyncClient
from pytest_operator.plugin import OpsTest

from tests.integration.conftest import (
    CA_APP,
    INGRESS_APP,
    ISTIO_CONTROL_PLANE_CHARM,
    ISTIO_INGRESS_CHARM,
    LOGIN_UI_APP,
    LOGIN_UI_IMAGE,
    PUBLIC_INGRESS_DOMAIN,
)

logger = logging.getLogger(__name__)


@pytest.mark.abort_on_fail
async def test_build_and_deploy(ops_test: OpsTest) -> None:
    await ops_test.track_model(
        alias="istio-system",
        model_name="istio-system",
        destroy_storage=True,
    )
    istio_system = ops_test.models.get("istio-system")

    await istio_system.model.deploy(
        application_name=ISTIO_CONTROL_PLANE_CHARM,
        entity_url=ISTIO_CONTROL_PLANE_CHARM,
        channel="latest/edge",
        trust=True,
    )
    await istio_system.model.wait_for_idle(
        [ISTIO_CONTROL_PLANE_CHARM],
        status="active",
        timeout=5 * 60,
    )

    charm = await ops_test.build_charm(".")
    await ops_test.model.deploy(
        entity_url=str(charm),
        resources={"oci-image": LOGIN_UI_IMAGE},
        application_name=LOGIN_UI_APP,
        trust=True,
        series="jammy",
    )

    await ops_test.model.deploy(
        ISTIO_INGRESS_CHARM,
        application_name=INGRESS_APP,
        trust=True,
        channel="latest/edge",
        config={"external_hostname": PUBLIC_INGRESS_DOMAIN},
    )

    await ops_test.model.deploy(
        CA_APP,
        channel="latest/stable",
        trust=True,
    )

    await ops_test.model.integrate(f"{INGRESS_APP}:certificates", f"{CA_APP}:certificates")
    await ops_test.model.integrate(LOGIN_UI_APP, INGRESS_APP)

    await ops_test.model.wait_for_idle(
        apps=[LOGIN_UI_APP, INGRESS_APP, CA_APP],
        status="active",
        raise_on_blocked=True,
        timeout=5 * 60,
    )


async def test_ingress_integration(
    ops_test: OpsTest,
    leader_ingress_integration_data: Optional[dict],
    public_ingress_address: str,
    http_client: AsyncClient,
) -> None:
    assert leader_ingress_integration_data
    assert leader_ingress_integration_data["ingress"]

    data = json.loads(leader_ingress_integration_data["ingress"])
    assert data["url"] == f"https://{PUBLIC_INGRESS_DOMAIN}/{ops_test.model_name}-{LOGIN_UI_APP}"

    # Test HTTP to HTTPS redirection
    http_endpoint = (
        f"http://{public_ingress_address}/{ops_test.model_name}-{LOGIN_UI_APP}/ui/login"
    )
    resp = await http_client.get(
        http_endpoint,
        headers={"Host": PUBLIC_INGRESS_DOMAIN},
    )
    assert resp.status_code == http.HTTPStatus.MOVED_PERMANENTLY, (
        f"Expected HTTP {http.HTTPStatus.MOVED_PERMANENTLY} for {http_endpoint}, got {resp.status_code}."
    )

    # Test HTTPS endpoint
    https_endpoint = (
        f"https://{public_ingress_address}/{ops_test.model_name}-{LOGIN_UI_APP}/ui/login"
    )
    resp = await http_client.get(
        https_endpoint,
        headers={"Host": PUBLIC_INGRESS_DOMAIN},
        extensions={"sni_hostname": PUBLIC_INGRESS_DOMAIN},
    )
    assert resp.status_code == http.HTTPStatus.OK, (
        f"Expected HTTP {http.HTTPStatus.OK} for {https_endpoint}, got {resp.status_code}."
    )
