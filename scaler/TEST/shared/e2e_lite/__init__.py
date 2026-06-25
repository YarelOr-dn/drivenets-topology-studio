"""
e2e_lite -- lightweight merge of best-of-cheetah-E2E into /TEST + /SPIRENT.

Modules:
    recovery_fsm_lite   -- 11-state FSM for DUT + Spirent recovery with guards
    scenario_runner     -- stop-fail-retry scenario gate (never silently skips)
    spirent_watchdog    -- shared Spirent session watchdog with FSM integration
    base_action         -- Action contract with pre/post validations (Phase 2)
    base_validation     -- Validation contract with collect + validate hooks (Phase 2)
    system_snapshot     -- pre/post device state diff with expected-changes DSL (Phase 2)
    spirent_actions     -- typed Spirent Actions built on BaseAction (Phase 2)
    test_config         -- TestConfiguration dataclass (Phase 2)
    recipe_lint         -- schema v2 (backward-compatible) recipe linter (Phase 2)
    context_managers    -- SwitchoverSection, SpirentTrafficSection, etc (Phase 3)
    core_dump_registry  -- session-scoped core dump monitor (Phase 3)

Authoritative schema reference: ``RECIPE_SCHEMA.md`` next to this file.

Design inspiration: cheetah/tests/shared/dnos_e2e_utils. Trimmed from ~30
recovery states to 11; BaseAction contract preserved; no pytest coupling.
"""

__version__ = "0.1.0"

from .recovery_fsm_lite import (
    FailureClass,
    RecoveryEvent,
    RecoveryFsmLite,
    RecoveryGuards,
    RecoveryState,
    RecoveryTransition,
    UnrecoverableError,
)
from .base_validation import (
    BaseValidation,
    CallableValidation,
    ShowCommandContains,
    ValidationResult,
    ValidationStatus,
    WaitForCondition,
)
from .base_action import (
    ActionRunRecord,
    ActionValidationStatus,
    BaseAction,
    CallableAction,
    DnosShowAction,
    RecoverableError,
    default_is_recoverable,
)
from .spirent_watchdog import (
    SpirentCmdResult,
    SpirentHealth,
    SpirentUnrecoverableError,
    SpirentWatchdog,
    WATCHDOG_STATE_PATH,
    WatchdogState,
    read_watchdog_state,
)
from .scenario_runner import (
    RunContext,
    ScenarioResult,
    ScenarioSpec,
    ScenarioVerdict,
    SuiteResult,
    UnrecoverableSuiteFailure,
    default_classifier,
    run as run_suite,
)
from .system_snapshot import (
    DiffEntry,
    ExpectedChangeError,
    SnapshotDiff,
    SystemSnapshot,
    SystemSnapshotter,
    diff_snapshots,
    parse_rule,
)
from .spirent_actions import (
    BgpPeerAction,
    CreateMacBlockAction,
    CreateStreamAction,
    EcmpBlockAction,
    SpirentCommandAction,
    StartTrafficAction,
    StopTrafficAction,
    ValidateBgpEstablished,
    ValidateDeviceExists,
    ValidatePortReserved,
    ValidateStreamExists,
    ValidateTrafficRunning,
    ValidateTxRateAbove,
    default_spirent_tool_path,
    spirent_status_json,
)
from .test_config import (
    CLUSTER_REQUIREMENT_VALUES,
    TEST_MODE_VALUES,
    TestConfiguration,
    TestConfigurationError,
    cluster_requirement_matches,
    load_test_configuration,
    load_validation_spec,
    register_validation_type,
)
from .recipe_lint import (
    CURRENT_SCHEMA_VERSION,
    LintIssue,
    LintReport,
    lint_catalog,
    lint_manifest,
    lint_recipe,
)
from .context_managers import (
    ContextManagerError,
    DutCliSection,
    ProcessRestartSection,
    SectionResult,
    SpirentTrafficSection,
    SpirentTrafficStats,
    SwitchoverSection,
)
from .core_dump_registry import (
    CORE_DUMP_REGISTRY_STATE_PATH,
    CoreDumpEvent,
    CoreDumpRegistryError,
    CoreDumpRegistrySummary,
    CoreDumpSessionRegistry,
    DeviceCoreState,
    default_core_dump_commands,
)


