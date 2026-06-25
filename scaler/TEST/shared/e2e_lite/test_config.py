#!/usr/bin/env python3
"""
test_config -- ``TestConfiguration`` dataclass wired to ``recipe.json``.

Every /TEST recipe can carry an optional ``test_config`` block. When present,
the orchestrator (or scenario runner) loads it into this dataclass and uses
it to:

* **Gate execution** -- enforce ``cluster_requirement`` (``sa_only`` / ``cl_only``
  / ``any``) against the resolved device type before running prerequisites.
* **Compose validations** -- additional BaseValidation instances returned by
  ``additional_pre_validations`` plug into the first Action's pre-validation
  list (wired by the orchestrator, not this module).
* **Parameterise the FSM** -- custom retry budgets / heavy-op caps from
  ``fsm_guards`` are applied to the suite-scoped ``RecoveryFsmLite``.
* **Enforce system snapshots** -- the ``snapshot_expected_changes`` DSL
  (see :mod:`system_snapshot`) declares allowed deltas so unlisted changes
  loudly fail.
* **Provide metadata** -- ``jira_component`` and ``owner`` land in verdict
  reports and telemetry for ownership tracking.

The recipe JSON block maps 1:1 to the dataclass. Example::

    "test_config": {
        "test_id": "TEST_flowspec_vpn_ha_001",
        "test_mode": "dnos_mode",
        "cluster_requirement": "cl_only",
        "jira_component": "flowspec-vpn",
        "owner": "yarel.or",
        "additional_pre_validations": [
            {"type": "ShowCommandContains",
             "command": "show bgp summary",
             "substring": "Established",
             "device": "PE-4"}
        ],
        "snapshot_expected_changes": {
            "container_restart:ncc/0/routing_engine": "INCREASE_BY(1)",
            "process_restart:ncc/0/routing_engine/bgpd": "INCREASE_BY(1)",
            "new_core_dumps": "FORBIDDEN"
        },
        "fsm_guards": {
            "max_ssh_retries": 5,
            "max_spirent_reconnects": 3,
            "max_scenario_retries": 2,
            "max_heavy_ops_per_session": 1,
            "hard_timeout_sec": 900
        }
    }

Backward compatibility: recipes that omit ``test_config`` use module defaults.
"""
from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field, fields, is_dataclass
from pathlib import Path
from typing import Any, ClassVar, Dict, List, Optional, Tuple, Type

from .base_validation import (
    BaseValidation,
    CallableValidation,
    ShowCommandContains,
    WaitForCondition,
)
from .recovery_fsm_lite import RecoveryGuards

logger = logging.getLogger(__name__)

__all__ = [
    "TEST_MODE_VALUES",
    "CLUSTER_REQUIREMENT_VALUES",
    "TestConfiguration",
    "TestConfigurationError",
    "cluster_requirement_matches",
    "load_test_configuration",
    "load_validation_spec",
    "register_validation_type",
]


TEST_MODE_VALUES: Tuple[str, ...] = ("dnos_mode", "baseos_mode")
CLUSTER_REQUIREMENT_VALUES: Tuple[str, ...] = ("sa_only", "cl_only", "any")


# ---------------------------------------------------------------------------
# Validation spec registry (recipe JSON -> BaseValidation instance)
# ---------------------------------------------------------------------------

_VALIDATION_REGISTRY: Dict[str, Type[BaseValidation]] = {
    "ShowCommandContains": ShowCommandContains,
    "WaitForCondition": WaitForCondition,
    "CallableValidation": CallableValidation,
}


def register_validation_type(
    name: str, cls: Type[BaseValidation], *, overwrite: bool = False,
) -> None:
    """Register a custom validation class under ``name`` for recipe deserialisation.

    Orchestrators can extend the registry with Spirent / DNOS validations
    they control without editing this module. Pass ``overwrite=True`` to
    replace an existing entry (for tests / plugins).
    """
    if not overwrite and name in _VALIDATION_REGISTRY:
        raise TestConfigurationError(
            f"validation type '{name}' already registered; "
            f"pass overwrite=True to replace"
        )
    _VALIDATION_REGISTRY[name] = cls


