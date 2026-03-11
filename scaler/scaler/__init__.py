"""SCALER - Scaled Configuration Automation for Large Enterprise Routers.

A comprehensive toolset for managing large-scale DNOS device configurations.
"""

# Suppress the "found in sys.modules after import" warning from runpy
import warnings
warnings.filterwarnings("ignore", message=".*found in sys.modules after import.*", category=RuntimeWarning)

__version__ = "2.0.0"

# Core models
from .models import (
    Device,
    Platform,
    DeviceConfig,
    HierarchyAction,
    NamingPattern,
    NamingFormat,
    VlanType,
    HierarchyConfig,
    InterfaceScaleInput,
    ServiceScaleInput,
    BGPScaleInput,
    BatchScaleConfig,
    WizardState,
    ValidationResult,
    InterfaceScale,
    ServiceScale,
    BGPPeerScale,
    ScaleConfig,
    ServiceType,
    InterfaceType,
)

# Device management
from .device_manager import DeviceManager

# Configuration handling
from .config_extractor import ConfigExtractor
from .config_parser import ConfigParser
from .config_pusher import ConfigPusher

# Generation and validation
from .scale_generator import ScaleGenerator
from .validator import Validator
from .diff_generator import DiffGenerator
from .verifier import Verifier, VerificationStatus

# Pattern parsing
from .pattern_parser import PatternParser, parse_count_input

# CLI validation
from .cli_validator import CLIValidator, ValidationSeverity

# Network-mapper integration (optional, lazy import to avoid slow MCP loading)
# Import these only when explicitly requested via get_network_mapper_imports()
NETWORK_MAPPER_AVAILABLE = False
NetworkMapperClient = None
Topology = None
TopologyDevice = None
InterfaceInfo = None
LLDPNeighbor = None
get_mapper_client = None

def get_network_mapper_imports():
    """Lazy import network mapper client to avoid slow MCP package loading."""
    global NETWORK_MAPPER_AVAILABLE, NetworkMapperClient, Topology, TopologyDevice
    global InterfaceInfo, LLDPNeighbor, get_mapper_client
    
    if NETWORK_MAPPER_AVAILABLE:
        return True
    
    try:
        from .network_mapper_client import (
            NetworkMapperClient as _NetworkMapperClient,
            Topology as _Topology,
            TopologyDevice as _TopologyDevice,
            InterfaceInfo as _InterfaceInfo,
            LLDPNeighbor as _LLDPNeighbor,
            get_mapper_client as _get_mapper_client,
        )
        NetworkMapperClient = _NetworkMapperClient
        Topology = _Topology
        TopologyDevice = _TopologyDevice
        InterfaceInfo = _InterfaceInfo
        LLDPNeighbor = _LLDPNeighbor
        get_mapper_client = _get_mapper_client
        NETWORK_MAPPER_AVAILABLE = True
        return True
    except ImportError:
        return False

# Wizard subpackage re-exports
from .wizard import (
    BackException,
    TopException,
    MultiDeviceContext,
    DeviceSummary,
)

# Main entry point - lazy import to avoid slow MCP loading for monitor.py
# Use get_wizard() instead of direct import
_run_wizard = None

def get_wizard():
    """Lazy import run_wizard to avoid slow MCP package loading in monitor."""
    global _run_wizard
    if _run_wizard is None:
        from .interactive_scale import run_wizard as _wizard
        _run_wizard = _wizard
    return _run_wizard

def run_wizard(*args, **kwargs):
    """Wrapper that lazy-loads the real run_wizard."""
    return get_wizard()(*args, **kwargs)

__all__ = [
    # Version
    '__version__',
    
    # Models
    'Device',
    'Platform',
    'DeviceConfig',
    'HierarchyAction',
    'NamingPattern',
    'NamingFormat',
    'VlanType',
    'HierarchyConfig',
    'InterfaceScaleInput',
    'ServiceScaleInput',
    'BGPScaleInput',
    'BatchScaleConfig',
    'WizardState',
    'ValidationResult',
    'InterfaceScale',
    'ServiceScale',
    'BGPPeerScale',
    'ScaleConfig',
    'ServiceType',
    'InterfaceType',
    
    # Core classes
    'DeviceManager',
    'ConfigExtractor',
    'ConfigParser',
    'ConfigPusher',
    'ScaleGenerator',
    'Validator',
    'DiffGenerator',
    'Verifier',
    'VerificationStatus',
    'PatternParser',
    'parse_count_input',
    'CLIValidator',
    'ValidationSeverity',
    
    # Network-mapper (optional)
    'NetworkMapperClient',
    'Topology',
    'TopologyDevice',
    'InterfaceInfo',
    'LLDPNeighbor',
    'get_mapper_client',
    'NETWORK_MAPPER_AVAILABLE',
    
    # Wizard
    'BackException',
    'TopException',
    'MultiDeviceContext',
    'DeviceSummary',
    'run_wizard',
]
