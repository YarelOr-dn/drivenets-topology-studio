"""Topology multi-user migrations.

Each module in this package is a one-shot migration helper. They are
imported lazily by ``api.migrations.<name>`` so the central
``api`` package does not pay the cost on every server start.

The first migration (``rename_to_email_local`` and the supporting
``email_resolver``) re-keys the user database so usernames match the
local part of each worker's ``@drivenets.com`` email. See
``DEVELOPMENT_GUIDELINES.md`` -> "Username = email local part".
"""