class TestConfigurationError(ValueError):
    """Raised for malformed ``test_config`` recipe blocks."""


def load_validation_spec(spec: Dict[str, Any]) -> BaseValidation:
    """Build a :class:`BaseValidation` from a recipe-style dict.

    Shape::

        {"type": "ShowCommandContains", "command": "...", "substring": "...",
         "device": "PE-4", "name": "optional", "timeout": 30}

    Unknown ``type`` -> :class:`TestConfigurationError`. Unknown kwargs that
    the target class rejects surface as ``TypeError`` from its constructor.
    """
    if not isinstance(spec, dict):
        raise TestConfigurationError(
            f"validation spec must be a dict, got {type(spec).__name__}"
        )
    spec = dict(spec)
    type_name = spec.pop("type", None)
    if not type_name:
        raise TestConfigurationError(
            f"validation spec missing required 'type' field: {spec!r}"
        )
    cls = _VALIDATION_REGISTRY.get(type_name)
    if cls is None:
        raise TestConfigurationError(
            f"unknown validation type '{type_name}' "
            f"(registered: {sorted(_VALIDATION_REGISTRY)})"
        )
    try:
        return cls(**spec)
    except TypeError as exc:
        raise TestConfigurationError(
            f"could not instantiate {type_name}: {exc}"
        ) from exc


# ---------------------------------------------------------------------------
# TestConfiguration dataclass
# ---------------------------------------------------------------------------

