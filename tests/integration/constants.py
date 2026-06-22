# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

from pathlib import Path

import yaml

METADATA = yaml.safe_load(Path("./charmcraft.yaml").read_text())
APP_NAME = METADATA["name"]
LOGIN_UI_IMAGE = METADATA["resources"]["oci-image"]["upstream-source"]
ISTIO_CHARM = "istio-k8s"
ISTIO_INGRESS_CHARM = "istio-ingress-k8s"
ISTIO_CHANNEL = "2/stable"
PUBLIC_ROUTE_INTEGRATION_NAME = "public-route"
