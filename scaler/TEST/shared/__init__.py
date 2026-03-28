"""
Generic QA engines for DNOS E2E test automation (Tier 1).

All engines are feature-agnostic: they read commands, patterns, and expectations
from recipe JSON.  Feature-specific knowledge lives in Tier 2 knowledge packs
(e.g. evpn_event_knowledge.py) that populate the recipe.

Engines:
    counter_tracker    -- Before/after counter snapshot + diff
    event_tracker      -- 3-method system event engine (terminal, syslog, traces)
    syslog_parser      -- Generic DNOS syslog line parser
    config_baseline    -- Golden config snapshot + debris detection
    health_guard       -- Device health (processes, crashes, CPU/mem, errors)
    multi_device       -- Cross-device command execution + correlation
    regression_detector-- Historical baseline comparison
    test_isolation     -- Cleanup guarantee (atexit, signals, state clear)
    continuous_poller  -- High-frequency counter/event polling during triggers
    report_generator   -- Unified FULL_REPORT.md
    vtysh_runner       -- vtysh deep access via InteractiveSSHSession
    post_run_learner   -- Auto-learn from verdicts, persist to JSON + MD
"""
