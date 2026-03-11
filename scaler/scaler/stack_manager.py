"""
Stack Manager for DNOS Version Stack

Manages the extraction, validation, and tracking of DNOS version stacks
from Jenkins builds. A stack consists of DNOS, GI, and BaseOS components.
"""

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, List, Tuple
from enum import Enum

from .jenkins_integration import JenkinsClient, JenkinsBuild, CheetahBranch


class StackComponent(Enum):
    """Stack component types."""
    DNOS = "dnos"
    GI = "gi"
    BASEOS = "baseos"
    FIRMWARE = "firmware"
    ONIE = "onie"


@dataclass
class ComponentInfo:
    """Information about a single stack component."""
    component_type: StackComponent
    url: str
    version: str = ""
    filename: str = ""
    
    def __post_init__(self):
        if self.url and not self.filename:
            # Extract filename from URL
            self.filename = self.url.split('/')[-1]
        
        if self.filename and not self.version:
            # Extract version from filename
            self._parse_version()
    
    def _parse_version(self):
        """Parse version from filename."""
        # Pattern: drivenets_dnos_25.1.0.464_dev.dev_v25_1_1050.tar
        # Pattern: drivenets_baseos_2.25104397329.tar
        # Pattern: drivenets_gi_25.1.0.59_dev.dev_v25_1_143.tar
        
        if 'drivenets_dnos_' in self.filename:
            match = re.search(r'drivenets_dnos_(.+?)\.tar', self.filename)
            if match:
                self.version = match.group(1)
        
        elif 'drivenets_gi_' in self.filename:
            match = re.search(r'drivenets_gi_(.+?)\.tar', self.filename)
            if match:
                self.version = match.group(1)
        
        elif 'drivenets_baseos_' in self.filename:
            match = re.search(r'drivenets_baseos_(.+?)\.tar', self.filename)
            if match:
                self.version = match.group(1)
    
    @property
    def major_version(self) -> str:
        """Extract major version (e.g., 'v25.1' from '25.1.0.464_dev...')."""
        # For DNOS/GI: 25.1.0.464_dev... -> v25.1
        match = re.match(r'(\d+)\.(\d+)', self.version)
        if match:
            return f"v{match.group(1)}.{match.group(2)}"
        
        # For BaseOS: 2.25104397329 -> check if contains version code
        if self.component_type == StackComponent.BASEOS:
            # BaseOS version 2.25xxx means v25.x compatible
            match = re.match(r'2\.(\d{2})', self.version)
            if match:
                major = match.group(1)
                return f"v{major[0]}{major[1]}.x"
        
        return self.version
    
    @property
    def is_valid(self) -> bool:
        """Check if component has valid URL."""
        return bool(self.url and self.url.startswith('http'))


@dataclass
class StackInfo:
    """Complete stack information with all components."""
    branch: str
    build_number: int
    build_time: datetime
    dnos: Optional[ComponentInfo] = None
    gi: Optional[ComponentInfo] = None
    baseos: Optional[ComponentInfo] = None
    firmware: Optional[ComponentInfo] = None
    onie: Optional[ComponentInfo] = None
    
    @property
    def age_hours(self) -> float:
        """Get age of stack in hours."""
        delta = datetime.now() - self.build_time
        return delta.total_seconds() / 3600
    
    @property
    def is_expired(self) -> bool:
        """Check if stack is older than 48 hours."""
        return self.age_hours > 48
    
    @property
    def age_str(self) -> str:
        """Human-readable age string."""
        hours = self.age_hours
        if hours < 1:
            return f"{int(hours * 60)}min ago"
        elif hours < 24:
            return f"{hours:.1f}hrs ago"
        else:
            return f"{hours/24:.1f}days ago"
    
    @property
    def has_core_components(self) -> bool:
        """Check if all core components (DNOS, GI, BaseOS) are present."""
        return all([
            self.dnos and self.dnos.is_valid,
            self.gi and self.gi.is_valid,
            self.baseos and self.baseos.is_valid
        ])
    
    @property
    def missing_components(self) -> List[str]:
        """Get list of missing core components."""
        missing = []
        if not self.dnos or not self.dnos.is_valid:
            missing.append("DNOS")
        if not self.gi or not self.gi.is_valid:
            missing.append("GI")
        if not self.baseos or not self.baseos.is_valid:
            missing.append("BaseOS")
        return missing
    
    def validate_version_compatibility(self) -> Tuple[bool, str]:
        """Check if all components have compatible versions."""
        if not self.has_core_components:
            return False, f"Missing components: {', '.join(self.missing_components)}"
        
        # Get major versions
        dnos_major = self.dnos.major_version if self.dnos else None
        gi_major = self.gi.major_version if self.gi else None
        
        # DNOS and GI should match
        if dnos_major and gi_major:
            # Extract numeric parts for comparison
            dnos_match = re.match(r'v(\d+)\.(\d+)', dnos_major)
            gi_match = re.match(r'v(\d+)\.(\d+)', gi_major)
            
            if dnos_match and gi_match:
                if dnos_match.groups() != gi_match.groups():
                    return False, f"Version mismatch: DNOS {dnos_major} vs GI {gi_major}"
        
        return True, "Version compatibility OK"
    
    def to_dict(self) -> Dict:
        """Convert to dictionary representation."""
        return {
            'branch': self.branch,
            'build_number': self.build_number,
            'build_time': self.build_time.isoformat(),
            'age_hours': self.age_hours,
            'is_expired': self.is_expired,
            'has_core_components': self.has_core_components,
            'dnos': {
                'url': self.dnos.url if self.dnos else None,
                'version': self.dnos.version if self.dnos else None,
            },
            'gi': {
                'url': self.gi.url if self.gi else None,
                'version': self.gi.version if self.gi else None,
            },
            'baseos': {
                'url': self.baseos.url if self.baseos else None,
                'version': self.baseos.version if self.baseos else None,
            }
        }


