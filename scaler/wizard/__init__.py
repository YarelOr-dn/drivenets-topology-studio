"""
SCALER Wizard Subpackage

This package contains the modular components of the Interactive Scale Wizard,
organized by functionality for easier maintenance and debugging.

Modules:
    - core: Core classes (WizardState proxies, navigation, exceptions)
    - ui: Console output, prompts, display functions
    - parsers: Config parsing (EVPN, MH, RT, VLAN mappings)
    - validators: DNOS limits, ESI format, interface validation
    - system: System hierarchy configuration
    - interfaces: Interface configuration
    - services: FXC/VPLS/EVPN service configuration
    - bgp: BGP configuration
    - igp: IGP/ISIS configuration
    - multihoming: Multihoming/ESI configuration
    - push: Push and verify functions
    - multi_device: Multi-device context and operations
"""

import sys

# Track which modules loaded successfully
_loaded_modules = []
_failed_modules = []

# ==============================================================================
# CORE MODULE - Navigation and Exceptions
# ==============================================================================
try:
    from .core import (
        BackException,
        TopException,
        StepNavigator,
        show_breadcrumb,
        push_path,
        pop_path,
        set_path,
        set_wizard_state,
        get_wizard_state,
        int_prompt_nav,
        str_prompt_nav,
    )
    _loaded_modules.append('core')
except Exception as e:
    _failed_modules.append(('core', str(e)))
    print(f"Warning: Failed to load wizard.core module: {e}", file=sys.stderr)
    
    # Stub definitions
    class BackException(Exception):
        pass
    class TopException(Exception):
        pass
    def int_prompt_nav(prompt_text: str, default: int = None, **kwargs) -> int:
        from rich.prompt import IntPrompt
        return IntPrompt.ask(prompt_text, default=default)
    def str_prompt_nav(prompt_text: str, default: str = None, **kwargs) -> str:
        from rich.prompt import Prompt
        return Prompt.ask(prompt_text, default=default)

# ==============================================================================
# UI MODULE - Console and Display Functions
# ==============================================================================
try:
    from .ui import (
        console,
        print_wizard_banner,
        display_split_view,
        show_section_summary,
        prompt_with_nav,
        input_with_nav,
        show_navigation_help,
        view_current_config,
    )
    _loaded_modules.append('ui')
except Exception as e:
    _failed_modules.append(('ui', str(e)))
    print(f"Warning: Failed to load wizard.ui module: {e}", file=sys.stderr)
    
    # Fallback console
    from rich.console import Console
    console = Console()

# ==============================================================================
# PARSERS MODULE - Config Parsing Functions
# ==============================================================================
try:
    from .parsers import (
        parse_existing_evpn_services,
        parse_existing_multihoming,
        parse_route_targets,
        build_interface_to_vlan_mapping,
        build_interface_to_rt_mapping,
        build_interface_to_rt_vlan_mapping,
        build_esi_groups_by_rt_vlan,
        build_rt_to_esi_mapping,
        get_lo0_ip_from_config,
        get_as_number_from_config,
        get_router_id_from_config,
        get_mpls_enabled_interfaces,
        extract_hierarchy_section,
        # New parsing functions for mirror config
        extract_lldp_section,
        extract_lacp_section,
        extract_bundle_interfaces,
        extract_acls_section,
        extract_qos_section,
        extract_routing_policy_section,
        # Advanced policy parsing
        parse_all_routing_policies,
        load_policies_from_config,
    )
    _loaded_modules.append('parsers')
except Exception as e:
    _failed_modules.append(('parsers', str(e)))
    print(f"Warning: Failed to load wizard.parsers module: {e}", file=sys.stderr)

# ==============================================================================
# VALIDATORS MODULE - Validation Functions
# ==============================================================================
try:
    from .validators import (
        get_dnos_limits,
        get_limit,
        validate_dnos_limits,
        show_dnos_limits_summary,
        validate_esi_format,
        validate_fxc_attachment,
    )
    _loaded_modules.append('validators')
except Exception as e:
    _failed_modules.append(('validators', str(e)))
    print(f"Warning: Failed to load wizard.validators module: {e}", file=sys.stderr)

# ==============================================================================
# SYSTEM MODULE - System Configuration
# ==============================================================================
try:
    from .system import configure_system
    _loaded_modules.append('system')
except Exception as e:
    _failed_modules.append(('system', str(e)))
    print(f"Warning: Failed to load wizard.system module: {e}", file=sys.stderr)

