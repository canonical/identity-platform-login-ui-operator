# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

from typing import Any, Mapping, TypeAlias

from ops import ConfigData

ServiceConfigs: TypeAlias = Mapping[str, Any]


class CharmConfig:
    """A class representing the data source of charm configurations."""

    def __init__(self, config: ConfigData) -> None:
        self._config = config

    def to_service_configs(self) -> ServiceConfigs:
        return {"log_level": self._config["log_level"]}

    def __getitem__(self, key: str) -> str:
        return self._config.get(key)
