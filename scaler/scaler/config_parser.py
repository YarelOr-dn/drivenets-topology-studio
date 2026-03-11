"""Parse DNOS configuration into structured data."""

import re
from typing import Dict, List, Any, Optional, Tuple
from .models import PreservedConfig


class ConfigParser:
    """Parse DNOS running configuration text into structured data."""

    # Patterns for identifying configuration sections
    INTERFACE_PATTERN = re.compile(r'^interfaces\s*\{', re.MULTILINE)
    PROTOCOLS_PATTERN = re.compile(r'^protocols\s*\{', re.MULTILINE)
    SYSTEM_PATTERN = re.compile(r'^system\s*\{', re.MULTILINE)
    ROUTING_POLICY_PATTERN = re.compile(r'^routing-policy\s*\{', re.MULTILINE)
    NETWORK_SERVICES_PATTERN = re.compile(r'^network-services\s*\{', re.MULTILINE)
    ROUTING_OPTIONS_PATTERN = re.compile(r'^routing-options\s*\{', re.MULTILINE)
    
    # Interface name pattern
    INTERFACE_NAME_PATTERN = re.compile(
        r'(ge\d+-\d+/\d+/\d+(?:\.\d+)?|'
        r'bundle\d+(?:\.\d+)?|'
        r'ph\d+(?:\.\d+)?|'
        r'lo\d+|'
        r'irb\d+|'
        r'pwhe\d+)'
    )

    def __init__(self):
        """Initialize the config parser."""
        pass

    def parse(self, config_text: str) -> Dict[str, Any]:
        """
        Parse the full configuration into structured data.
        
        Args:
            config_text: Raw DNOS configuration text
        
        Returns:
            Dict with parsed configuration sections
        """
        result = {
            "interfaces": {},
            "protocols": {},
            "system": {},
            "routing_policy": {},
            "network_services": {},
            "routing_options": {},
            "raw_sections": {}
        }
        
        # Extract each major section
        result["raw_sections"]["interfaces"] = self._extract_section(config_text, "interfaces")
        result["raw_sections"]["protocols"] = self._extract_section(config_text, "protocols")
        result["raw_sections"]["system"] = self._extract_section(config_text, "system")
        result["raw_sections"]["routing_policy"] = self._extract_section(config_text, "routing-policy")
        result["raw_sections"]["network_services"] = self._extract_section(config_text, "network-services")
        result["raw_sections"]["routing_options"] = self._extract_section(config_text, "routing-options")
        
        # Parse interfaces
        if result["raw_sections"]["interfaces"]:
            result["interfaces"] = self._parse_interfaces(result["raw_sections"]["interfaces"])
        
        # Parse protocols (identify BGP, IS-IS, OSPF, etc.)
        if result["raw_sections"]["protocols"]:
            result["protocols"] = self._parse_protocols(result["raw_sections"]["protocols"])
        
        # Parse system
        if result["raw_sections"]["system"]:
            result["system"] = self._parse_system(result["raw_sections"]["system"])
        
        return result

    def _extract_section(self, config_text: str, section_name: str) -> Optional[str]:
        """
        Extract a complete configuration section.
        Handles both brace-style ({}) and indentation-style (!) config formats.
        
        Args:
            config_text: Full configuration text
            section_name: Section name (e.g., "interfaces", "protocols")
        
        Returns:
            Section text or None if not found
        """
        # Try brace-style first: section_name {
        pattern_brace = re.compile(rf'^{section_name}\s*\{{', re.MULTILINE)
        match = pattern_brace.search(config_text)
        
        if match:
            # Brace-style config
            start = match.start()
            brace_start = match.end() - 1
            
            brace_count = 1
            pos = brace_start + 1
            
            while pos < len(config_text) and brace_count > 0:
                if config_text[pos] == '{':
                    brace_count += 1
                elif config_text[pos] == '}':
                    brace_count -= 1
                pos += 1
            
            if brace_count == 0:
                return config_text[start:pos]
            return None
        
        # Try indentation-style: section_name\n  content\n!
        pattern_indent = re.compile(rf'^{section_name}\s*$', re.MULTILINE)
        match = pattern_indent.search(config_text)
        
        if match:
            # Indentation-style config - section ends at unindented line or next section
            start = match.start()
            lines = config_text[start:].split('\n')
            section_lines = [lines[0]]  # Include the section header
            
            for i, line in enumerate(lines[1:], 1):
                # Check if this is the end of the section
                # Section ends when we hit an unindented non-empty line (next top-level section)
                if line and not line[0].isspace() and line.strip() != '!':
                    # Check if it's a new section (not just a comment)
                    if not line.strip().startswith('#'):
                        break
                section_lines.append(line)
            
            return '\n'.join(section_lines)
        
        return None

    def _parse_interfaces(self, interfaces_text: str) -> Dict[str, Any]:
        """
        Parse the interfaces section.
        Handles both brace-style and indentation-style config formats.
        
        Args:
            interfaces_text: Interfaces section text
        
        Returns:
            Dict of interface configurations
        """
        interfaces = {}
        
        # Detect format: brace-style has '{', indentation-style uses '!' as block end
        is_brace_style = '{' in interfaces_text
        
        lines = interfaces_text.split('\n')
        current_interface = None
        current_content = []
        
        if is_brace_style:
            # Brace-style parsing
            brace_depth = 0
            
            for line in lines:
                stripped = line.strip()
                
                if not stripped or stripped.startswith('/*') or stripped.startswith('//'):
                    continue
                
                match = self.INTERFACE_NAME_PATTERN.match(stripped)
                if match and brace_depth == 1:
                    if current_interface:
                        interfaces[current_interface] = self._build_interface_info(current_content)
                    current_interface = match.group(1)
                    current_content = [line]
                elif current_interface:
                    current_content.append(line)
                
                brace_depth += stripped.count('{') - stripped.count('}')
        else:
            # Indentation-style parsing (uses '!' as block delimiter)
            for line in lines:
                stripped = line.strip()
                
                # Skip empty lines, comments, and header
                if not stripped or stripped.startswith('#'):
                    continue
                if stripped == 'interfaces':  # Skip section header
                    continue
                
                # Calculate indentation level
                indent = len(line) - len(line.lstrip())
                
                # Interface names are at first indentation level (typically 2 spaces)
                # and match interface pattern
                match = self.INTERFACE_NAME_PATTERN.match(stripped)
                if match and indent <= 2:
                    # Save previous interface
                    if current_interface:
                        interfaces[current_interface] = self._build_interface_info(current_content)
                    current_interface = match.group(1)
                    current_content = [line]
                elif current_interface:
                    # Content belongs to current interface (higher indentation)
                    if stripped == '!' and indent <= 2:
                        # Block end marker at interface level - save and reset
                        interfaces[current_interface] = self._build_interface_info(current_content)
                        current_interface = None
                        current_content = []
                    else:
                        current_content.append(line)
        
        # Don't forget the last interface
        if current_interface:
            interfaces[current_interface] = self._build_interface_info(current_content)
        
        return interfaces

    def _build_interface_info(self, content_lines: list) -> Dict[str, Any]:
        """Build interface info dict from content lines."""
        config = '\n'.join(content_lines)
        return {
            "config": config,
            "has_igp": self._interface_has_igp(config),
            "has_l2_service": 'l2-service' in config,
            "has_ipv4": 'ipv4-address' in config,
            "has_ipv6": 'ipv6-address' in config,
        }

    def _interface_has_igp(self, config: str) -> bool:
        """Check if interface configuration references an IGP."""
        igp_keywords = ['isis', 'ospf', 'ldp', 'mpls', 'rsvp']
        config_lower = config.lower()
        return any(kw in config_lower for kw in igp_keywords)

    def _parse_protocols(self, protocols_text: str) -> Dict[str, Any]:
        """
        Parse the protocols section.
        
        Args:
            protocols_text: Protocols section text
        
        Returns:
            Dict of protocol configurations
        """
        protocols = {
            "bgp": None,
            "isis": None,
            "ospf": None,
            "ldp": None,
            "mpls": None,
            "lacp": None,
            "bfd": None,
        }
        
        for proto in protocols.keys():
            section = self._extract_subsection(protocols_text, proto)
            if section:
                protocols[proto] = {
                    "raw": section,
                    "present": True
                }
                
                # Extract additional BGP info
                if proto == "bgp":
                    protocols[proto]["local_as"] = self._extract_bgp_as(section)
                    protocols[proto]["router_id"] = self._extract_router_id(section)
        
        return protocols

    def _parse_system(self, system_text: str) -> Dict[str, Any]:
        """
        Parse the system section.
        
        Args:
            system_text: System section text
        
        Returns:
            Dict of system configuration
        """
        system = {
            "raw": system_text,
            "hostname": None,
            "profile": None,
            "has_login": "login" in system_text,
            "has_ntp": "ntp" in system_text,
            "has_ssh": "ssh" in system_text,
            "has_snmp": "snmp" in system_text,
        }
        
        # Extract hostname
        hostname_match = re.search(r'name\s+(\S+)', system_text)
        if hostname_match:
            system["hostname"] = hostname_match.group(1)
        
        # Extract profile
        if "profile l3_pe" in system_text:
            system["profile"] = "l3_pe"
        
        return system

    def _extract_subsection(self, text: str, section_name: str) -> Optional[str]:
        """Extract a subsection from within a larger section.
        Handles both brace-style and indentation-style configs.
        """
        # Try brace-style first
        pattern_brace = re.compile(rf'\b{section_name}\s*\{{', re.IGNORECASE)
        match = pattern_brace.search(text)
        
        if match:
            start = match.start()
            brace_start = match.end() - 1
            
            brace_count = 1
            pos = brace_start + 1
            
            while pos < len(text) and brace_count > 0:
                if text[pos] == '{':
                    brace_count += 1
                elif text[pos] == '}':
                    brace_count -= 1
                pos += 1
            
            if brace_count == 0:
                return text[start:pos]
            return None
        
        # Try indentation-style: "  section_name" or "  section_name <value>"
        pattern_indent = re.compile(rf'^\s+{section_name}(?:\s+\S+)?\s*$', re.MULTILINE | re.IGNORECASE)
        match = pattern_indent.search(text)
        
        if match:
            start = match.start()
            start_indent = len(text[start:].split('\n')[0]) - len(text[start:].split('\n')[0].lstrip())
            
            lines = text[start:].split('\n')
            section_lines = [lines[0]]
            
            for line in lines[1:]:
                if not line.strip() or line.strip() == '!':
                    continue
                # Calculate indentation
                current_indent = len(line) - len(line.lstrip())
                # If indentation is less than or equal to section start, we've exited
                if current_indent <= start_indent and line.strip():
                    break
                section_lines.append(line)
            
            return '\n'.join(section_lines)
        
        return None

    def _extract_bgp_as(self, bgp_text: str) -> Optional[int]:
        """Extract the local AS number from BGP config.
        Handles both 'local-as N' and 'bgp N' (AS on same line) formats.
        """
        # Try 'local-as N' format first
        as_match = re.search(r'local-as\s+(\d+)', bgp_text)
        if as_match:
            return int(as_match.group(1))
        
        # Try 'bgp N' format (AS number on the bgp line itself)
        as_match = re.search(r'^\s*bgp\s+(\d+)', bgp_text, re.MULTILINE)
        if as_match:
            return int(as_match.group(1))
        
        return None

    def _extract_router_id(self, text: str) -> Optional[str]:
        """Extract router-id from config."""
        rid_match = re.search(r'router-id\s+(\d+\.\d+\.\d+\.\d+)', text)
        if rid_match:
            return rid_match.group(1)
        return None

    def identify_wan_interfaces(self, parsed_config: Dict[str, Any]) -> List[str]:
        """
        Identify WAN interfaces (those attached to IGP protocols).
        
        Args:
            parsed_config: Parsed configuration dict
        
        Returns:
            List of WAN interface names
        """
        wan_interfaces = []
        
        interfaces = parsed_config.get("interfaces", {})
        protocols = parsed_config.get("protocols", {})
        
        # Method 1: Interfaces with IGP references
        for iface_name, iface_data in interfaces.items():
            if iface_data.get("has_igp"):
                wan_interfaces.append(iface_name)
        
        # Method 2: Check protocol configs for interface references
        for proto_name in ["isis", "ospf", "ldp", "mpls"]:
            proto_config = protocols.get(proto_name)
            if proto_config and proto_config.get("raw"):
                # Find interfaces referenced in protocol config
                matches = self.INTERFACE_NAME_PATTERN.findall(proto_config["raw"])
                wan_interfaces.extend(matches)
        
        # Deduplicate and sort
        return sorted(set(wan_interfaces))

    def extract_preserved_config(self, config_text: str) -> PreservedConfig:
        """
        Extract all configuration that should be preserved.
        
        Args:
            config_text: Full configuration text
        
        Returns:
            PreservedConfig object
        """
        parsed = self.parse(config_text)
        wan_interfaces = self.identify_wan_interfaces(parsed)
        
        # Build preserved config text (WAN interfaces + protocols + system + routing-policy)
        preserved_parts = []
        
        # Preserve WAN interfaces
        if parsed["interfaces"]:
            preserved_parts.append("interfaces {")
            for iface_name in wan_interfaces:
                if iface_name in parsed["interfaces"]:
                    preserved_parts.append(parsed["interfaces"][iface_name]["config"])
            preserved_parts.append("}")
        
        # Preserve full protocols section
        if parsed["raw_sections"]["protocols"]:
            preserved_parts.append(parsed["raw_sections"]["protocols"])
        
        # Preserve full system section
        if parsed["raw_sections"]["system"]:
            preserved_parts.append(parsed["raw_sections"]["system"])
        
        # Preserve full routing-policy section
        if parsed["raw_sections"]["routing_policy"]:
            preserved_parts.append(parsed["raw_sections"]["routing_policy"])
        
        # Preserve routing-options section
        if parsed["raw_sections"]["routing_options"]:
            preserved_parts.append(parsed["raw_sections"]["routing_options"])
        
        return PreservedConfig(
            wan_interfaces=wan_interfaces,
            protocols=parsed["protocols"],
            system=parsed["system"],
            routing_policy={"raw": parsed["raw_sections"]["routing_policy"]},
            raw_text='\n'.join(preserved_parts)
        )

    def get_interface_count(self, parsed_config: Dict[str, Any]) -> Dict[str, int]:
        """
        Count interfaces by type.
        
        Args:
            parsed_config: Parsed configuration dict
        
        Returns:
            Dict with counts per interface type
        """
        counts = {
            "physical": 0,
            "subinterfaces": 0,
            "bundles": 0,
            "loopbacks": 0,
            "irb": 0,
            "pwhe": 0,
            "total": 0
        }
        
        for iface_name in parsed_config.get("interfaces", {}).keys():
            counts["total"] += 1
            
            # Check for sub-interface first (has .N suffix)
            if '.' in iface_name:
                counts["subinterfaces"] += 1
            # Physical interfaces: ge100-, ge400-, hundredGigE, tenGigE (without .N suffix)
            elif re.match(r'^(ge\d+-|ge100-|ge400-|hundredGigE|tenGigE)', iface_name):
                counts["physical"] += 1
            elif iface_name.startswith('bundle'):
                counts["bundles"] += 1
            elif iface_name.startswith('lo'):
                counts["loopbacks"] += 1
            elif iface_name.startswith('irb'):
                counts["irb"] += 1
            elif re.match(r'^ph\d+$', iface_name):
                # PWHE parent interfaces only (ph1, ph2, etc. - no .N suffix)
                counts["pwhe"] += 1
        
        return counts

    def get_service_count(self, config_text: str) -> Dict[str, int]:
        """
        Count network services by type.
        Handles both brace-style and indentation-style config formats.
        
        Args:
            config_text: Raw configuration text
        
        Returns:
            Dict with counts per service type
        """
        counts = {
            "evpn_vpws_fxc": 0,
            "vrf": 0,
            "evpn": 0,
            "vpws": 0,
            "bridge_domain": 0,
            "total": 0
        }
        
        ns_section = self._extract_section(config_text, "network-services")
        if not ns_section:
            return counts
        
        is_brace_style = '{' in ns_section
        
        if is_brace_style:
            # Brace-style: count "service-type name {" patterns
            counts["evpn_vpws_fxc"] = len(re.findall(r'evpn-vpws-fxc\s+\S+\s*\{', ns_section))
            counts["vrf"] = len(re.findall(r'\bvrf\s+\S+\s*\{', ns_section))
            counts["evpn"] = len(re.findall(r'(?<!-)evpn(?!-vpws)\s+\S+\s*\{', ns_section))
            counts["vpws"] = len(re.findall(r'(?<!evpn-)vpws\s+\S+\s*\{', ns_section))
            counts["bridge_domain"] = len(re.findall(r'bridge-domain\s+\S+\s*\{', ns_section))
        else:
            # Indentation-style: count "instance <name>" lines within each service type
            current_service = None
            
            for line in ns_section.split('\n'):
                stripped = line.strip()
                indent = len(line) - len(line.lstrip())
                
                # Service type at second level (2-4 spaces)
                if indent <= 4 and not stripped.startswith('#'):
                    if stripped == 'evpn-vpws-fxc' or stripped.startswith('evpn-vpws-fxc '):
                        current_service = 'evpn_vpws_fxc'
                    elif re.match(r'^vrf\b', stripped):
                        current_service = 'vrf'
                    elif re.match(r'^evpn(?!-vpws)\b', stripped):
                        current_service = 'evpn'
                    elif re.match(r'^vpws\b', stripped) and 'evpn' not in stripped:
                        current_service = 'vpws'
                    elif stripped.startswith('bridge-domain'):
                        current_service = 'bridge_domain'
                
                # Count instances within each service type
                if current_service and stripped.startswith('instance '):
                    counts[current_service] += 1
        
        counts["total"] = sum(v for k, v in counts.items() if k != "total")
        
        return counts

    # ========== Enhanced Summary Methods for Operational State ==========

    def parse_interfaces_brief(self, show_output: str) -> Dict[str, Any]:
        """
        Parse 'show interfaces' output to get UP/DOWN counts per interface type.
        
        Example output format:
            | Interface      | Admin    | Operational     | ...
            | bundle-2       | enabled  | up              | ...
            | bundle-3.100   | disabled | down            | ...
            | ge100-0/0/1    | enabled  | up              | ...
            | irb1           | enabled  | up              | ...
        
        Args:
            show_output: Raw output from 'show interfaces' or 'show interfaces brief'
        
        Returns:
            Dict with counts per interface type including UP status
        """
        result = {
            "total_configured": 0,
            "total_up": 0,
            "by_type": {
                "physical": {"parent": 0, "subif": 0, "parent_up": 0, "subif_up": 0},
                "bundle": {"parent": 0, "subif": 0, "parent_up": 0, "subif_up": 0},
                "loopback": {"parent": 0, "subif": 0, "parent_up": 0, "subif_up": 0},
                "irb": {"parent": 0, "subif": 0, "parent_up": 0, "subif_up": 0},
                "pwhe": {"parent": 0, "subif": 0, "parent_up": 0, "subif_up": 0},
                "gre_tunnel": {"parent": 0, "subif": 0, "parent_up": 0, "subif_up": 0},
            }
        }
        
        if not show_output:
            return result
        
        # Parse each line looking for interface entries
        for line in show_output.split('\n'):
            line = line.strip()
            
            # Skip header lines and separators
            if not line or line.startswith('+') or line.startswith('Legend') or 'Interface' in line and 'Admin' in line:
                continue
            
            # Parse table row: | interface | admin | operational | ...
            if line.startswith('|'):
                parts = [p.strip() for p in line.split('|') if p.strip()]
                if len(parts) >= 3:
                    iface_name = parts[0].split()[0]  # Get just the interface name, strip (L2) etc
                    admin_state = parts[1].lower()
                    oper_state = parts[2].lower()
                    
                    is_up = 'up' in oper_state and 'not' not in oper_state
                    is_subif = '.' in iface_name
                    
                    result["total_configured"] += 1
                    if is_up:
                        result["total_up"] += 1
                    
                    # Categorize by type
                    iface_type = None
                    # Check PWHE first (phX interfaces in DNOS)
                    if re.match(r'^ph\d+', iface_name):
                        iface_type = "pwhe"
                    elif iface_name.startswith(('ge100', 'ge400', 'ge10', 'ge25')):
                        iface_type = "physical"
                    elif iface_name.startswith('bundle'):
                        iface_type = "bundle"
                    elif iface_name.startswith('lo'):
                        iface_type = "loopback"
                    elif iface_name.startswith('irb'):
                        iface_type = "irb"
                    elif iface_name.startswith('gre-tunnel'):
                        iface_type = "gre_tunnel"
                    
                    if iface_type and iface_type in result["by_type"]:
                        if is_subif:
                            result["by_type"][iface_type]["subif"] += 1
                            if is_up:
                                result["by_type"][iface_type]["subif_up"] += 1
                        else:
                            result["by_type"][iface_type]["parent"] += 1
                            if is_up:
                                result["by_type"][iface_type]["parent_up"] += 1
        
        return result

    def parse_isis_interfaces(self, show_output: str) -> Dict[str, Any]:
        """
        Parse 'show isis interfaces' output to extract level and interface count per instance.
        
        Example output format:
            Instance ISIS_A:
              Interface    State    Type           Level
              lo1          Up       loopback       L2
              bundle-1     Up       point-to-point L2
        
        Args:
            show_output: Raw output from 'show isis interfaces' command
        
        Returns:
            Dict with instances, each containing level and interface count
        """
        if not show_output:
            return {"instances": [], "total_interfaces": 0}
        
        result = {
            "instances": [],
            "total_interfaces": 0,
            "levels": set()
        }
        
        current_instance = None
        instance_interfaces = 0
        instance_level = None
        
        for line in show_output.split('\n'):
            line = line.strip()
            
            # Match instance line: "Instance ISIS_A:" or "Instance one:"
            instance_match = re.match(r'Instance\s+(\S+):?', line, re.IGNORECASE)
            if instance_match:
                # Save previous instance if exists
                if current_instance:
                    result["instances"].append({
                        "name": current_instance,
                        "level": instance_level,
                        "interface_count": instance_interfaces
                    })
                    result["total_interfaces"] += instance_interfaces
                
                current_instance = instance_match.group(1)
                instance_interfaces = 0
                instance_level = None
                continue
            
            # Match "Instance Level: L2" line
            level_line_match = re.match(r'Instance Level:\s*(L1|L2|L1L2|L1-2)', line, re.IGNORECASE)
            if level_line_match:
                instance_level = level_line_match.group(1).upper().replace('L1-2', 'L1L2')
                result["levels"].add(instance_level)
                continue
            
            # Match interface line with level: "bundle-1     Up       point-to-point L2"
            iface_match = re.match(
                r'(\S+)\s+(Up|Down|One-Way)\s+(\S+)\s+(L1|L2|L1L2|L1-2)',
                line, re.IGNORECASE
            )
            if iface_match:
                instance_interfaces += 1
                level = iface_match.group(4).upper().replace('L1-2', 'L1L2')
                if not instance_level:
                    instance_level = level
                result["levels"].add(level)
        
        # Don't forget the last instance
        if current_instance:
            result["instances"].append({
                "name": current_instance,
                "level": instance_level,
                "interface_count": instance_interfaces
            })
            result["total_interfaces"] += instance_interfaces
        
        # Convert levels set to sorted list
        result["levels"] = sorted(list(result["levels"]))
        
        return result

    def parse_ospf_interfaces(self, show_output: str, detail_output: str = None) -> Dict[str, Any]:
        """
        Parse 'show ospf interfaces' and 'show ospf interfaces detail' output.
        
        Example output format:
            OSPF instance instance1
            Interface                                         State     Type                Area      
            bundle-2.1011                                     Up        POINT-TO-POINT      0.0.0.0   
            bundle-2.1012                                     Up        BROADCAST           0.0.0.2   
        
        Detail output shows DR/BDR:
            Designated Router (ID) 10.170.1.66, Interface Address 10.170.1.66
            Backup Designated Router (ID) 100.70.1.45, Interface Address 10.170.1.65
        
        Args:
            show_output: Raw output from 'show ospf interfaces' command
            detail_output: Raw output from 'show ospf interfaces detail' command
        
        Returns:
            Dict with interface types count and DR/BDR status
        """
        result = {
            "instances": [],
            "total_interfaces": 0,
            "p2p_count": 0,
            "broadcast_count": 0,
            "loopback_count": 0,
            "dr_count": 0,
            "bdr_count": 0,
        }
        
        if not show_output:
            return result
        
        current_instance = None
        
        for line in show_output.split('\n'):
            line = line.strip()
            
            # Match instance line: "OSPF instance instance1"
            instance_match = re.match(r'OSPF instance\s+(\S+)', line, re.IGNORECASE)
            if instance_match:
                current_instance = instance_match.group(1)
                if current_instance not in [i["name"] for i in result["instances"]]:
                    result["instances"].append({"name": current_instance})
                continue
            
            # Skip header line
            if 'Interface' in line and 'State' in line and 'Type' in line:
                continue
            
            # Match interface line: "bundle-2.1011  Up  POINT-TO-POINT  0.0.0.0"
            iface_match = re.match(
                r'(\S+)\s+(Up|Down)\s+(POINT-TO-POINT|BROADCAST|LOOPBACK)\s+(\S+)',
                line, re.IGNORECASE
            )
            if iface_match:
                result["total_interfaces"] += 1
                iface_type = iface_match.group(3).upper()
                
                if iface_type == "POINT-TO-POINT":
                    result["p2p_count"] += 1
                elif iface_type == "BROADCAST":
                    result["broadcast_count"] += 1
                elif iface_type == "LOOPBACK":
                    result["loopback_count"] += 1
        
        # Parse detail output for DR/BDR status
        if detail_output:
            # Count interfaces where this router is DR
            dr_matches = re.findall(
                r'Designated Router \(ID\)\s+(\d+\.\d+\.\d+\.\d+)',
                detail_output
            )
            # Count interfaces where this router is BDR
            bdr_matches = re.findall(
                r'Backup Designated Router \(ID\)\s+(\d+\.\d+\.\d+\.\d+)',
                detail_output
            )
            
            # Extract router-id to check if we're DR or BDR
            router_id_match = re.search(r'Router ID\s+(\d+\.\d+\.\d+\.\d+)', detail_output)
            router_id = router_id_match.group(1) if router_id_match else None
            
            if router_id:
                result["dr_count"] = sum(1 for dr in dr_matches if dr == router_id)
                result["bdr_count"] = sum(1 for bdr in bdr_matches if bdr == router_id)
        
        return result

    def parse_bgp_summary(self, show_output: str) -> Dict[str, Any]:
        """
        Parse 'show bgp summary' output to extract local AS number.
        
        Example output format:
            BGP router identifier 9.9.9.2, local AS number 2
            BGP router identifier 9.9.9.9, local AS number 65000, confederation identifier 1
        
        Args:
            show_output: Raw output from 'show bgp summary' command
        
        Returns:
            Dict with BGP information
        """
        result = {
            "local_as": None,
            "router_id": None,
            "confederation_id": None,
            "neighbor_count": 0,
            "established_count": 0,
        }
        
        if not show_output:
            return result
        
        # Extract local AS number
        as_match = re.search(r'local AS number\s+(\d+)', show_output)
        if as_match:
            result["local_as"] = int(as_match.group(1))
        
        # Extract router identifier
        rid_match = re.search(r'BGP router identifier\s+(\d+\.\d+\.\d+\.\d+)', show_output)
        if rid_match:
            result["router_id"] = rid_match.group(1)
        
        # Extract confederation identifier if present
        conf_match = re.search(r'confederation identifier\s+(\d+)', show_output)
        if conf_match:
            result["confederation_id"] = int(conf_match.group(1))
        
        # Count neighbors (lines with IP addresses and AS numbers)
        neighbor_pattern = re.compile(r'^\s*[D\s]*(\d+\.\d+\.\d+\.\d+|[\da-fA-F:]+)\s+4\s+(\d+)')
        for line in show_output.split('\n'):
            if neighbor_pattern.match(line.strip()):
                result["neighbor_count"] += 1
        
        # Extract established count from "Total number of established neighbors"
        established_match = re.search(r'Total number of established neighbors[^:]*:\s*(\d+)', show_output)
        if established_match:
            result["established_count"] = int(established_match.group(1))
        else:
            # Alternative: count neighbors in Full/Established state
            result["established_count"] = len(re.findall(r'\d+\.\d+\.\d+\.\d+.*\d{2}:\d{2}:\d{2}', show_output))
        
        return result

    def get_vlan_summary(self, parsed_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract VLAN summary from sub-interfaces in parsed configuration.
        
        Args:
            parsed_config: Parsed configuration dict
        
        Returns:
            Dict with VLAN range and count
        """
        vlans = set()
        
        for iface_name in parsed_config.get("interfaces", {}).keys():
            # Extract VLAN from sub-interface name (e.g., bundle-1.100 -> 100)
            if '.' in iface_name:
                try:
                    vlan_id = int(iface_name.split('.')[-1])
                    if 1 <= vlan_id <= 4094:  # Valid VLAN range
                        vlans.add(vlan_id)
                except ValueError:
                    pass
        
        if not vlans:
            return {"count": 0, "range": None, "vlans": []}
        
        sorted_vlans = sorted(vlans)
        
        # Create a compact range representation
        ranges = []
        start = sorted_vlans[0]
        end = start
        
        for vlan in sorted_vlans[1:]:
            if vlan == end + 1:
                end = vlan
            else:
                if start == end:
                    ranges.append(str(start))
                else:
                    ranges.append(f"{start}-{end}")
                start = vlan
                end = vlan
        
        # Don't forget the last range
        if start == end:
            ranges.append(str(start))
        else:
            ranges.append(f"{start}-{end}")
        
        return {
            "count": len(vlans),
            "range": ", ".join(ranges),
            "min": min(vlans),
            "max": max(vlans),
        }

    def get_vlan_tags_summary(self, parsed_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract VLAN-tags (outer/inner) from interface configurations.
        
        Supports multiple formats:
            1. vlan-id 12 (single VLAN)
            2. vlan-tags outer-tag 1 inner-tag 100 outer-tpid 0x8100 (QinQ inline)
            3. vlan-tags
                 outer 1
                 inner 100
        
        Args:
            parsed_config: Parsed configuration dict
        
        Returns:
            Dict with outer/inner VLAN ranges and counts
        """
        outer_vlans = {}  # vlan_id -> count of sub-interfaces using it
        inner_vlans = set()
        single_vlans = set()  # For simple vlan-id configs
        
        for iface_name, iface_data in parsed_config.get("interfaces", {}).items():
            if '.' not in iface_name:  # Skip parent interfaces
                continue
            
            config = iface_data.get("config", "")
            
            # Format 1: Simple vlan-id
            vlan_id_match = re.search(r'vlan-id\s+(\d+)', config)
            if vlan_id_match:
                single_vlans.add(int(vlan_id_match.group(1)))
            
            # Format 2: QinQ inline format - vlan-tags outer-tag 1 inner-tag 100
            qinq_match = re.search(r'vlan-tags\s+outer-tag\s+(\d+)\s+inner-tag\s+(\d+)', config)
            if qinq_match:
                outer_vlan = int(qinq_match.group(1))
                inner_vlan = int(qinq_match.group(2))
                outer_vlans[outer_vlan] = outer_vlans.get(outer_vlan, 0) + 1
                inner_vlans.add(inner_vlan)
                continue  # Skip other checks if QinQ matched
            
            # Format 3: Multi-line vlan-tags (older format)
            outer_match = re.search(r'outer\s+(\d+)', config)
            if outer_match:
                outer_vlan = int(outer_match.group(1))
                outer_vlans[outer_vlan] = outer_vlans.get(outer_vlan, 0) + 1
            
            inner_match = re.search(r'inner\s+(\d+)', config)
            if inner_match:
                inner_vlans.add(int(inner_match.group(1)))
        
        result = {
            "outer": {"vlans": {}, "range": None, "count": 0, "subif_count": 0},
            "inner": {"vlans": set(), "range": None, "count": 0},
            "single": {"vlans": set(), "range": None, "count": 0},
        }
        
        # Process outer VLANs (QinQ)
        if outer_vlans:
            result["outer"]["vlans"] = outer_vlans
            result["outer"]["count"] = len(outer_vlans)
            result["outer"]["subif_count"] = sum(outer_vlans.values())
            
            # Create range string for outer VLANs
            sorted_outer = sorted(outer_vlans.keys())
            result["outer"]["range"] = self._create_range_string(sorted_outer)
        
        # Process inner VLANs (QinQ)
        if inner_vlans:
            result["inner"]["vlans"] = inner_vlans
            result["inner"]["count"] = len(inner_vlans)
            
            # Create range string for inner VLANs
            sorted_inner = sorted(inner_vlans)
            result["inner"]["range"] = self._create_range_string(sorted_inner)
        
        # Process single VLANs (non-QinQ)
        if single_vlans:
            result["single"]["vlans"] = single_vlans
            result["single"]["count"] = len(single_vlans)
            
            sorted_single = sorted(single_vlans)
            result["single"]["range"] = self._create_range_string(sorted_single)
        
        return result

    def _create_range_string(self, sorted_vlans: List[int]) -> str:
        """Create a compact range string from sorted VLAN list."""
        if not sorted_vlans:
            return ""
        
        ranges = []
        start = sorted_vlans[0]
        end = start
        
        for vlan in sorted_vlans[1:]:
            if vlan == end + 1:
                end = vlan
            else:
                if start == end:
                    ranges.append(str(start))
                else:
                    ranges.append(f"{start}-{end}")
                start = vlan
                end = vlan
        
        # Last range
        if start == end:
            ranges.append(str(start))
        else:
            ranges.append(f"{start}-{end}")
        
        return ", ".join(ranges)

    def get_interface_type_summary(
        self, 
        parsed_config: Dict[str, Any],
        operational_data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Categorize interfaces by type with parent/sub counts and UP status.
        
        Args:
            parsed_config: Parsed configuration dict
            operational_data: Dict from operational.json with UP counts from bash script
        
        Returns:
            Dict with detailed counts per interface type
        """
        # Initialize structure with parent/sub breakdown per type
        counts = {
            "total": 0,
            "total_up": 0,
            "physical": {"parent": 0, "subif": 0, "parent_up": 0, "subif_up": 0},
            "bundle": {"parent": 0, "subif": 0, "parent_up": 0, "subif_up": 0},
            "loopback": {"parent": 0, "subif": 0, "parent_up": 0, "subif_up": 0},
            "irb": {"parent": 0, "subif": 0, "parent_up": 0, "subif_up": 0},
            "pwhe": {"parent": 0, "subif": 0, "parent_up": 0, "subif_up": 0},
            "gre_tunnel": {"parent": 0, "subif": 0, "parent_up": 0, "subif_up": 0},
        }
        
        for iface_name in parsed_config.get("interfaces", {}).keys():
            counts["total"] += 1
            is_subif = '.' in iface_name
            
            # Check for PWHE interfaces first (ph0, ph1, ph13, ph13.1, etc.)
            # PWHE = Pseudowire Headend, named phX or phX.Y in DNOS
            if re.match(r'^ph\d+', iface_name):
                if is_subif:
                    counts["pwhe"]["subif"] += 1
                else:
                    counts["pwhe"]["parent"] += 1
            elif iface_name.startswith(('ge100', 'ge400', 'ge10', 'ge25')):
                if is_subif:
                    counts["physical"]["subif"] += 1
                else:
                    counts["physical"]["parent"] += 1
            elif iface_name.startswith('bundle'):
                if is_subif:
                    counts["bundle"]["subif"] += 1
                else:
                    counts["bundle"]["parent"] += 1
            elif iface_name.startswith('lo'):
                counts["loopback"]["parent"] += 1
            elif iface_name.startswith('irb'):
                counts["irb"]["parent"] += 1
            elif iface_name.startswith('gre-tunnel'):
                counts["gre_tunnel"]["parent"] += 1
        
        # Get UP counts from bash-parsed operational.json
        if operational_data:
            # Use bash-parsed counts (interfaces_up, physical_up, etc.)
            counts["total_up"] = operational_data.get("interfaces_up", 0)
            
            # Map bash field names to our structure
            counts["physical"]["parent_up"] = operational_data.get("physical_up", 0)
            counts["bundle"]["parent_up"] = operational_data.get("bundle_up", 0)
            counts["loopback"]["parent_up"] = operational_data.get("loopback_up", 0)
            counts["irb"]["parent_up"] = operational_data.get("irb_up", 0)
            counts["pwhe"]["parent_up"] = operational_data.get("pwhe_up", 0)
        
        return counts

    def get_wan_interfaces(self, parsed_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get WAN interfaces - interfaces with 'mpls enabled' in their config.
        
        WAN interfaces are those participating in MPLS backbone connectivity,
        typically used for IGP/LDP peering.
        
        Args:
            parsed_config: Parsed configuration dict
        
        Returns:
            Dict with wan interface names and count
        """
        wan_interfaces = []
        
        for iface_name, iface_data in parsed_config.get("interfaces", {}).items():
            config = iface_data.get("config", "")
            # Check for 'mpls enabled' in the interface config
            if re.search(r'mpls\s+enabled', config):
                wan_interfaces.append(iface_name)
        
        return {
            "interfaces": wan_interfaces,
            "count": len(wan_interfaces)
        }

    def get_service_transport(self, config_text: str) -> Dict[str, Dict[str, Any]]:
        """
        Detect transport protocol (MPLS/VXLAN/SRv6) per service type.
        Uses get_service_count for counts and scans for transport keywords.
        
        Args:
            config_text: Raw configuration text
        
        Returns:
            Dict with service counts grouped by transport protocol
        """
        # Get counts using the format-aware method
        counts = self.get_service_count(config_text)
        
        result = {
            "evpn_vpws_fxc": {"count": counts["evpn_vpws_fxc"], "transport": "MPLS"},
            "vrf": {"count": counts["vrf"], "transport": "MPLS"},
            "evpn": {"count": counts["evpn"], "transport": "MPLS"},
            "vpws": {"count": counts["vpws"], "transport": "MPLS"},
            "bridge_domain": {"count": counts["bridge_domain"], "transport": None},
        }
        
        ns_section = self._extract_section(config_text, "network-services")
        if not ns_section:
            return result
        
        # Track current service context and detect transport
        # Works for both brace-style and indentation-style
        current_service = None
        current_indent = 0
        
        for line in ns_section.split('\n'):
            stripped = line.strip()
            if not stripped or stripped == '!':
                continue
            
            indent = len(line) - len(line.lstrip())
            
            # Detect service type (at low indentation)
            if indent <= 4:
                if stripped == 'evpn-vpws-fxc' or stripped.startswith('evpn-vpws-fxc '):
                    current_service = "evpn_vpws_fxc"
                    current_indent = indent
                elif re.match(r'^evpn(?!-vpws)\b', stripped):
                    current_service = "evpn"
                    current_indent = indent
                elif re.match(r'^vpws\b', stripped) and 'evpn' not in stripped:
                    current_service = "vpws"
                    current_indent = indent
                elif re.match(r'^vrf\b', stripped):
                    current_service = "vrf"
                    current_indent = indent
            
            # Detect transport protocol in current context
            if current_service and current_service in result and indent > current_indent:
                if 'transport-protocol' in stripped.lower():
                    if 'srv6' in stripped.lower():
                        result[current_service]["transport"] = "SRv6"
                    elif 'vxlan' in stripped.lower():
                        result[current_service]["transport"] = "VXLAN"
                    elif 'mpls' in stripped.lower():
                        result[current_service]["transport"] = "MPLS"
                # Also check for vni (VXLAN) or locator (SRv6)
                elif current_service == "evpn" and re.match(r'vni\s+\d+', stripped):
                    result[current_service]["transport"] = "VXLAN"
                elif 'locator' in stripped.lower():
                    result[current_service]["transport"] = "SRv6"
        
        return result

    def generate_enhanced_summary(
        self,
        parsed_config: Dict[str, Any],
        raw_config: str,
        operational_data: Dict[str, Any] = None
    ) -> str:
        """
        Generate a compact enhanced summary of the device configuration.
        
        Output format:
            IGP: ISIS L2 (45 ifaces) + OSPF (3 P2P, 1 DR) | BGP: AS 65000, 10/12 established
            Interfaces: 2350 cfg/2345 UP | Physical: 8 | Bundle: 5+2300 sub | Lo: 2 | IRB: 10 | PWHE: 25 (20 UP)
            VLANs: 100-2400 (2300 used) | Services: FXC: 2300 (MPLS), VRF: 150 | 62K lines
        
        Args:
            parsed_config: Parsed configuration dict
            raw_config: Raw configuration text
            operational_data: Dict with output from show commands
        
        Returns:
            Compact multi-line summary string
        """
        parts = []
        
        # === Line 1: IGP + BGP ===
        line1_parts = []
        
        # IGP Summary
        igp_parts = []
        
        # IGP from bash-parsed operational data or config
        if operational_data and operational_data.get("igp"):
            igp_type = operational_data.get("igp", "")
            if igp_type == "IS-IS":
                igp_parts.append("ISIS")
            elif igp_type == "OSPF":
                igp_parts.append("OSPF")
            elif igp_type not in ["None", ""]:
                igp_parts.append(igp_type)
        
        # Fallback to config-based detection
        if not igp_parts:
            if parsed_config.get("protocols", {}).get("isis"):
                igp_parts.append("ISIS")
            if parsed_config.get("protocols", {}).get("ospf"):
                igp_parts.append("OSPF")
        
        if igp_parts:
            line1_parts.append(f"IGP: {' + '.join(igp_parts)}")
        
        # BGP from bash-parsed operational data or config
        bgp_as = None
        bgp_neighbors = 0
        
        # Try bash-parsed operational data first
        if operational_data:
            bgp_as = operational_data.get("local_as")
            bgp_neighbors = operational_data.get("bgp_neighbors", 0)
        
        # Fallback to config-based BGP info
        if not bgp_as and parsed_config.get("protocols", {}).get("bgp"):
            bgp_config = parsed_config["protocols"]["bgp"]
            bgp_as = bgp_config.get("local_as")
        
        # Build BGP line
        if bgp_as:
            if bgp_neighbors and bgp_neighbors > 0:
                line1_parts.append(f"BGP: AS {bgp_as}, {bgp_neighbors} peers")
            else:
                line1_parts.append(f"BGP: AS {bgp_as}")
        
        if line1_parts:
            parts.append(" | ".join(line1_parts))
        
        # === Line 2: Interfaces with parent/sub and UP counts ===
        iface_summary = self.get_interface_type_summary(parsed_config, operational_data)
        iface_parts = []
        
        # Total with UP count: "X cfg / Y UP"
        total_cfg = iface_summary["total"]
        total_up = iface_summary.get("total_up", 0)
        if total_up > 0:
            iface_parts.append(f"{total_cfg} cfg / {total_up} UP")
        else:
            iface_parts.append(f"{total_cfg} cfg")
        
        # Physical (parent + sub with UP count)
        phys = iface_summary.get("physical", {})
        phys_parent = phys.get("parent", 0)
        phys_subif = phys.get("subif", 0)
        phys_up = phys.get("parent_up", 0) + phys.get("subif_up", 0)
        if phys_parent > 0 or phys_subif > 0:
            if phys_subif > 0:
                if phys_up > 0:
                    iface_parts.append(f"Physical: {phys_parent}+{phys_subif} sub ({phys_up} UP)")
                else:
                    iface_parts.append(f"Physical: {phys_parent}+{phys_subif} sub")
            else:
                if phys_up > 0:
                    iface_parts.append(f"Physical: {phys_parent} ({phys_up} UP)")
                else:
                    iface_parts.append(f"Physical: {phys_parent}")
        
        # Bundle (parent + sub with UP)
        bundle = iface_summary.get("bundle", {})
        bundle_parent = bundle.get("parent", 0)
        bundle_subif = bundle.get("subif", 0)
        bundle_up = bundle.get("parent_up", 0) + bundle.get("subif_up", 0)
        if bundle_parent > 0 or bundle_subif > 0:
            if bundle_subif > 0:
                if bundle_up > 0:
                    iface_parts.append(f"Bundle: {bundle_parent}+{bundle_subif} sub ({bundle_up} UP)")
                else:
                    iface_parts.append(f"Bundle: {bundle_parent}+{bundle_subif} sub")
            else:
                if bundle_up > 0:
                    iface_parts.append(f"Bundle: {bundle_parent} ({bundle_up} UP)")
                else:
                    iface_parts.append(f"Bundle: {bundle_parent}")
        
        # Loopback with UP count
        lo = iface_summary.get("loopback", {})
        lo_count = lo.get("parent", 0)
        lo_up = lo.get("parent_up", 0)
        if lo_count > 0:
            if lo_up > 0:
                iface_parts.append(f"Lo: {lo_count} ({lo_up} UP)")
            else:
                iface_parts.append(f"Lo: {lo_count}")
        
        # IRB with UP count
        irb = iface_summary.get("irb", {})
        irb_count = irb.get("parent", 0)
        irb_up = irb.get("parent_up", 0)
        if irb_count > 0:
            if irb_up > 0:
                iface_parts.append(f"IRB: {irb_count} ({irb_up} UP)")
            else:
                iface_parts.append(f"IRB: {irb_count}")
        
        # PWHE with UP count
        pwhe = iface_summary.get("pwhe", {})
        pwhe_parent = pwhe.get("parent", 0)
        pwhe_up = pwhe.get("parent_up", 0)
        if pwhe_parent > 0:
            if pwhe_up > 0:
                iface_parts.append(f"PWHE: {pwhe_parent} ({pwhe_up} UP)")
            else:
                iface_parts.append(f"PWHE: {pwhe_parent}")
        
        if iface_parts:
            parts.append("Interfaces: " + " | ".join(iface_parts))
        
        # === Line 3: VLAN-Tags (outer/inner) or simple vlan-ids ===
        vlan_tags = self.get_vlan_tags_summary(parsed_config)
        vlan_parts = []
        
        # QinQ outer/inner tags
        if vlan_tags["outer"]["count"] > 0:
            outer_range = vlan_tags["outer"]["range"]
            outer_subs = vlan_tags["outer"]["subif_count"]
            vlan_parts.append(f"outer {outer_range} ({outer_subs} subs)")
        
        if vlan_tags["inner"]["count"] > 0:
            inner_range = vlan_tags["inner"]["range"]
            inner_count = vlan_tags["inner"]["count"]
            vlan_parts.append(f"inner {inner_range} ({inner_count} used)")
        
        # Single VLAN IDs (non-QinQ)
        if vlan_tags["single"]["count"] > 0:
            single_range = vlan_tags["single"]["range"]
            single_count = vlan_tags["single"]["count"]
            vlan_parts.append(f"{single_range} ({single_count} used)")
        
        if vlan_parts:
            parts.append("VLANs: " + ", ".join(vlan_parts))
        
        # === Line 4: Services with UP counts + Config size ===
        line4_parts = []
        
        # Service Summary with transport protocol and UP counts
        svc_transport = self.get_service_transport(raw_config)
        svc_parts = []
        
        # Map service types to display names and operational data keys
        svc_map = {
            "evpn_vpws_fxc": ("FXC", "fxc"),
            "vrf": ("VRF", "vrf"),
            "evpn": ("EVPN", "evpn"),
            "vpws": ("VPWS", "vpws"),
            "bridge_domain": ("BD", None),
        }
        
        for svc_type, svc_info in svc_transport.items():
            if svc_info["count"] > 0:
                svc_name, op_key = svc_map.get(svc_type, (svc_type, None))
                total = svc_info["count"]
                transport = svc_info.get("transport")
                
                # Get UP count from operational data
                up_count = 0
                if operational_data and op_key:
                    up_count = operational_data.get(f"{op_key}_up", 0)
                
                # Build service string: "FXC: 2300/2300 UP (MPLS)"
                if up_count > 0:
                    if transport:
                        svc_parts.append(f"{svc_name}: {total}/{up_count} UP ({transport})")
                    else:
                        svc_parts.append(f"{svc_name}: {total}/{up_count} UP")
                else:
                    if transport:
                        svc_parts.append(f"{svc_name}: {total} ({transport})")
                    else:
                        svc_parts.append(f"{svc_name}: {total}")
        
        if svc_parts:
            line4_parts.append("Services: " + ", ".join(svc_parts))
        
        # Config size
        config_lines = len(raw_config.split('\n'))
        if config_lines >= 1000:
            line4_parts.append(f"{config_lines // 1000}K lines")
        else:
            line4_parts.append(f"{config_lines} lines")
        
        if line4_parts:
            parts.append(" | ".join(line4_parts))
        
        return "\n".join(parts)

    def _parse_multihoming_summary(self, raw_config: str) -> Dict[str, Any]:
        """
        Parse multihoming configuration summary from raw config.
        
        Args:
            raw_config: Raw configuration text
            
        Returns:
            Dict with multihoming info: configured, interface_count, esi_prefix, redundancy_mode, in_services
        """
        import re
        
        result = {
            "configured": False,
            "interface_count": 0,
            "esi_prefix": "",
            "redundancy_mode": "single-active",
            "in_services": 0,
            "first_interface": "",
            "last_interface": ""
        }
        
        # Find multihoming section (may be indented under network-services)
        mh_match = re.search(r'^\s*multihoming\s*\n(.*?)(?=^\s*!\s*\n\s*!\s*$|\Z)', raw_config, re.MULTILINE | re.DOTALL)
        if not mh_match:
            return result
        
        mh_section = mh_match.group(0)  # Include the multihoming line itself
        
        # Count interfaces with ESI
        esi_pattern = r'interface\s+(\S+)\s*\n\s*esi\s+arbitrary\s+value\s+([0-9a-fA-F:]+)'
        esi_matches = list(re.finditer(esi_pattern, mh_section))
        
        if not esi_matches:
            return result
        
        result["configured"] = True
        result["interface_count"] = len(esi_matches)
        
        # Get first and last interface names
        result["first_interface"] = esi_matches[0].group(1)
        result["last_interface"] = esi_matches[-1].group(1)
        
        # Get ESI prefix from first match (first 3 octets)
        if esi_matches:
            first_esi = esi_matches[0].group(2)
            octets = first_esi.split(":")
            if len(octets) >= 3:
                result["esi_prefix"] = ":".join(octets[:3])
        
        # Check redundancy mode
        if "redundancy-mode single-active" in mh_section:
            result["redundancy_mode"] = "single-active"
        elif "redundancy-mode all-active" in mh_section:
            result["redundancy_mode"] = "all-active"
        
        # Count interfaces that are also in services (PWHE in FXC)
        mh_interfaces = set(m.group(1) for m in esi_matches)
        
        # Check for service attachments
        svc_iface_pattern = r'instance\s+\S+\s*\n.*?interface\s+(\S+)'
        svc_matches = re.findall(svc_iface_pattern, raw_config, re.DOTALL)
        
        in_services = len(mh_interfaces & set(svc_matches))
        result["in_services"] = in_services
        
        return result

    def _boxed_section(self, title: str, width: int = 78) -> List[str]:
        """
        Generate boxed section header using Unicode box characters.
        
        Args:
            title: Section title
            width: Box width (default 78 for 80-char terminal with # prefix)
        
        Returns:
            List of lines forming the box header
        """
        # Box drawing characters: ╔ ═ ╗ ║ ╚ ╝
        inner_width = width - 2  # Account for side borders
        title_padded = f" {title}".ljust(inner_width)
        
        return [
            "╔" + "═" * inner_width + "╗",
            "║" + title_padded + "║",
            "╚" + "═" * inner_width + "╝"
        ]

    def generate_history_header(
        self,
        hostname: str,
        parsed_config: Dict[str, Any],
        raw_config: str,
        operational_data: Dict[str, Any] = None
    ) -> str:
        """
        Generate a detailed sectioned header for history files.
        
        Sections: STACK, SYSTEM, ROUTING, INTERFACES, NETWORK SERVICES, VLANS
        Uses boxed separators with Unicode box-drawing characters.
        
        Args:
            hostname: Device hostname
            parsed_config: Parsed configuration dict
            raw_config: Raw configuration text
            operational_data: Dict with output from show commands
        
        Returns:
            Multi-line sectioned header string (without # prefix - caller adds it)
        """
        lines = []
        
        # === UPGRADE Section (only shown when upgrade in progress) ===
        upgrade_in_progress = operational_data.get("upgrade_in_progress", False) if operational_data else False
        if upgrade_in_progress:
            lines.extend(self._boxed_section("⚠ UPGRADE IN PROGRESS"))
            upgrade_status = operational_data.get("upgrade_status", "")
            upgrade_progress = operational_data.get("upgrade_progress", "")
            nodes_upgrading = operational_data.get("nodes_upgrading", "")
            
            if upgrade_status:
                lines.append(f"  • Status: {upgrade_status}")
            if upgrade_progress:
                lines.append(f"  • Progress: {upgrade_progress}")
            if nodes_upgrading:
                lines.append(f"  • Nodes: {nodes_upgrading}")
        
        # === STACK Section ===
        # Get installation finish time for header
        install_finish = operational_data.get("install_finish", "N/A") if operational_data else "N/A"
        install_status = operational_data.get("install_status", "") if operational_data else ""
        
        # Get device state and connection method
        device_state = operational_data.get("device_state", "DNOS") if operational_data else "DNOS"
        connection_method = operational_data.get("connection_method", "") if operational_data else ""
        
        # Build STACK header with state info
        stack_header = "STACK"
        if device_state and device_state != "DNOS":
            stack_header = f"STACK [STATE: {device_state}]"
        elif install_finish and install_finish != "N/A":
            stack_header = f"STACK (last installed: {install_finish})"
        
        lines.extend(self._boxed_section(stack_header))
        
        # Show connection method if available
        if connection_method and connection_method not in ('N/A', ''):
            lines.append(f"  • Connection: {connection_method}")
        
        # Get current versions and URLs
        dnos_ver = operational_data.get("dnos_version", "N/A") if operational_data else "N/A"
        baseos_ver = operational_data.get("baseos_version", "N/A") if operational_data else "N/A"
        gi_ver = operational_data.get("gi_version", "N/A") if operational_data else "N/A"
        dnos_url = operational_data.get("dnos_url", "") if operational_data else ""
        baseos_url = operational_data.get("baseos_url", "") if operational_data else ""
        gi_url = operational_data.get("gi_url", "") if operational_data else ""
        
        # Get target versions (for GI mode devices with staged images)
        target_dnos = operational_data.get("target_dnos_version", "") if operational_data else ""
        target_gi = operational_data.get("target_gi_version", "") if operational_data else ""
        target_baseos = operational_data.get("target_baseos_version", "") if operational_data else ""
        
        # DNOS with source
        if dnos_url and dnos_url != "N/A":
            lines.append(f"  • DNOS: {dnos_ver}")
            lines.append(f"      Source: {dnos_url}")
        else:
            lines.append(f"  • DNOS: {dnos_ver}")
        
        # BaseOS with source
        if baseos_url and baseos_url != "N/A":
            lines.append(f"  • BaseOS: {baseos_ver}")
            lines.append(f"      Source: {baseos_url}")
        else:
            lines.append(f"  • BaseOS: {baseos_ver}")
        
        # GI with source
        if gi_url and gi_url != "N/A":
            lines.append(f"  • GI: {gi_ver}")
            lines.append(f"      Source: {gi_url}")
        else:
            lines.append(f"  • GI: {gi_ver}")
        
        # Show target stacks if they exist (for GI mode with staged images)
        has_targets = any([
            target_dnos and target_dnos not in ('N/A', '-', ''),
            target_gi and target_gi not in ('N/A', '-', ''),
            target_baseos and target_baseos not in ('N/A', '-', '')
        ])
        if has_targets:
            lines.append(f"  ─── Target Stacks (Ready to Deploy) ───")
            if target_dnos and target_dnos not in ('N/A', '-', ''):
                lines.append(f"  • Target DNOS: {target_dnos}")
            if target_gi and target_gi not in ('N/A', '-', ''):
                lines.append(f"  • Target GI: {target_gi}")
            if target_baseos and target_baseos not in ('N/A', '-', ''):
                lines.append(f"  • Target BaseOS: {target_baseos}")
        
        # === SYSTEM Section ===
        lines.extend(self._boxed_section("SYSTEM"))
        sys_type = operational_data.get("system_type", "N/A") if operational_data else "N/A"
        sys_uptime = operational_data.get("system_uptime", "N/A") if operational_data else "N/A"
        serial_number = operational_data.get("serial_number", "N/A") if operational_data else "N/A"
        mgmt_ip = operational_data.get("mgmt_ip", "N/A") if operational_data else "N/A"
        lines.append(f"  • Type: {sys_type}")
        lines.append(f"  • Serial: {serial_number}")
        lines.append(f"  • Mgmt IP: {mgmt_ip}")
        lines.append(f"  • Uptime: {sys_uptime}")
        
        # Node counts - show physical NCC count based on architecture
        if operational_data:
            # Determine physical NCC count based on system type
            # SA (Standalone) = 1 NCC, CL (Cluster) = 2 NCCs
            ncc_up = operational_data.get("ncc_up", 0)
            
            if sys_type.startswith("CL"):
                # Cluster: 2 physical NCCs
                physical_ncc = 2
                lines.append(f"  • NCC: {ncc_up}/{physical_ncc} UP (Cluster)")
            elif sys_type.startswith("SA"):
                # Standalone: 1 physical NCC
                physical_ncc = 1
                lines.append(f"  • NCC: {ncc_up}/{physical_ncc} UP (Standalone)")
            else:
                # Unknown - show slot count
                ncc_total = operational_data.get("ncc_total", 0)
                if ncc_total > 0:
                    lines.append(f"  • NCC: {ncc_up}/{ncc_total} UP")
            
            ncp_total = operational_data.get("ncp_total", 0)
            ncp_up = operational_data.get("ncp_up", 0)
            if ncp_total > 0:
                lines.append(f"  • NCP: {ncp_up}/{ncp_total} UP")
            
            ncf_total = operational_data.get("ncf_total", 0)
            ncf_up = operational_data.get("ncf_up", 0)
            if ncf_total > 0:
                lines.append(f"  • NCF: {ncf_up}/{ncf_total} UP")
            
            ncm_total = operational_data.get("ncm_total", 0)
            ncm_up = operational_data.get("ncm_up", 0)
            if ncm_total > 0:
                lines.append(f"  • NCM: {ncm_up}/{ncm_total} UP")
        
        # === ROUTING Section ===
        lines.extend(self._boxed_section("ROUTING"))
        
        # IGP
        igp_parts = []
        if operational_data and operational_data.get("igp"):
            igp_type = operational_data.get("igp", "")
            if igp_type == "IS-IS":
                igp_parts.append("ISIS")
            elif igp_type == "OSPF":
                igp_parts.append("OSPF")
            elif igp_type not in ["None", ""]:
                igp_parts.append(igp_type)
        
        if not igp_parts:
            if parsed_config.get("protocols", {}).get("isis"):
                igp_parts.append("ISIS")
            if parsed_config.get("protocols", {}).get("ospf"):
                igp_parts.append("OSPF")
        
        igp_str = " + ".join(igp_parts) if igp_parts else "None"
        lines.append(f"  • IGP: {igp_str}")
        
        # BGP - only show if protocols bgp is configured
        bgp_as = None
        bgp_neighbors = 0
        bgp_configured = parsed_config.get("protocols", {}).get("bgp") is not None
        
        if bgp_configured:
            if operational_data:
                bgp_as = operational_data.get("local_as")
                bgp_neighbors = operational_data.get("bgp_neighbors", 0)
            
            if not bgp_as:
                bgp_as = parsed_config["protocols"]["bgp"].get("local_as")
            
            if bgp_as:
                bgp_up = operational_data.get("bgp_up", 0) if operational_data else 0
                if bgp_neighbors > 0:
                    lines.append(f"  • BGP: AS {bgp_as}, {bgp_up}/{bgp_neighbors} peers UP")
                else:
                    lines.append(f"  • BGP: AS {bgp_as}")
        
        # Label Protocol
        label_proto = operational_data.get("label_protocol", "None") if operational_data else "None"
        lines.append(f"  • Label Protocol: {label_proto}")
        
        # === PROTOCOLS Section (LLDP, LACP, BFD, etc.) ===
        protocols_list = []
        
        # Check from operational_data first
        if operational_data:
            if operational_data.get("lldp_interfaces"):
                lldp_count = operational_data["lldp_interfaces"]
                protocols_list.append(f"LLDP ({lldp_count} interfaces)")
            if operational_data.get("lacp_interfaces"):
                lacp_count = operational_data["lacp_interfaces"]
                protocols_list.append(f"LACP ({lacp_count} bundles)")
            if operational_data.get("bfd_interfaces"):
                bfd_count = operational_data["bfd_interfaces"]
                protocols_list.append(f"BFD ({bfd_count} interfaces)")
        
        # Fallback: detect from raw_config if operational_data doesn't have them
        if not protocols_list and raw_config:
            # LLDP
            if re.search(r'^\s{2}lldp\s*$', raw_config, re.MULTILINE):
                lldp_section = raw_config[raw_config.find('  lldp'):] if '  lldp' in raw_config else ''
                lldp_end = lldp_section.find('\n  !') if '\n  !' in lldp_section else 2000
                lldp_block = lldp_section[:lldp_end]
                lldp_ifs = len(re.findall(r'interface\s+\S+', lldp_block))
                protocols_list.append(f"LLDP ({lldp_ifs} interfaces)" if lldp_ifs else "LLDP")
            
            # LACP
            if re.search(r'^\s{2}lacp\s*$', raw_config, re.MULTILINE):
                lacp_section = raw_config[raw_config.find('  lacp'):] if '  lacp' in raw_config else ''
                lacp_end = lacp_section.find('\n  !') if '\n  !' in lacp_section else 2000
                lacp_block = lacp_section[:lacp_end]
                lacp_ifs = len(re.findall(r'interface\s+bundle-\d+', lacp_block))
                protocols_list.append(f"LACP ({lacp_ifs} bundles)" if lacp_ifs else "LACP")
            
            # BFD
            if re.search(r'^\s{2}bfd\s*$', raw_config, re.MULTILINE):
                bfd_section = raw_config[raw_config.find('  bfd'):] if '  bfd' in raw_config else ''
                bfd_end = bfd_section.find('\n  !') if '\n  !' in bfd_section else 2000
                bfd_block = bfd_section[:bfd_end]
                bfd_ifs = len(re.findall(r'interface\s+\S+', bfd_block))
                protocols_list.append(f"BFD ({bfd_ifs} interfaces)" if bfd_ifs else "BFD")
        
        # Only show PROTOCOLS section if there are protocols configured
        if protocols_list:
            lines.extend(self._boxed_section("PROTOCOLS"))
            for proto in protocols_list:
                lines.append(f"  • {proto}")
        
        # === INTERFACES Section ===
        lines.extend(self._boxed_section("INTERFACES"))
        
        iface_summary = self.get_interface_type_summary(parsed_config, operational_data)
        total_cfg = iface_summary.get("total", 0)
        total_up = iface_summary.get("total_up", 0)
        lines.append(f"  • Total: {total_cfg} configured / {total_up} UP")
        
        # Physical
        phys = iface_summary.get("physical", {})
        phys_parent = phys.get("parent", 0)
        phys_subif = phys.get("subif", 0)
        phys_up = phys.get("parent_up", 0) + phys.get("subif_up", 0)
        if phys_parent > 0 or phys_subif > 0:
            lines.append(f"  • Physical: {phys_parent} + {phys_subif} sub-interfaces ({phys_up} UP)")
        
        # Bundle
        bundle = iface_summary.get("bundle", {})
        bundle_parent = bundle.get("parent", 0)
        bundle_subif = bundle.get("subif", 0)
        bundle_up = bundle.get("parent_up", 0) + bundle.get("subif_up", 0)
        if bundle_parent > 0 or bundle_subif > 0:
            lines.append(f"  • Bundle: {bundle_parent} + {bundle_subif} sub-interfaces ({bundle_up} UP)")
        
        # Loopback
        lo = iface_summary.get("loopback", {})
        lo_count = lo.get("parent", 0)
        lo_up = lo.get("parent_up", 0)
        if lo_count > 0:
            lines.append(f"  • Loopback: {lo_count} ({lo_up} UP)")
        
        # IRB
        irb = iface_summary.get("irb", {})
        irb_count = irb.get("parent", 0)
        irb_up = irb.get("parent_up", 0)
        if irb_count > 0:
            lines.append(f"  • IRB: {irb_count} ({irb_up} UP)")
        
        # PWHE (phX = parent, phX.Y = sub-interfaces)
        pwhe = iface_summary.get("pwhe", {})
        pwhe_parent = pwhe.get("parent", 0)
        pwhe_subif = pwhe.get("subif", 0)
        pwhe_parent_up = pwhe.get("parent_up", 0)
        pwhe_subif_up = pwhe.get("subif_up", 0)
        pwhe_total_up = pwhe_parent_up + pwhe_subif_up
        if pwhe_parent > 0 or pwhe_subif > 0:
            lines.append(f"  • PWHE: {pwhe_parent} parent + {pwhe_subif} sub-interfaces ({pwhe_total_up} UP)")
        
        # WAN interfaces (MPLS-enabled)
        wan_info = self.get_wan_interfaces(parsed_config)
        wan_count = wan_info.get("count", 0)
        wan_up = operational_data.get("wan_up", 0) if operational_data else 0
        if wan_count > 0:
            lines.append(f"  • WAN: {wan_count} ({wan_up} UP)")
        
        # === NETWORK SERVICES Section ===
        lines.extend(self._boxed_section("NETWORK SERVICES"))
        
        svc_transport = self.get_service_transport(raw_config)
        
        # Get UP counts from operational data
        fxc_up = operational_data.get("fxc_up", 0) if operational_data else 0
        vrf_up = operational_data.get("vrf_up", 0) if operational_data else 0
        evpn_up = operational_data.get("evpn_up", 0) if operational_data else 0
        vpws_up = operational_data.get("vpws_up", 0) if operational_data else 0
        
        has_services = False
        
        # FXC
        fxc = svc_transport.get("evpn_vpws_fxc", {})
        fxc_count = fxc.get("count", 0)
        fxc_transport = fxc.get("transport", "")
        if fxc_count > 0:
            transport_str = f" ({fxc_transport})" if fxc_transport else ""
            lines.append(f"  • FXC: {fxc_up}/{fxc_count} UP{transport_str}")
            has_services = True
        
        # VRF
        vrf_count = svc_transport.get("vrf", {}).get("count", 0)
        if vrf_count > 0:
            lines.append(f"  • VRF: {vrf_up}/{vrf_count} UP")
            has_services = True
        
        # EVPN
        evpn_count = svc_transport.get("evpn", {}).get("count", 0)
        if evpn_count > 0:
            lines.append(f"  • EVPN: {evpn_up}/{evpn_count} UP")
            has_services = True
        
        # VPWS
        vpws_count = svc_transport.get("vpws", {}).get("count", 0)
        if vpws_count > 0:
            lines.append(f"  • VPWS: {vpws_up}/{vpws_count} UP")
            has_services = True
        
        if not has_services:
            lines.append("  • None configured")
        
        # === MULTIHOMING Section ===
        mh_info = self._parse_multihoming_summary(raw_config)
        if mh_info.get("configured"):
            lines.extend(self._boxed_section("MULTIHOMING"))
            
            mh_count = mh_info.get("interface_count", 0)
            mh_mode = mh_info.get("redundancy_mode", "single-active")
            esi_prefix = mh_info.get("esi_prefix", "")
            first_if = mh_info.get("first_interface", "")
            last_if = mh_info.get("last_interface", "")
            
            # Show interface count with range
            if first_if and last_if and first_if != last_if:
                lines.append(f"  • Interfaces: {mh_count} configured ({first_if} → {last_if})")
            else:
                lines.append(f"  • Interfaces: {mh_count} configured")
            lines.append(f"  • Mode: {mh_mode}")
            if esi_prefix:
                lines.append(f"  • ESI Prefix: {esi_prefix}:...")
            
            # Check for services with multihoming
            mh_in_services = mh_info.get("in_services", 0)
            if mh_in_services > 0:
                lines.append(f"  • In Services: {mh_in_services} ACs with ESI")
        
        # === VLANS Section ===
        lines.extend(self._boxed_section("VLANS"))
        
        vlan_tags = self.get_vlan_tags_summary(parsed_config)
        has_vlans = False
        
        # vlan-tags (QinQ - outer and inner)
        has_vlan_tags = vlan_tags["outer"]["count"] > 0 or vlan_tags["inner"]["count"] > 0
        if has_vlan_tags:
            lines.append("  • vlan-tags:")
            if vlan_tags["outer"]["count"] > 0:
                outer_range = vlan_tags["outer"]["range"]
                outer_subs = vlan_tags["outer"]["subif_count"]
                lines.append(f"      ◦ Outer: {outer_range} ({outer_subs} sub-interfaces)")
            if vlan_tags["inner"]["count"] > 0:
                inner_range = vlan_tags["inner"]["range"]
                inner_count = vlan_tags["inner"]["count"]
                lines.append(f"      ◦ Inner: {inner_range} ({inner_count} unique)")
            has_vlans = True
        
        # vlan-id (single VLAN)
        if vlan_tags["single"]["count"] > 0:
            single_range = vlan_tags["single"]["range"]
            single_count = vlan_tags["single"]["count"]
            lines.append(f"  • vlan-id: {single_range} ({single_count} used)")
            has_vlans = True
        
        if not has_vlans:
            lines.append("  • None configured")
        
        lines.append("")
        
        return "\n".join(lines)