@dataclass
class TestConfiguration:
    """Optional per-test configuration block loaded from ``recipe.json``.

    Every field has a safe default so a recipe that omits ``test_config``
    entirely still produces a valid object via :meth:`from_dict` with an
    empty mapping.
    """

    test_id: str = ""
    test_mode: str = "dnos_mode"
    cluster_requirement: str = "any"
    jira_component: str = ""
    owner: str = ""
    additional_pre_validations: List[BaseValidation] = field(default_factory=list)
    snapshot_expected_changes: Dict[str, str] = field(default_factory=dict)
    fsm_guards: RecoveryGuards = field(default_factory=RecoveryGuards)

    _RAW_VALIDATION_SPECS: ClassVar[str] = "_raw_validation_specs"

    def __post_init__(self) -> None:
        self._validate_literals()

    def _validate_literals(self) -> None:
        if self.test_mode not in TEST_MODE_VALUES:
            raise TestConfigurationError(
                f"test_mode must be one of {TEST_MODE_VALUES}, "
                f"got {self.test_mode!r}"
            )
        if self.cluster_requirement not in CLUSTER_REQUIREMENT_VALUES:
            raise TestConfigurationError(
                f"cluster_requirement must be one of {CLUSTER_REQUIREMENT_VALUES}, "
                f"got {self.cluster_requirement!r}"
            )

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------
    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "TestConfiguration":
        """Build a TestConfiguration from a recipe.json ``test_config`` dict.

        Accepts ``None`` or ``{}`` for backward-compat with legacy recipes:
        you get defaults. Validation kwargs that the dataclass doesn't know
        about are reported as :class:`TestConfigurationError` rather than
        silently dropped.
        """
        data = dict(data or {})

        raw_validations = data.pop("additional_pre_validations", []) or []
        raw_guards = data.pop("fsm_guards", None)
        snapshot_changes = dict(data.pop("snapshot_expected_changes", {}) or {})

        known = {f.name for f in fields(cls)}
        unknown = sorted(k for k in data if k not in known)
        if unknown:
            raise TestConfigurationError(
                f"unknown test_config fields: {unknown} "
                f"(allowed: {sorted(known)})"
            )

        if not isinstance(raw_validations, list):
            raise TestConfigurationError(
                "additional_pre_validations must be a list of validation specs"
            )
        validations: List[BaseValidation] = []
        for i, spec in enumerate(raw_validations):
            try:
                validations.append(load_validation_spec(spec))
            except TestConfigurationError as exc:
                raise TestConfigurationError(
                    f"additional_pre_validations[{i}]: {exc}"
                ) from exc

        guards = _build_guards(raw_guards)

        inst = cls(
            test_id=str(data.get("test_id", "") or ""),
            test_mode=str(data.get("test_mode", "dnos_mode")),
            cluster_requirement=str(data.get("cluster_requirement", "any")),
            jira_component=str(data.get("jira_component", "") or ""),
            owner=str(data.get("owner", "") or ""),
            additional_pre_validations=validations,
            snapshot_expected_changes=snapshot_changes,
            fsm_guards=guards,
        )
        setattr(inst, cls._RAW_VALIDATION_SPECS, list(raw_validations))
        return inst

    @classmethod
    def from_recipe(cls, recipe: Dict[str, Any]) -> "TestConfiguration":
        """Convenience: extract ``test_config`` from a full recipe dict."""
        if not isinstance(recipe, dict):
            raise TestConfigurationError("recipe must be a dict")
        return cls.from_dict(recipe.get("test_config"))

    @classmethod
    def from_recipe_file(cls, path: Path | str) -> "TestConfiguration":
        """Read ``recipe.json`` from disk and build a TestConfiguration from it."""
        p = Path(path)
        if not p.exists():
            raise TestConfigurationError(f"recipe file not found: {p}")
        with p.open("r", encoding="utf-8") as fh:
            try:
                recipe = json.load(fh)
            except json.JSONDecodeError as exc:
                raise TestConfigurationError(
                    f"could not parse recipe JSON ({p}): {exc}"
                ) from exc
        return cls.from_recipe(recipe)

    def to_dict(self) -> Dict[str, Any]:
        """Serialise back to a recipe-shaped dict (round-trips cleanly).

        ``additional_pre_validations`` is serialised from the preserved raw
        spec list when available; otherwise from a best-effort fallback that
        captures each validation's class name and public attrs. Custom
        validation subclasses that mangle their __init__ args may not
        round-trip perfectly -- keep the recipe as the source of truth.
        """
        raw_specs = getattr(self, self._RAW_VALIDATION_SPECS, None)
        if raw_specs is None:
            raw_specs = [
                _validation_to_spec(v) for v in self.additional_pre_validations
            ]
        return {
            "test_id": self.test_id,
            "test_mode": self.test_mode,
            "cluster_requirement": self.cluster_requirement,
            "jira_component": self.jira_component,
            "owner": self.owner,
            "additional_pre_validations": raw_specs,
            "snapshot_expected_changes": dict(self.snapshot_expected_changes),
            "fsm_guards": asdict(self.fsm_guards) if is_dataclass(self.fsm_guards) else {},
        }

    def to_json(self, **json_kwargs: Any) -> str:
        """Serialise to a JSON string, passing kwargs through to ``json.dumps``."""
        json_kwargs.setdefault("indent", 2)
        json_kwargs.setdefault("sort_keys", True)
        return json.dumps(self.to_dict(), **json_kwargs)

    # ------------------------------------------------------------------
    # Runtime helpers
    # ------------------------------------------------------------------
    def matches_device(self, device_type: str) -> bool:
        """Return True iff ``device_type`` satisfies ``cluster_requirement``.

        ``device_type`` is the free-form family string (e.g. "SA-36CD-S",
        "CL-86", "NCP-12") that the orchestrator resolves from Network
        Mapper / devices.json. Matching is case-insensitive substring:
        "SA-*" -> ``sa_only``, "CL-*" -> ``cl_only``. Anything matches
        ``any``.
        """
        return cluster_requirement_matches(self.cluster_requirement, device_type)

    def apply_guards_to(self, fsm: Any) -> None:
        """Replace a bound FSM's guards with :attr:`fsm_guards`.

        Safe no-op if the provided object lacks a ``guards`` attribute
        (e.g. during unit tests where the FSM is mocked).
        """
        if fsm is None:
            return
        if not hasattr(fsm, "guards"):
            logger.debug("apply_guards_to: object has no 'guards' attr; skipping")
            return
        fsm.guards = self.fsm_guards

    def summary(self) -> str:
        """Human-friendly one-liner for log lines / UI."""
        return (
            f"TestConfiguration(test_id={self.test_id!r}, mode={self.test_mode}, "
            f"cluster={self.cluster_requirement}, owner={self.owner!r}, "
            f"pre_validations={len(self.additional_pre_validations)}, "
            f"snapshot_rules={len(self.snapshot_expected_changes)})"
        )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _build_guards(raw: Any) -> RecoveryGuards:
    """Build a :class:`RecoveryGuards` from a dict, or return defaults."""
    if raw is None:
        return RecoveryGuards()
    if isinstance(raw, RecoveryGuards):
        return raw
    if not isinstance(raw, dict):
        raise TestConfigurationError(
            f"fsm_guards must be a dict or RecoveryGuards, got {type(raw).__name__}"
        )

    defaults = RecoveryGuards()
    known = {f.name for f in fields(RecoveryGuards)}
    unknown = sorted(k for k in raw if k not in known)
    if unknown:
        raise TestConfigurationError(
            f"unknown fsm_guards fields: {unknown} (allowed: {sorted(known)})"
        )
    merged = {f.name: getattr(defaults, f.name) for f in fields(RecoveryGuards)}
    merged.update(raw)
    return RecoveryGuards(**merged)