class StackManager:
    """Manager for retrieving and validating DNOS version stacks."""
    
    def __init__(self, jenkins_client: JenkinsClient = None):
        self.jenkins = jenkins_client or JenkinsClient()
        self._cache: Dict[str, StackInfo] = {}
    
    def get_stack_from_build(self, branch_name: str, build_number: int = None) -> Optional[StackInfo]:
        """Get stack information from a specific build.
        
        Args:
            branch_name: Branch name (e.g., 'dev_v25_1')
            build_number: Specific build number, or None for last successful
            
        Returns:
            StackInfo with all component URLs, or None if build not found
        """
        # Check cache
        cache_key = f"{branch_name}:{build_number or 'latest'}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Get build info
        build = self.jenkins.get_build_info(branch_name, build_number)
        if not build:
            return None
        
        # Get component URLs
        urls = self.jenkins.get_stack_urls(branch_name, build.build_number)
        
        # Create stack info
        stack = StackInfo(
            branch=branch_name,
            build_number=build.build_number,
            build_time=build.build_time,
            dnos=ComponentInfo(StackComponent.DNOS, urls.get('dnos') or '') if urls.get('dnos') else None,
            gi=ComponentInfo(StackComponent.GI, urls.get('gi') or '') if urls.get('gi') else None,
            baseos=ComponentInfo(StackComponent.BASEOS, urls.get('baseos') or '') if urls.get('baseos') else None
        )
        
        # Cache it
        self._cache[cache_key] = stack
        
        return stack
    
    def get_latest_stack(self, branch_name: str) -> Optional[StackInfo]:
        """Get the latest successful stack for a branch."""
        return self.get_stack_from_build(branch_name, None)
    
    def get_stack_from_url(self, url: str) -> Optional[Dict]:
        """Get stack information from a Jenkins or Minio URL.
        
        Args:
            url: A Jenkins URL (Blue Ocean or classic) or direct Minio URL
            
        Returns:
            Dict with build info and stack URLs, or dict with 'error' key if failed
        """
        from .jenkins_integration import get_stack_from_url as _get_stack_from_url, JenkinsClient
        
        # Check if it's a Minio URL (direct image link)
        if 'minio' in url.lower() or url.endswith('.tar') or url.endswith('.tar.gz'):
            # Extract version from Minio URL
            # Example: http://minio-ssd-il.dev.drivenets.net:9000/dnpkg-48hrs/drivenets_dnos_26.1.0.1_priv.86760_5.tar
            import re
            version_match = re.search(r'drivenets_(\w+)_([\d.]+_\w+\.\d+(?:_\d+)?)', url)
            if version_match:
                component = version_match.group(1)  # dnos, gi, baseos
                version = version_match.group(2)    # 26.1.0.1_priv.86760_5
                
                result = {
                    'branch': 'minio_direct',
                    'build': 0,
                    'dnos_url': url if component.lower() == 'dnos' else None,
                    'gi_url': url if component.lower() == 'gi' else None,
                    'baseos_url': url if component.lower() in ('baseos', 'base') else None,
                    'version': version
                }
                return result
            else:
                return {'error': f'Could not parse Minio URL: {url}'}
        
        # It's a Jenkins URL - use the standard parser
        return _get_stack_from_url(url)
    
    def get_main_branch_for_version(self, branch_name: str) -> Optional[str]:
        """Determine the main dev branch for a given branch.
        
        Examples:
            'dev_v25_1' -> 'dev_v25_1' (already main)
            'rel_v25_1' -> 'dev_v25_1'
            'PR-12345' -> None (can't determine)
            'yarelor_SW-123_v25_1_feature' -> 'dev_v25_1'
        """
        import re
        
        # Already a dev branch
        if branch_name.startswith('dev_v'):
            return branch_name
        
        # Release branch -> dev branch
        if branch_name.startswith('rel_v'):
            return branch_name.replace('rel_', 'dev_')
        
        # Try to extract version from branch name
        match = re.search(r'v(\d+)[_.](\d+)', branch_name)
        if match:
            major, minor = match.groups()
            return f"dev_v{major}_{minor}"
        
        return None
    
    def get_stack_with_fallback(self, branch_name: str, build_number: int = None, 
                                  prefer_private: bool = True) -> Tuple[Optional[StackInfo], str]:
        """Get stack from branch, optionally falling back to main branch for missing GI/BaseOS.
        
        Args:
            branch_name: Branch to get DNOS from
            build_number: Specific build, or None for latest
            prefer_private: If True, prefer components from private branch first,
                           only fallback to main if missing. If False, always use main for GI/BaseOS.
            
        Returns:
            Tuple of (StackInfo, message describing what was done)
        """
        # Get stack from requested branch
        stack = self.get_stack_from_build(branch_name, build_number)
        if not stack:
            return None, f"No builds found for {branch_name}"
        
        messages = [f"DNOS from {branch_name}"]
        
        # Track what we got from private
        got_gi_from_private = stack.gi and stack.gi.is_valid
        got_baseos_from_private = stack.baseos and stack.baseos.is_valid
        
        if got_gi_from_private:
            messages.append(f"GI from {branch_name}")
        if got_baseos_from_private:
            messages.append(f"BaseOS from {branch_name}")
        
        # Check for missing components - only fallback if not found in private
        needs_gi = not got_gi_from_private
        needs_baseos = not got_baseos_from_private
        
        if needs_gi or needs_baseos:
            # Try to get from main branch
            main_branch = self.get_main_branch_for_version(branch_name)
            
            if main_branch and main_branch != branch_name:
                main_stack = self.get_latest_stack(main_branch)
                
                if main_stack:
                    if needs_gi and main_stack.gi and main_stack.gi.is_valid:
                        stack.gi = main_stack.gi
                        messages.append(f"GI from {main_branch} (fallback)")
                    
                    if needs_baseos and main_stack.baseos and main_stack.baseos.is_valid:
                        stack.baseos = main_stack.baseos
                        messages.append(f"BaseOS from {main_branch} (fallback)")
        
        return stack, ", ".join(messages)
    
    @staticmethod
    def extract_major_version(version_str: str) -> Tuple[int, int]:
        """Extract major.minor version from version string.
        
        Examples:
            '25.2.0.464_dev' -> (25, 2)
            '2.25204397329' (BaseOS) -> (25, 2)
            'dev_v25_1' -> (25, 1)
        """
        import re
        
        # Try standard format: 25.2.0.464
        match = re.match(r'(\d+)\.(\d+)', version_str)
        if match:
            return int(match.group(1)), int(match.group(2))
        
        # Try branch format: dev_v25_1
        match = re.search(r'v(\d+)[_.](\d+)', version_str)
        if match:
            return int(match.group(1)), int(match.group(2))
        
        # Try BaseOS format: 2.25204... (25 is major version)
        match = re.match(r'2\.(\d{2})(\d)', version_str)
        if match:
            return int(match.group(1)), int(match.group(2))
        
        return 0, 0
    
    @staticmethod
    def requires_delete_deploy(current_version: str, target_version: str) -> bool:
        """Check if upgrade requires delete + deploy (major version change).
        
        Args:
            current_version: Current DNOS version on device
            target_version: Target DNOS version to install
            
        Returns:
            True if major version differs (e.g., 25.4 -> 26.1)
        """
        current_major, _ = StackManager.extract_major_version(current_version)
        target_major, _ = StackManager.extract_major_version(target_version)
        
        if current_major == 0 or target_major == 0:
            return False  # Can't determine, assume no
        
        return current_major != target_major
    
    def check_freshness(self, stack: StackInfo) -> Tuple[bool, str]:
        """Check if a stack is fresh enough (< 48 hours).
        
        Returns:
            Tuple of (is_fresh, message)
        """
        if stack.is_expired:
            return False, f"Stack expired! Built {stack.age_str} (>48hrs). Minio URLs may be invalid."
        elif stack.age_hours > 40:
            return True, f"Warning: Stack is {stack.age_str}. Will expire soon."
        else:
            return True, f"Stack is fresh ({stack.age_str})"
    
    def validate_stack(self, stack: StackInfo) -> Tuple[bool, List[str]]:
        """Perform full validation on a stack.
        
        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []
        
        # Check completeness
        if not stack.has_core_components:
            issues.append(f"Missing components: {', '.join(stack.missing_components)}")
        
        # Check freshness
        if stack.is_expired:
            issues.append(f"Stack expired ({stack.age_str}). URLs may be invalid.")
        
        # Check version compatibility
        compat_ok, compat_msg = stack.validate_version_compatibility()
        if not compat_ok:
            issues.append(compat_msg)
        
        return len(issues) == 0, issues
    
    def list_available_stacks(self, branch_name: str, limit: int = 5) -> List[StackInfo]:
        """Get recent stacks for a branch.
        
        Args:
            branch_name: Branch to list stacks for
            limit: Maximum number of stacks to return
            
        Returns:
            List of StackInfo objects, most recent first
        """
        builds = self.jenkins.get_branch_builds(branch_name, limit=limit)
        
        stacks = []
        for build in builds:
            if build.result == 'SUCCESS':
                stack = self.get_stack_from_build(branch_name, build.build_number)
                if stack:
                    stacks.append(stack)
        
        return stacks
    
    def find_fresh_stack(self, branch_name: str) -> Tuple[Optional[StackInfo], str]:
        """Find a fresh, complete stack for a branch.
        
        Returns:
            Tuple of (StackInfo or None, message)
        """
        # Try latest first
        stack = self.get_latest_stack(branch_name)
        
        if not stack:
            return None, "No successful builds found for this branch"
        
        is_valid, issues = self.validate_stack(stack)
        
        if is_valid:
            return stack, f"Found valid stack: build #{stack.build_number}"
        
        # Check if it's just expired
        if stack.has_core_components and stack.is_expired:
            return stack, f"Stack expired ({stack.age_str}). Recommend triggering new build."
        
        # Stack has issues
        return stack, f"Stack issues: {'; '.join(issues)}"
    
    def clear_cache(self):
        """Clear the stack cache."""
        self._cache.clear()


# =============================================================================
# Convenience Functions
# =============================================================================

def get_stack(branch_name: str, build_number: int = None) -> Optional[StackInfo]:
    """Get stack info for a branch."""
    manager = StackManager()
    return manager.get_stack_from_build(branch_name, build_number)


def check_stack_freshness(branch_name: str) -> Dict:
    """Check if a branch has a fresh stack available."""
    manager = StackManager()
    stack = manager.get_latest_stack(branch_name)
    
    if not stack:
        return {
            'branch': branch_name,
            'has_stack': False,
            'message': 'No successful builds found'
        }
    
    is_fresh, message = manager.check_freshness(stack)
    is_valid, issues = manager.validate_stack(stack)
    
    return {
        'branch': branch_name,
        'has_stack': True,
        'build_number': stack.build_number,
        'build_time': stack.build_time.isoformat(),
        'age_hours': stack.age_hours,
        'is_fresh': is_fresh,
        'is_valid': is_valid,
        'issues': issues,
        'message': message,
        'dnos_version': stack.dnos.version if stack.dnos else None,
        'gi_version': stack.gi.version if stack.gi else None,
        'baseos_version': stack.baseos.version if stack.baseos else None
    }


def format_stack_summary(stack: StackInfo) -> str:
    """Format a stack as a human-readable summary."""
    lines = [
        f"Branch: {stack.branch}",
        f"Build: #{stack.build_number} ({stack.age_str})",
        "",
        "Components:",
    ]
    
    if stack.dnos:
        lines.append(f"  DNOS:   {stack.dnos.version or 'N/A'}")
    else:
        lines.append(f"  DNOS:   ❌ Missing")
    
    if stack.gi:
        lines.append(f"  GI:     {stack.gi.version or 'N/A'}")
    else:
        lines.append(f"  GI:     ❌ Missing")
    
    if stack.baseos:
        lines.append(f"  BaseOS: {stack.baseos.version or 'N/A'}")
    else:
        lines.append(f"  BaseOS: ❌ Missing")
    
    # Status
    lines.append("")
    if stack.is_expired:
        lines.append("⚠️  EXPIRED - URLs may be invalid")
    elif stack.age_hours > 40:
        lines.append("⚠️  Expires soon!")
    else:
        lines.append("✅ Stack is fresh")
    
    return "\n".join(lines)


if __name__ == "__main__":
    # Test stack manager
    print("Testing Stack Manager...")
    
    manager = StackManager()
    
    # List branches
    branches = manager.jenkins.list_dev_branches()
    print(f"\nFound {len(branches)} dev branches")
    
    if branches:
        # Get stack for first branch
        branch = branches[0].name
        print(f"\nGetting stack for {branch}...")
        
        stack = manager.get_latest_stack(branch)
        if stack:
            print(format_stack_summary(stack))
            
            # Validate
            is_valid, issues = manager.validate_stack(stack)
            if issues:
                print("\nIssues:")
                for issue in issues:
                    print(f"  - {issue}")

