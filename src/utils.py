#!/usr/bin/env python3
# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Utility functions for the login UI charm."""

from urllib.parse import urlparse, urlunparse


def normalise_url(url: str) -> str:
    """Convert a URL to a more user friendly HTTPS URL.

    The user will be redirected to this URL, we need to use the https prefix
    in order to be able to set cookies (secure attribute is set). Also we remove
    the port from the URL to make it more user-friendly.

    For example:
        http://ingress:80 -> https://ingress
        http://ingress:80/ -> https://ingress/
        http://ingress:80/path/subpath -> https://ingress/path/subpath

    This conversion works under the following assumptions:
    1) The ingress will serve https under the 443 port, the user-agent will
       implicitly make the request on that port
    2) The provided URL is not a relative path
    3) No user/password is provided in the netloc

    This is a hack and should be removed once traefik provides a way for us to
    request the https URL.
    """
    p = urlparse(url)

    p = p._replace(scheme="https")
    p = p._replace(netloc=p.netloc.rsplit(":", 1)[0])

    return urlunparse(p)