# ==============================================================================
# INTERFACES MODULE - Interface Configuration
# ==============================================================================
try:
    from .interfaces import (
        configure_interfaces,
        _configure_single_interface_type,
        _get_all_interfaces_from_config,
        categorize_interfaces_by_type,
        get_parent_interfaces,
        get_bundle_members,
        group_pwhe_subinterfaces_by_parent,
        get_pwhe_subinterfaces_only,
        get_lacp_config_for_bundles,
        get_interface_config_block,
        show_interface_mapping,
    )
    _loaded_modules.append('interfaces')
except Exception as e:
    _failed_modules.append(('interfaces', str(e)))
    print(f"Warning: Failed to load wizard.interfaces module: {e}", file=sys.stderr)

# ==============================================================================
# SERVICES MODULE - Service Configuration
# ==============================================================================
try:
    from .services import configure_services
    _loaded_modules.append('services')
except Exception as e:
    _failed_modules.append(('services', str(e)))
    print(f"Warning: Failed to load wizard.services module: {e}", file=sys.stderr)

# ==============================================================================
# BGP MODULE - BGP Configuration
# ==============================================================================
try:
    from .bgp import (
        configure_bgp,
        _configure_single_bgp_peer,
    )
    _loaded_modules.append('bgp')
except Exception as e:
    _failed_modules.append(('bgp', str(e)))
    print(f"Warning: Failed to load wizard.bgp module: {e}", file=sys.stderr)

# ==============================================================================
# IGP MODULE - IGP/ISIS Configuration
# ==============================================================================
try:
    from .igp import (
        configure_igp,
        ip_to_isis_net,
    )
    _loaded_modules.append('igp')
except Exception as e:
    _failed_modules.append(('igp', str(e)))
    print(f"Warning: Failed to load wizard.igp module: {e}", file=sys.stderr)

# ==============================================================================
# MULTIHOMING MODULE - ESI/Multihoming Configuration
# ==============================================================================
try:
    from .multihoming import (
        configure_multihoming,
        push_multihoming_to_existing,
        push_synchronized_multihoming,
        filter_multihoming_interfaces,
        extract_interface_number,
        generate_esi,
        match_esi_by_service,
        detect_neighbor_pe_with_mh,
        configure_df_invert_preference,
    )
    _loaded_modules.append('multihoming')
except Exception as e:
    _failed_modules.append(('multihoming', str(e)))
    print(f"Warning: Failed to load wizard.multihoming module: {e}", file=sys.stderr)

# ==============================================================================
# PUSH MODULE - Push and Verify Functions
# ==============================================================================
try:
    from .push import (
        push_and_verify,
        ask_push_method,
        suggest_error_fix,
        show_diff_preview,
        delete_hierarchy,
        show_delete_hierarchy_menu,
        confirm_delete_hierarchy,
        execute_delete_hierarchy,
        HIERARCHY_DELETE_COMMANDS,
        HIERARCHY_DISPLAY_NAMES,
        CRITICAL_HIERARCHIES,
        # Multi-device delete operations
        SUB_HIERARCHY_DELETE_COMMANDS,
        delete_sub_hierarchy,
        delete_interface_range,
        delete_hierarchy_multi,
        show_delete_hierarchy_menu_multi,
        execute_delete_hierarchy_multi,
    )
    _loaded_modules.append('push')
except Exception as e:
    _failed_modules.append(('push', str(e)))
    print(f"Warning: Failed to load wizard.push module: {e}", file=sys.stderr)

# ==============================================================================
# INTERFACE_MAPPER MODULE - Multi-Device Interface Mapping
# ==============================================================================
try:
    from .interface_mapper import (
        InterfaceMapper,
        select_interface_mapping_mode,
        show_interface_mapping_preview,
    )
    _loaded_modules.append('interface_mapper')
except Exception as e:
    _failed_modules.append(('interface_mapper', str(e)))
    print(f"Warning: Failed to load wizard.interface_mapper module: {e}", file=sys.stderr)

# ==============================================================================
# MULTI_DEVICE MODULE - Multi-Device Context
# ==============================================================================
try:
    from .multi_device import (
        MultiDeviceContext,
        DeviceSummary,
        select_multiple_devices,
        show_quick_load_menu,
        _show_multi_device_compare,
        _refresh_multi_device_configs,
        _show_multi_device_sync_status,
        _push_config_to_all_devices,
        _show_delete_files_menu,
        # Service interface modification
        parse_service_interfaces,
        modify_service_interfaces,
        show_modify_service_interfaces_menu,
    )
    _loaded_modules.append('multi_device')
except Exception as e:
    _failed_modules.append(('multi_device', str(e)))
    print(f"Warning: Failed to load wizard.multi_device module: {e}", file=sys.stderr)

