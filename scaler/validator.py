"""Configuration validator for DNOS scale limits."""

from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class ValidationResult:
    """Result of validation check."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    recommendations: List[str]


# DNOS 25.4 Scale Limits (verified from limits.json and DNOS source)
DNOS_LIMITS = {
    # Interface limits - based on ifindex pool capacities
    "interfaces_total": 8000,  # L3 internal index limit for ALL datapath interfaces
    "interfaces_physical": 1024,
    "interfaces_bundle": 512,
    "interfaces_bundle_members": 64,
    "interfaces_loopback": 256,
    "interfaces_irb": 4096,  # IRB pool (ifindex 41985-46080)
    "interfaces_pwhe": 4000,  # PH pool capacity (phX + phX.Y max 4000)
    "interfaces_pwhe_qinq": 4000,  # Stag pool (ifindex 88001-92000)
    "interfaces_subif_per_parent": 4000,
    "interfaces_physical_subif": 20480,  # VLAN pool (ifindex 13313-33792)
    
    # BGP limits
    "bgp_peers": 2000,
    "bgp_peer_groups": 256,
    "bgp_routes": 10000000,
    
    # Service limits
    "services_fxc": 8000,  # Max FXC instances from limits.json
    "services_vrf": 4096,
    "services_evpn": 4000,  # Max EVPN instances from limits.json
    "services_vpws": 8000,
    "services_bridge_domain": 16000,
    
    # VLAN limits
    "vlans": 4094,
    "vlan_subinterfaces": 20480,  # VLAN pool capacity
    
    # Protocol limits
    "isis_interfaces": 1024,
    "ospf_interfaces": 1024,
    "ldp_interfaces": 1024,
    
    # Multihoming limits
    "multihoming_esi": 2000,  # Max interfaces with ESI
}


class Validator:
    """Validates configuration against DNOS limits."""
    
    def __init__(self, limits: Dict[str, int] = None):
        """Initialize validator with optional custom limits.
        
        Args:
            limits: Custom limits to override defaults
        """
        self.limits = DNOS_LIMITS.copy()
        if limits:
            self.limits.update(limits)
    
    def validate_interfaces(
        self,
        current_count: int,
        new_count: int,
        interface_type: str = "total"
    ) -> ValidationResult:
        """Validate interface count against limits.
        
        Args:
            current_count: Current number of interfaces
            new_count: Number of interfaces to add
            interface_type: Type of interface (total, physical, bundle, etc.)
            
        Returns:
            ValidationResult with status and messages
        """
        errors = []
        warnings = []
        recommendations = []
        
        limit_key = f"interfaces_{interface_type}"
        limit = self.limits.get(limit_key, self.limits["interfaces_total"])
        
        total = current_count + new_count
        
        if total > limit:
            errors.append(
                f"Interface count ({total}) exceeds limit ({limit}) for {interface_type}"
            )
        elif total > limit * 0.9:
            warnings.append(
                f"Interface count ({total}) is at {total/limit*100:.0f}% of limit ({limit})"
            )
            recommendations.append("Consider reviewing interface usage before adding more")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            recommendations=recommendations
        )
    
    def validate_services(
        self,
        current_count: int,
        new_count: int,
        service_type: str
    ) -> ValidationResult:
        """Validate service count against limits.
        
        Args:
            current_count: Current number of services
            new_count: Number of services to add
            service_type: Type of service (fxc, vrf, evpn, etc.)
            
        Returns:
            ValidationResult with status and messages
        """
        errors = []
        warnings = []
        recommendations = []
        
        # Map service type to limit key
        type_map = {
            "evpn-vpws-fxc": "services_fxc",
            "fxc": "services_fxc",
            "vrf": "services_vrf",
            "evpn": "services_evpn",
            "vpws": "services_vpws",
            "bridge-domain": "services_bridge_domain",
        }
        
        limit_key = type_map.get(service_type, f"services_{service_type}")
        limit = self.limits.get(limit_key, 10000)
        
        total = current_count + new_count
        
        if total > limit:
            errors.append(
                f"Service count ({total}) exceeds limit ({limit}) for {service_type}"
            )
        elif total > limit * 0.9:
            warnings.append(
                f"Service count ({total}) is at {total/limit*100:.0f}% of limit ({limit})"
            )
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            recommendations=recommendations
        )
    
    def validate_bgp_peers(
        self,
        current_count: int,
        new_count: int
    ) -> ValidationResult:
        """Validate BGP peer count against limits.
        
        Args:
            current_count: Current number of BGP peers
            new_count: Number of peers to add
            
        Returns:
            ValidationResult with status and messages
        """
        errors = []
        warnings = []
        recommendations = []
        
        limit = self.limits["bgp_peers"]
        total = current_count + new_count
        
        if total > limit:
            errors.append(f"BGP peer count ({total}) exceeds limit ({limit})")
        elif total > limit * 0.9:
            warnings.append(f"BGP peer count ({total}) is at {total/limit*100:.0f}% of limit")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            recommendations=recommendations
        )
    
    def validate_vlans(
        self,
        current_count: int,
        new_count: int
    ) -> ValidationResult:
        """Validate VLAN count against limits.
        
        Args:
            current_count: Current number of VLANs
            new_count: Number of VLANs to add
            
        Returns:
            ValidationResult with status and messages
        """
        errors = []
        warnings = []
        recommendations = []
        
        limit = self.limits["vlans"]
        total = current_count + new_count
        
        if total > limit:
            errors.append(f"VLAN count ({total}) exceeds limit ({limit})")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            recommendations=recommendations
        )
    
    def validate_all(
        self,
        current_state: Dict[str, int],
        new_config: Dict[str, int]
    ) -> ValidationResult:
        """Validate all aspects of new configuration.
        
        Args:
            current_state: Current counts by type
            new_config: New counts to add by type
            
        Returns:
            Combined ValidationResult
        """
        all_errors = []
        all_warnings = []
        all_recommendations = []
        
        # Validate each type
        for key, new_count in new_config.items():
            current = current_state.get(key, 0)
            
            if key.startswith("interface"):
                result = self.validate_interfaces(current, new_count, key.replace("interfaces_", ""))
            elif key.startswith("service"):
                result = self.validate_services(current, new_count, key.replace("services_", ""))
            elif key == "bgp_peers":
                result = self.validate_bgp_peers(current, new_count)
            elif key == "vlans":
                result = self.validate_vlans(current, new_count)
            else:
                continue
            
            all_errors.extend(result.errors)
            all_warnings.extend(result.warnings)
            all_recommendations.extend(result.recommendations)
        
        return ValidationResult(
            is_valid=len(all_errors) == 0,
            errors=all_errors,
            warnings=all_warnings,
            recommendations=all_recommendations
        )
    
    def get_available_capacity(self, current_state: Dict[str, int]) -> Dict[str, int]:
        """Calculate remaining capacity for each resource type.
        
        Args:
            current_state: Current counts by type
            
        Returns:
            Dictionary of available capacity by type
        """
        capacity = {}
        
        for limit_key, limit_value in self.limits.items():
            current = current_state.get(limit_key, 0)
            capacity[limit_key] = max(0, limit_value - current)
        
        return capacity














