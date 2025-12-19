# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

import os
import uuid
from pathlib import Path
from typing import Iterator

import jubilant
import pytest
from integration.constants import (
    LOGIN_UI_APP,
    PUBLIC_ROUTE_INTEGRATION_NAME,
    TRAEFIK_PUBLIC_APP,
)
from integration.utils import create_temp_juju_model, unit_address


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add custom command-line options for model management and deployment control.

    This function adds the following options:
        --keep-models: Keep the Juju model after the test is finished.
        --model: Specify the Juju model to run the tests on.
        --no-deploy: Skip deployment of the charm.
    """
    parser.addoption(
        "--keep-models",
        action="store_true",
        default=False,
        help="Keep the model after the test is finished.",
    )
    parser.addoption(
        "--model",
        action="store",
        default=None,
        help="The model to run the tests on.",
    )
    parser.addoption(
        "--no-deploy",
        action="store_true",
        default=False,
        help="Skip deployment of the charm.",
    )


def pytest_configure(config: pytest.Config) -> None:
    """Register custom markers for test selection based on deployment and model management.

    This function registers the following markers:
        skip_if_deployed: Skip tests if the charm is already deployed.
    """
    config.addinivalue_line("markers", "skip_if_deployed: skip test if deployed")


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Modify collected test items based on command-line options.

    This function skips tests with specific markers based on the provided command-line options:
        - If --no-deploy is set, tests marked with "skip_if_deployed" are skipped.
    """
    for item in items:
        if config.getoption("--no-deploy") and "skip_if_deployed" in item.keywords:
            skip_deployed = pytest.mark.skip(reason="skipping deployment")
            item.add_marker(skip_deployed)


@pytest.fixture(scope="module")
def juju(request: pytest.FixtureRequest) -> Iterator[jubilant.Juju]:
    """Create a temporary Juju model for integration tests."""
    model_name = request.config.getoption("--model")
    if not model_name:
        model_name = f"test-login-ui-{uuid.uuid4().hex[-8:]}"

    yield from create_temp_juju_model(request, model=model_name)


@pytest.fixture(scope="module")
def local_charm(juju: jubilant.Juju) -> Path:
    """Get the path to the charm-under-test."""
    # in GitHub CI, charms are built with charmcraftcache and uploaded to $CHARM_PATH
    charm: str | Path | None = os.getenv("CHARM_PATH")
    if not charm:
        import shutil
        import subprocess

        # Check if charmcraft is available
        if not shutil.which("charmcraft"):
            raise RuntimeError("charmcraft not found in PATH")

        subprocess.run(["charmcraft", "pack"], check=True)
        charms = list(Path(".").glob("*.charm"))
        if charms:
            charm = charms[0].absolute()
        else:
            raise RuntimeError("Charm not found and build failed")
    return Path(charm)


def integrate_dependencies(juju: jubilant.Juju) -> None:
    """Integrate the login UI app with its dependencies."""
    juju.integrate(f"{LOGIN_UI_APP}:{PUBLIC_ROUTE_INTEGRATION_NAME}", TRAEFIK_PUBLIC_APP)


@pytest.fixture
def public_address(juju: jubilant.Juju) -> str:
    """Get the public address of the Traefik application."""
    return unit_address(juju, app_name=TRAEFIK_PUBLIC_APP)
