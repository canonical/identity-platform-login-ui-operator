# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

import functools
import os
from pathlib import Path
from typing import Awaitable, Callable

import pytest_asyncio
import yaml
from pytest_operator.plugin import OpsTest

from constants import PUBLIC_ROUTE_INTEGRATION_NAME

METADATA = yaml.safe_load(Path("./charmcraft.yaml").read_text())
LOGIN_UI_APP = METADATA["name"]
LOGIN_UI_IMAGE = METADATA["resources"]["oci-image"]["upstream-source"]
# CA_APP = "self-signed-certificates"
TRAEFIK_CHARM = "traefik-k8s"
TRAEFIK_PUBLIC_APP = "traefik-public"
PUBLIC_INGRESS_DOMAIN = "public"


async def integrate_dependencies(ops_test: OpsTest) -> None:
    await ops_test.model.integrate(
        f"{LOGIN_UI_APP}:{PUBLIC_ROUTE_INTEGRATION_NAME}", TRAEFIK_PUBLIC_APP
    )


@pytest_asyncio.fixture(scope="module")
async def local_charm(ops_test: OpsTest) -> Path:
    # in GitHub CI, charms are built with charmcraftcache and uploaded to $CHARM_PATH
    charm = os.getenv("CHARM_PATH")
    if not charm:
        # fall back to build locally - required when run outside of GitHub CI
        charm = await ops_test.build_charm(".")
    return charm


async def unit_address(ops_test: OpsTest, *, app_name: str, unit_num: int = 0) -> str:
    status = await ops_test.model.get_status()
    return status["applications"][app_name]["units"][f"{app_name}/{unit_num}"]["address"]


@pytest_asyncio.fixture
async def public_address() -> Callable[[OpsTest, int], Awaitable[str]]:
    return functools.partial(unit_address, app_name=TRAEFIK_PUBLIC_APP)
