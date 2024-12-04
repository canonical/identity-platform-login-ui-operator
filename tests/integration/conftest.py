# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.


import asyncio
import functools
from pathlib import Path
from typing import AsyncGenerator, Callable, Optional

import httpx
import pytest_asyncio
import yaml
from pytest_operator.plugin import OpsTest

from constants import INGRESS_INTEGRATION_NAME

METADATA = yaml.safe_load(Path("./charmcraft.yaml").read_text())
LOGIN_UI_APP = METADATA["name"]
LOGIN_UI_IMAGE = METADATA["resources"]["oci-image"]["upstream-source"]
CA_APP = "self-signed-certificates"
INGRESS_APP = "public-ingress"
ISTIO_CONTROL_PLANE_CHARM = "istio-k8s"
ISTIO_INGRESS_CHARM = "istio-ingress-k8s"
PUBLIC_INGRESS_DOMAIN = "public"
PUBLIC_LOAD_BALANCER = f"{INGRESS_APP}-istio"


async def get_unit_data(ops_test: OpsTest, unit_name: str) -> dict:
    show_unit_cmd = (f"show-unit {unit_name}").split()
    _, stdout, _ = await ops_test.juju(*show_unit_cmd)
    cmd_output = yaml.safe_load(stdout)
    return cmd_output[unit_name]


async def get_integration_data(
    ops_test: OpsTest, app_name: str, integration_name: str, unit_num: int = 0
) -> Optional[dict]:
    data = await get_unit_data(ops_test, f"{app_name}/{unit_num}")
    return next(
        (
            integration
            for integration in data["relation-info"]
            if integration["endpoint"] == integration_name
        ),
        None,
    )


async def get_app_integration_data(
    ops_test: OpsTest,
    app_name: str,
    integration_name: str,
    unit_num: int = 0,
) -> Optional[dict]:
    data = await get_integration_data(ops_test, app_name, integration_name, unit_num)
    return data["application-data"] if data else None


@pytest_asyncio.fixture
async def app_integration_data(ops_test: OpsTest) -> Callable:
    return functools.partial(get_app_integration_data, ops_test)


@pytest_asyncio.fixture
async def leader_ingress_integration_data(app_integration_data: Callable) -> Optional[dict]:
    return await app_integration_data(LOGIN_UI_APP, INGRESS_INTEGRATION_NAME)


@pytest_asyncio.fixture
async def http_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    async with httpx.AsyncClient(verify=False) as client:
        yield client


async def get_k8s_service_address(namespace: str, service_name: str) -> str:
    cmd = [
        "kubectl",
        "-n",
        namespace,
        "get",
        f"service/{service_name}",
        "-o=jsonpath={.status.loadBalancer.ingress[0].ip}",
    ]

    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, _ = await process.communicate()

    return stdout.decode().strip() if not process.returncode else ""


@pytest_asyncio.fixture
async def public_ingress_address(ops_test: OpsTest) -> str:
    return await get_k8s_service_address(ops_test.model_name, PUBLIC_LOAD_BALANCER)
