# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

import json
from unittest.mock import MagicMock

import ops.testing
import pytest

from .conftest import create_state

PEM = "-----BEGIN CERTIFICATE-----\nMIIB\n-----END CERTIFICATE-----"
V0_UNIT_DATA = {
    "ca": json.dumps(PEM),
    "certificate": json.dumps(PEM),
    "chain": json.dumps([PEM]),
    "version": "0",
}


@pytest.mark.parametrize(
    "remote_app_data, remote_units_data",
    [
        pytest.param(
            {"certificates": json.dumps([PEM]), "version": "1"}, {0: {}}, id="v1 provider"
        ),
        pytest.param({}, {0: V0_UNIT_DATA}, id="v0 provider, which JSON-encodes its fields"),
    ],
)
def test_ca_bundle_gets_the_certificate(
    context: ops.testing.Context,
    peer_relation: ops.testing.PeerRelation,
    patch_certificate_transfer_integration_file_open: MagicMock,
    remote_app_data: dict,
    remote_units_data: dict,
) -> None:
    relation = ops.testing.Relation(
        endpoint="receive-ca-cert",
        interface="certificate_transfer",
        remote_app_name="self-signed-certificates",
        remote_app_data=remote_app_data,
        remote_units_data=remote_units_data,
    )
    state_in = create_state(relations=[peer_relation, relation])

    context.run(context.on.config_changed(), state_in)

    patch_certificate_transfer_integration_file_open().write.assert_any_call(PEM)