def _validation_to_spec(v: BaseValidation) -> Dict[str, Any]:
    """Best-effort reverse mapping of a BaseValidation back to a dict spec.

    Used only when :meth:`TestConfiguration.to_dict` is called on an object
    that was built programmatically (no recipe specs preserved). Custom
    subclasses with private state may not round-trip perfectly.
    """
    spec: Dict[str, Any] = {"type": type(v).__name__, "name": getattr(v, "name", "")}
    for attr in (
        "command", "substring", "device",
        "timeout", "negative_validation", "fail_on_error",
    ):
        if hasattr(v, attr):
            val = getattr(v, attr)
            if val not in (None, "", 0, False):
                spec[attr] = val
    return spec


def cluster_requirement_matches(requirement: str, device_type: str) -> bool:
    """Return True iff the device_type family satisfies the requirement."""
    req = (requirement or "any").lower()
    if req == "any":
        return True
    dt = (device_type or "").upper()
    if req == "sa_only":
        return "SA" in dt
    if req == "cl_only":
        return "CL" in dt
    raise TestConfigurationError(
        f"unknown cluster_requirement {requirement!r} "
        f"(expected one of {CLUSTER_REQUIREMENT_VALUES})"
    )


# ---------------------------------------------------------------------------
# Public convenience
# ---------------------------------------------------------------------------

def load_test_configuration(
    source: Dict[str, Any] | Path | str | None,
) -> TestConfiguration:
    """Load a :class:`TestConfiguration` from a dict, file path, or recipe file.

    Dispatches on ``source`` type:

    * ``None`` / ``{}`` -> defaults
    * ``dict`` -> treated as a recipe dict (uses ``test_config`` sub-key
      when present, else the dict itself)
    * ``str`` / ``Path`` -> reads the JSON file, then extracts ``test_config``
    """
    if source is None:
        return TestConfiguration()
    if isinstance(source, (str, Path)):
        return TestConfiguration.from_recipe_file(source)
    if isinstance(source, dict):
        if "test_config" in source:
            return TestConfiguration.from_recipe(source)
        return TestConfiguration.from_dict(source)
    raise TestConfigurationError(
        f"unsupported source type: {type(source).__name__}"
    )