def install_mac_trigger_watchdog(watchdog: "SpirentWatchdog") -> None:
    """Install a shared SpirentWatchdog into the evpn_mac_mobility mac_trigger.

    This is a convenience shim for orchestrators that want the mac-mobility
    suite to go through the FSM-aware watchdog without touching their own
    trigger code. Safe no-op if the mac_trigger module isn't importable
    (e.g. the suite isn't installed).
    """
    try:
        from scaler.TEST.catalog.evpn_mac_mobility_SW204115.shared import mac_trigger  # type: ignore
    except Exception:
        try:
            from TEST.catalog.evpn_mac_mobility_SW204115.shared import mac_trigger  # type: ignore
        except Exception:
            return
    mac_trigger.set_shared_watchdog(watchdog)

__all__ = [
    "ActionRunRecord",
    "ActionValidationStatus",
    "BaseAction",
    "BaseValidation",
    "BgpPeerAction",
    "CLUSTER_REQUIREMENT_VALUES",
    "CORE_DUMP_REGISTRY_STATE_PATH",
    "CURRENT_SCHEMA_VERSION",
    "CallableAction",
    "CallableValidation",
    "ContextManagerError",
    "CoreDumpEvent",
    "CoreDumpRegistryError",
    "CoreDumpRegistrySummary",
    "CoreDumpSessionRegistry",
    "CreateMacBlockAction",
    "CreateStreamAction",
    "DeviceCoreState",
    "DiffEntry",
    "DnosShowAction",
    "DutCliSection",
    "EcmpBlockAction",
    "ExpectedChangeError",
    "FailureClass",
    "LintIssue",
    "LintReport",
    "ProcessRestartSection",
    "RecoverableError",
    "RecoveryEvent",
    "RecoveryFsmLite",
    "RecoveryGuards",
    "RecoveryState",
    "RecoveryTransition",
    "RunContext",
    "ScenarioResult",
    "ScenarioSpec",
    "ScenarioVerdict",
    "SectionResult",
    "ShowCommandContains",
    "SnapshotDiff",
    "SpirentCmdResult",
    "SpirentCommandAction",
    "SpirentHealth",
    "SpirentTrafficSection",
    "SpirentTrafficStats",
    "SpirentUnrecoverableError",
    "SpirentWatchdog",
    "StartTrafficAction",
    "StopTrafficAction",
    "SuiteResult",
    "SwitchoverSection",
    "SystemSnapshot",
    "SystemSnapshotter",
    "TEST_MODE_VALUES",
    "TestConfiguration",
    "TestConfigurationError",
    "UnrecoverableError",
    "UnrecoverableSuiteFailure",
    "ValidateBgpEstablished",
    "ValidateDeviceExists",
    "ValidatePortReserved",
    "ValidateStreamExists",
    "ValidateTrafficRunning",
    "ValidateTxRateAbove",
    "ValidationResult",
    "ValidationStatus",
    "WATCHDOG_STATE_PATH",
    "WaitForCondition",
    "WatchdogState",
    "cluster_requirement_matches",
    "default_classifier",
    "default_core_dump_commands",
    "default_is_recoverable",
    "default_spirent_tool_path",
    "diff_snapshots",
    "install_mac_trigger_watchdog",
    "lint_catalog",
    "lint_manifest",
    "lint_recipe",
    "load_test_configuration",
    "load_validation_spec",
    "parse_rule",
    "read_watchdog_state",
    "register_validation_type",
    "run_suite",
    "spirent_status_json",
]