# ==============================================================================
# MIRROR_CONFIG MODULE - Configuration Mirroring
# ==============================================================================
try:
    from .mirror_config import (
        ConfigMirror,
        show_mirror_analysis,
        select_interface_mapping_strategy,
        configure_custom_interface_mapping,
        run_mirror_config_wizard,
        run_multi_target_mirror_wizard,
        run_mirror_system_only_wizard,
    )
    _loaded_modules.append('mirror_config')
except Exception as e:
    _failed_modules.append(('mirror_config', str(e)))
    print(f"Warning: Failed to load wizard.mirror_config module: {e}", file=sys.stderr)

# ==============================================================================
# SYSTEM_RESTORE MODULE - Recovery Mode System Restore
# ==============================================================================
try:
    from .system_restore import (
        DeviceKnowledge,
        run_system_restore_wizard,
        check_recovery_and_prompt,
        show_device_knowledge_panel,
        execute_restore_to_gi_mode,
        prompt_image_source_redirect,
    )
    _loaded_modules.append('system_restore')
except Exception as e:
    _failed_modules.append(('system_restore', str(e)))
    print(f"Warning: Failed to load wizard.system_restore module: {e}", file=sys.stderr)

# ==============================================================================
# POLICIES MODULE - Advanced Policy Engine
# ==============================================================================
try:
    from .policies import (
        PolicyManager,
        PrefixList,
        PrefixListRule,
        CommunityList,
        CommunityListRule,
        ExtCommunityList,
        ExtCommunityListRule,
        LargeCommunityList,
        LargeCommunityListRule,
        AsPathList,
        AsPathListRule,
        RoutingPolicy,
        PolicyRule,
        MatchCondition,
        SetAction,
        RuleAction,
        MatchType,
        SetActionType,
        OnMatchAction,
        PrefixListBuilder,
        CommunityListBuilder,
        ExtCommunityListBuilder,
        LargeCommunityListBuilder,
        AsPathListBuilder,
        PolicyBuilder,
        PolicySuggester,
        suggest_policy_name,
        format_policy_for_display,
    )
    _loaded_modules.append('policies')
except Exception as e:
    _failed_modules.append(('policies', str(e)))
    print(f"Warning: Failed to load wizard.policies module: {e}", file=sys.stderr)

# ==============================================================================
# POLICY VALIDATOR MODULE - Policy Validation Engine
# ==============================================================================
try:
    from .policy_validator import (
        PolicyValidator,
        ValidationResult,
        ValidationIssue,
        ValidationSeverity,
        validate_policy_manager,
        validate_and_display,
    )
    _loaded_modules.append('policy_validator')
except Exception as e:
    _failed_modules.append(('policy_validator', str(e)))
    print(f"Warning: Failed to load wizard.policy_validator module: {e}", file=sys.stderr)

# ==============================================================================
# POLICY TEMPLATES MODULE - Pre-built Policy Templates
# ==============================================================================
try:
    from .policy_templates import (
        PolicyTemplate,
        TemplateVariable,
        PolicyTemplateEngine,
    )
    _loaded_modules.append('policy_templates')
except Exception as e:
    _failed_modules.append(('policy_templates', str(e)))
    print(f"Warning: Failed to load wizard.policy_templates module: {e}", file=sys.stderr)

# ==============================================================================
# MAIN WIZARD FUNCTIONS
# ==============================================================================
try:
    from .main import (
        run_wizard,
        select_device,
        fetch_current_config,
        display_hierarchy_config,
        select_configuration_mode,
        show_current_config_summary,
        _calculate_scale_info,
        calculate_next_ip,
        _get_config_history_path,
        _save_config_history,
        _mark_config_validated,
        _mark_config_pushed,
        _load_config_history,
    )
    _loaded_modules.append('main')
except Exception as e:
    _failed_modules.append(('main', str(e)))
    print(f"Warning: Failed to load wizard.main module: {e}", file=sys.stderr)


def get_module_status():
    """Get status of loaded/failed modules for debugging."""
    return {
        'loaded': _loaded_modules.copy(),
        'failed': _failed_modules.copy(),
    }


def check_modules():
    """Print module status for debugging."""
    print(f"Loaded modules: {', '.join(_loaded_modules) if _loaded_modules else 'none'}")
    if _failed_modules:
        print(f"Failed modules:")
        for mod, err in _failed_modules:
            print(f"  - {mod}: {err}")


