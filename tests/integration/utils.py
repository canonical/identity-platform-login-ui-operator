# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

from typing import Iterator

import jubilant
import pytest
import yaml


def create_temp_juju_model(
    request: pytest.FixtureRequest, *, model: str = ""
) -> Iterator[jubilant.Juju]:
    """Create a temporary Juju model."""
    keep_models = bool(request.config.getoption("--keep-models"))

    # jubilant.temp_model is a context manager provided by the library
    with jubilant.temp_model(keep=keep_models) as juju:
        # Hack to get around `jubilant.temp_model` not accepting a custom model name
        if model:
            assert juju.model is not None
            # Destroy `jubilant-*` model created by default
            if juju.model.startswith("jubilant-"):
                juju.destroy_model(juju.model, destroy_storage=True, force=True)

            # `CLIError` will be emitted if `--model` already exists so silently ignore
            # error and set the `model` attribute to the value of model.
            try:
                juju.add_model(model)
            except jubilant.CLIError as e:
                # Model already exists, just use it
                import logging

                logging.debug(f"Model {model} already exists, reusing it: {e}")
                juju.model = model

        juju.wait_timeout = 10 * 60

        yield juju

        if request.session.testsfailed:
            log = juju.debug_log(limit=1000)
            print(log, end="")


def unit_address(juju: jubilant.Juju, *, app_name: str, unit_num: int = 0) -> str:
    """Get the address of a unit."""
    status_yaml = juju.cli("status", "--format", "yaml")
    status = yaml.safe_load(status_yaml)
    return status["applications"][app_name]["units"][f"{app_name}/{unit_num}"]["address"]


def wait_for_active_idle(juju: jubilant.Juju, apps: list[str], timeout: float = 1000) -> None:
    """Wait for all applications and their units to be active and idle."""

    def condition(s: jubilant.Status) -> bool:
        return jubilant.all_active(s, *apps) and jubilant.all_agents_idle(s, *apps)

    juju.wait(condition, error=jubilant.any_error, timeout=timeout)
