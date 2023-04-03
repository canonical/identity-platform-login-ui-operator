#!/usr/bin/env python3
# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Interface library for sharing Identity Platform Login UI application's endpoint with other charms.
This library provides a Python API for both requesting and providing a public endpoint.
## Getting Started
To get started using the library, you need to fetch the library using `charmcraft`.
```shell
cd some-charm
charmcraft fetch-lib charms.identity_platform_login_ui.v0.login_ui_endpoint
```
To use the library from the requirer side:
In the `metadata.yaml` of the charm, add the following:
```yaml
requires:
  ui-endpoint-info:
    interface: login_ui_endpoint
    limit: 1
```
Then, to initialise the library:
```python
from charms.identity_platform_login_ui.v0.login_ui_endpoint import (
    LoginUIEndpointRelationError,
    LoginUIEndpointRequirer,
)
Class SomeCharm(CharmBase):
    def __init__(self, *args):
        self.login_ui_endpoint_relation = LoginUIEndpointRequirer(self)
        self.framework.observe(self.on.some_event_emitted, self.some_event_function)
    def some_event_function():
        # fetch the relation info
        try:
            login_ui_endpoint = self.login_ui_endpoint_relation.get_login_ui_endpoint()
        except LoginUIEndpointRelationError as error:
            ...
```
"""

import logging
from typing import Dict, Optional

from ops.charm import CharmBase, RelationCreatedEvent
from ops.framework import EventBase, EventSource, Object, ObjectEvents
from ops.model import Application

# The unique Charmhub library identifier, never change it
LIBID = "460ab09e6b874d1c891b67f83586c9a7"

# Increment this major API version when introducing breaking changes
LIBAPI = 0

# Increment this PATCH version before using `charmcraft publish-lib` or reset
# to 0 if you are raising the major API version
LIBPATCH = 1

RELATION_NAME = "ui-endpoint-info"
INTERFACE_NAME = "login_ui_endpoint"
logger = logging.getLogger(__name__)


class LoginUIEndpointRelationReadyEvent(EventBase):
    """Event to notify the charm that the relation is ready."""


class LoginUIEndpointProviderEvents(ObjectEvents):
    """Event descriptor for events raised by `LoginUIEndpointProvider`."""

    ready = EventSource(LoginUIEndpointRelationReadyEvent)


class LoginUIEndpointProvider(Object):
    """Provider side of the endpoint-info relation."""

    on = LoginUIEndpointProviderEvents()

    def __init__(self, charm: CharmBase, relation_name: str = RELATION_NAME):
        super().__init__(charm, relation_name)

        self._charm = charm
        self._relation_name = relation_name

        events = self._charm.on[relation_name]
        self.framework.observe(
            events.relation_created, self._on_provider_endpoint_relation_created
        )

    def _on_provider_endpoint_relation_created(self, event: RelationCreatedEvent) -> None:
        self.on.ready.emit()

    def send_endpoint_relation_data(self, endpoint: str) -> None:
        """Updates relation with endpoint info."""
        if not self._charm.unit.is_leader():
            return

        relations = self.model.relations[self._relation_name]
        for relation in relations:
            relation.data[self._charm.app].update(
                {
                    "endpoint": endpoint,
                }
            )


class LoginUIEndpointRelationError(Exception):
    """Base class for the relation exceptions."""

    pass


class LoginUIEndpointRelationMissingError(LoginUIEndpointRelationError):
    """Raised when the relation is missing."""

    def __init__(self) -> None:
        self.message = "Missing endpoint-info relation with Identity Platform Login UI"
        super().__init__(self.message)


class LoginUIEndpointRelationDataMissingError(LoginUIEndpointRelationError):
    """Raised when information is missing from the relation."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(self.message)


class LoginUIEndpointRequirer(Object):
    """Requirer side of the ui-endpoint-info relation."""

    def __init__(self, charm: CharmBase, relation_name: str = RELATION_NAME):
        super().__init__(charm, relation_name)
        self.charm = charm
        self._relation_name = relation_name

    def get_login_ui_endpoint(self) -> Optional[Dict]:
        """Get the Identity Platform Login UI endpoints."""
        if not self.model.unit.is_leader():
            return None
        endpoint = self.model.relations[self._relation_name]
        if len(endpoint) == 0:
            raise LoginUIEndpointRelationMissingError()

        remote_app = [
            app
            for app in endpoint[0].data.keys()
            if isinstance(app, Application) and not app._is_our_app
        ][0]

        data = endpoint[0].data[remote_app]

        if "endpoint" not in data:
            raise LoginUIEndpointRelationDataMissingError(
                "Missing endpoint in ui-endpoint-info relation data"
            )

        if data["endpoint"] == "":
            raise LoginUIEndpointRelationDataMissingError(
                "Missing endpoint in ui-endpoint-info relation data"
            )

        return {
            "endpoint": data["endpoint"],
        }