# Public API
__all__ = [
    # Core
    'BackException',
    'TopException',
    'StepNavigator',
    'show_breadcrumb',
    'push_path',
    'pop_path',
    'set_path',
    'set_wizard_state',
    'get_wizard_state',
    'int_prompt_nav',
    'str_prompt_nav',
    
    # UI
    'console',
    'print_wizard_banner',
    'display_split_view',
    'show_section_summary',
    'prompt_with_nav',
    'input_with_nav',
    'show_navigation_help',
    'view_current_config',
    
    # Parsers
    'parse_existing_evpn_services',
    'parse_existing_multihoming',
    'parse_route_targets',
    'build_interface_to_vlan_mapping',
    'build_interface_to_rt_mapping',
    'build_interface_to_rt_vlan_mapping',
    'build_esi_groups_by_rt_vlan',
    'build_rt_to_esi_mapping',
    'get_lo0_ip_from_config',
    'get_as_number_from_config',
    'get_router_id_from_config',
    'get_mpls_enabled_interfaces',
    'extract_hierarchy_section',
    'extract_lldp_section',
    'extract_lacp_section',
    'extract_bundle_interfaces',
    'extract_acls_section',
    'extract_qos_section',
    'extract_routing_policy_section',
    'parse_all_routing_policies',
    'load_policies_from_config',
    
    # Validators
    'get_dnos_limits',
    'get_limit',
    'validate_dnos_limits',
    'show_dnos_limits_summary',
    'validate_esi_format',
    'validate_fxc_attachment',
    
    # Hierarchies
    'configure_system',
    'configure_interfaces',
    '_configure_single_interface_type',
    'configure_services',
    'configure_bgp',
    '_configure_single_bgp_peer',
    'configure_igp',
    'ip_to_isis_net',
    'configure_multihoming',
    'push_multihoming_to_existing',
    'push_synchronized_multihoming',
    'configure_df_invert_preference',
    
    # Interface helpers
    '_get_all_interfaces_from_config',
    'categorize_interfaces_by_type',
    'get_parent_interfaces',
    'get_bundle_members',
    'group_pwhe_subinterfaces_by_parent',
    'get_pwhe_subinterfaces_only',
    'get_lacp_config_for_bundles',
    'get_interface_config_block',
    'show_interface_mapping',
    
    # MH helpers
    'filter_multihoming_interfaces',
    'extract_interface_number',
    'generate_esi',
    'match_esi_by_service',
    'detect_neighbor_pe_with_mh',
    
    # Push
    'push_and_verify',
    'ask_push_method',
    'suggest_error_fix',
    'show_diff_preview',
    
    # Interface Mapper
    'InterfaceMapper',
    'select_interface_mapping_mode',
    'show_interface_mapping_preview',
    
    # Multi-device
    'MultiDeviceContext',
    'DeviceSummary',
    'select_multiple_devices',
    'show_quick_load_menu',
    '_show_multi_device_compare',
    '_refresh_multi_device_configs',
    '_show_multi_device_sync_status',
    '_push_config_to_all_devices',
    '_show_delete_files_menu',
    
    # Main
    'run_wizard',
    'select_device',
    'fetch_current_config',
    'display_hierarchy_config',
    'select_configuration_mode',
    'show_current_config_summary',
    '_calculate_scale_info',
    'calculate_next_ip',
    '_get_config_history_path',
    '_save_config_history',
    '_mark_config_validated',
    '_mark_config_pushed',
    '_load_config_history',
    
    # Mirror Config
    'ConfigMirror',
    'show_mirror_analysis',
    'select_interface_mapping_strategy',
    'configure_custom_interface_mapping',
    'run_mirror_config_wizard',
    'run_multi_target_mirror_wizard',
    'run_mirror_system_only_wizard',
    
    # System Restore (Recovery Mode)
    'DeviceKnowledge',
    'run_system_restore_wizard',
    'check_recovery_and_prompt',
    'show_device_knowledge_panel',
    'execute_restore_to_gi_mode',
    'prompt_image_source_redirect',
    
    # Policies (Advanced Policy Engine)
    'PolicyManager',
    'PrefixList',
    'PrefixListRule',
    'CommunityList',
    'CommunityListRule',
    'ExtCommunityList',
    'ExtCommunityListRule',
    'LargeCommunityList',
    'LargeCommunityListRule',
    'AsPathList',
    'AsPathListRule',
    'RoutingPolicy',
    'PolicyRule',
    'MatchCondition',
    'SetAction',
    'RuleAction',
    'MatchType',
    'SetActionType',
    'OnMatchAction',
    'PrefixListBuilder',
    'CommunityListBuilder',
    'ExtCommunityListBuilder',
    'LargeCommunityListBuilder',
    'AsPathListBuilder',
    'PolicyBuilder',
    'PolicySuggester',
    'suggest_policy_name',
    'format_policy_for_display',
    
    # Policy Validator
    'PolicyValidator',
    'ValidationResult',
    'ValidationIssue',
    'ValidationSeverity',
    'validate_policy_manager',
    'validate_and_display',
    
    # Policy Templates
    'PolicyTemplate',
    'TemplateVariable',
    'PolicyTemplateEngine',
    
    # Debug
    'get_module_status',
    'check_modules',
]

