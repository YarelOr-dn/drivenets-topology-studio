"""
Jenkins Integration for DNOS Image Management

Connects to DriveNets Jenkins to:
- List available DNOS branches and builds
- Download artifacts (DNOS, GI, BaseOS URLs)
- Trigger new builds with parameters
- Monitor build progress
"""

import requests
from requests.auth import HTTPBasicAuth
from typing import Optional, List, Dict, Tuple, Callable
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime, timedelta
import json
import re
import time
from urllib.parse import unquote, quote


@dataclass
class JenkinsConfig:
    """Jenkins connection configuration."""
    url: str = "https://jenkins.dev.drivenets.net"
    username: str = "yarelor-dn"
    api_token: str = "1127888ffe4ef65770a72228ceb1f334bd"
    
    @property
    def auth(self) -> HTTPBasicAuth:
        return HTTPBasicAuth(self.username, self.api_token)


@dataclass 
class JenkinsBuild:
    """Represents a Jenkins build."""
    job_name: str
    build_number: int
    result: str
    timestamp: int  # Unix timestamp in milliseconds
    url: str
    artifacts: List[Dict] = field(default_factory=list)
    building: bool = False
    duration: int = 0
    display_name: str = ""
    build_params: Dict = field(default_factory=dict)
    
    @property
    def build_time(self) -> datetime:
        """Convert timestamp to datetime."""
        return datetime.fromtimestamp(self.timestamp / 1000)
    
    @property
    def age_hours(self) -> float:
        """Get age of build in hours."""
        delta = datetime.now() - self.build_time
        return delta.total_seconds() / 3600
    
    @property
    def is_expired(self) -> bool:
        """Check if build is older than 48 hours (dnpkg-48hrs bucket retention)."""
        return self.age_hours > 48
    
    @property
    def is_sanitizer(self) -> bool:
        """Check if this build was compiled with AddressSanitizer (ASAN).
        
        Jenkins uses TESTS_TO_RUN (trigger_build sets this) or TEST_NAMES
        depending on pipeline version. Check both for compatibility.
        """
        test_names = str(self.build_params.get('TEST_NAMES', '')).upper()
        tests_to_run = str(self.build_params.get('TESTS_TO_RUN', '')).upper()
        return 'ENABLE_SANITIZER' in test_names or 'ENABLE_SANITIZER' in tests_to_run
    
    @property
    def has_image_artifacts(self) -> bool:
        """Check if this build has DNOS/GI image artifact files (even if build failed)."""
        artifact_names = [a.get('fileName', '').lower() for a in self.artifacts]
        has_dnos = any('dnos' in n and 'artifact' in n for n in artifact_names)
        has_gi = any(('gi_gi' in n or n == 'gi_artifact.txt') and 'artifact' in n for n in artifact_names)
        return has_dnos or has_gi
    
    def __str__(self) -> str:
        age = self.age_hours
        if age < 1:
            age_str = f"{int(age * 60)}min ago"
        elif age < 24:
            age_str = f"{age:.1f}hrs ago"
        else:
            age_str = f"{age/24:.1f}days ago"
        
        status = "[BUILDING]" if self.building else ("[OK]" if self.result == "SUCCESS" else "[FAIL]")
        expired = " [EXPIRED]" if self.is_expired else ""
        sanitizer = " [Sanitizer]" if self.is_sanitizer else ""
        
        return f"#{self.build_number} {status} {age_str}{expired}{sanitizer}"


def validate_artifact_url(url: str, timeout: int = 10) -> Tuple[bool, str]:
    """
    Validate that an artifact URL is still accessible on MinIO.
    
    Performs an HTTP HEAD request to check if the artifact exists.
    This catches cases where MinIO cleaned up artifacts before the 48h mark.
    
    Args:
        url: The MinIO artifact URL to validate
        timeout: Request timeout in seconds
        
    Returns:
        Tuple of (is_valid, status_message)
    """
    if not url or url == 'N/A':
        return False, "No URL provided"
    
    try:
        # Use HEAD request to check existence without downloading
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        
        if response.status_code == 200:
            size = response.headers.get('content-length', 0)
            if size:
                size_mb = int(size) / (1024 * 1024)
                return True, f"Available ({size_mb:.1f} MB)"
            return True, "Available"
        elif response.status_code == 404:
            return False, "Not found (404) - artifact expired or deleted"
        elif response.status_code == 403:
            return False, "Access denied (403)"
        else:
            return False, f"Error ({response.status_code})"
    except requests.Timeout:
        return False, "Timeout - MinIO may be unreachable"
    except requests.ConnectionError:
        return False, "Connection error - network issue"
    except Exception as e:
        return False, f"Error: {str(e)[:50]}"


def validate_stack_artifacts(stack: Dict, console=None) -> Tuple[bool, Dict[str, Tuple[bool, str]]]:
    """
    Validate all artifact URLs in a stack.
    
    Args:
        stack: Stack dict with dnos_url, gi_url, baseos_url
        console: Optional Rich console for live output
        
    Returns:
        Tuple of (all_valid, {component: (is_valid, message)})
    """
    results = {}
    all_valid = True
    
    components = [
        ('DNOS', stack.get('dnos_url')),
        ('GI', stack.get('gi_url')),
        ('BaseOS', stack.get('baseos_url')),
    ]
    
    for name, url in components:
        if url and url != 'N/A':
            if console:
                console.print(f"  [dim]Checking {name}...[/dim]", end="")
            
            is_valid, message = validate_artifact_url(url)
            results[name] = (is_valid, message)
            
            if console:
                if is_valid:
                    console.print(f"\r  [green]{name}: {message}[/green]")
                else:
                    console.print(f"\r  [red]{name}: {message}[/red]")
                    all_valid = False
            elif not is_valid:
                all_valid = False
    
    return all_valid, results


@dataclass
class CheetahBranch:
    """Represents a Cheetah branch (DNOS development branch)."""
    name: str
    url: str
    last_build: Optional[JenkinsBuild] = None
    
    @property
    def version(self) -> str:
        """Extract version from branch name (e.g., dev_v25_1 -> v25.1)."""
        match = re.search(r'v(\d+)_(\d+)', self.name)
        if match:
            return f"v{match.group(1)}.{match.group(2)}"
        return self.name


@dataclass
class ParsedJenkinsUrl:
    """Parsed components from a Jenkins URL (classic or Blue Ocean)."""
    job_path: str  # e.g., "drivenets/cheetah"
    branch_or_pr: str  # e.g., "dev_v26_1" or "PR-86760"
    build_number: Optional[int] = None
    is_pr: bool = False
    original_url: str = ""
    
    @property
    def jenkins_job_path(self) -> str:
        """Convert to Jenkins API job path format."""
        from urllib.parse import quote
        path_parts = self.job_path.split('/')
        job_path = '/job/' + '/job/'.join(path_parts)
        
        if self.is_pr:
            return f"{job_path}/view/change-requests/job/{self.branch_or_pr}"
        else:
            encoded_branch = quote(self.branch_or_pr, safe='')
            return f"{job_path}/job/{encoded_branch}"


class JenkinsClient:
    """Client for interacting with Jenkins API for DNOS builds."""
    
    CHEETAH_BASE = "/job/drivenets/job/cheetah"
    
    _branch_cache: Dict[str, Tuple[float, list]] = {}
    BRANCH_CACHE_TTL = 120  # seconds
    
    def __init__(self, config: JenkinsConfig = None):
        self.config = config or JenkinsConfig()
        self.session = requests.Session()
        self.session.auth = self.config.auth
        self.session.verify = False  # For internal certs
        
        # Suppress SSL warnings for internal Jenkins
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    @staticmethod
    def _encode_branch(name: str) -> str:
        """Normalize and double-encode a branch name for Jenkins URL segments.

        Accepts raw names (feature/dev_v26_2/branch), single-encoded
        (feature%2Fdev_v26_2%2Fbranch), or even double-encoded input.
        Always returns a correctly double-encoded string for /job/{branch}/ paths.
        """
        raw = name
        prev = None
        while prev != raw:
            prev = raw
            raw = unquote(raw)
        return quote(quote(raw, safe=''), safe='')

    def _api_get(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Make GET request to Jenkins API."""
        url = f"{self.config.url}{endpoint}"
        if not url.endswith('/api/json') and '/artifact/' not in url:
            url = url.rstrip('/') + '/api/json'
        
        try:
            resp = self.session.get(url, params=params, timeout=30)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            # Don't print for expected 404s
            if hasattr(e, 'response') and e.response is not None and e.response.status_code == 404:
                return None
            return None
    
    def _api_post(self, endpoint: str, params: Dict = None, data: Dict = None) -> Tuple[bool, str]:
        """Make POST request to Jenkins API."""
        url = f"{self.config.url}{endpoint}"
        
        try:
            resp = self.session.post(url, params=params, data=data, timeout=30)
            resp.raise_for_status()
            return True, "Success"
        except requests.exceptions.RequestException as e:
            return False, str(e)
    
    def test_connection(self) -> Tuple[bool, str]:
        """Test connection to Jenkins."""
        try:
            data = self._api_get('/')
            if data:
                return True, f"Connected to Jenkins (mode: {data.get('mode', 'unknown')})"
            return False, "No response from Jenkins"
        except Exception as e:
            return False, f"Connection failed: {str(e)}"
    
    # =========================================================================
    # Branch Management
    # =========================================================================
    
    def list_cheetah_branches(self, pattern: str = None, sort_newest_first: bool = True) -> List[CheetahBranch]:
        """List all Cheetah branches (DNOS development branches).
        
        Args:
            pattern: Regex pattern to filter branches
            sort_newest_first: If True, sort by version (newest first)
        """
        cache_key = f"{pattern or 'all'}_{sort_newest_first}"
        cached = JenkinsClient._branch_cache.get(cache_key)
        if cached:
            ts, branches = cached
            if time.time() - ts < self.BRANCH_CACHE_TTL:
                return branches
        
        data = self._api_get(self.CHEETAH_BASE, params={'tree': 'jobs[name,url]'})
        if not data or 'jobs' not in data:
            return []
        
        branches = []
        for job in data['jobs']:
            name = job.get('name', '')
            
            if pattern and not re.search(pattern, name, re.IGNORECASE):
                continue
            
            branch = CheetahBranch(
                name=name,
                url=job.get('url', '')
            )
            branches.append(branch)
        
        if sort_newest_first:
            def extract_version_tuple(branch: CheetahBranch) -> tuple:
                name = branch.name
                match = re.search(r'v(\d+)[._](\d+)(?:[._](\d+))?', name)
                if match:
                    major = int(match.group(1))
                    minor = int(match.group(2))
                    patch = int(match.group(3)) if match.group(3) else 0
                    return (major, minor, patch)
                return (0, 0, 0)
            
            branches.sort(key=extract_version_tuple, reverse=True)
        
        JenkinsClient._branch_cache[cache_key] = (time.time(), branches)
        return branches
    
    def list_dev_branches(self) -> List[CheetahBranch]:
        """List development branches (dev_v*), sorted newest first."""
        return self.list_cheetah_branches(pattern=r'^dev_v\d+', sort_newest_first=True)
    
    def list_release_branches(self) -> List[CheetahBranch]:
        """List release branches (rel_v*), sorted newest first."""
        return self.list_cheetah_branches(pattern=r'^rel_v\d+', sort_newest_first=True)

    def list_feature_branches(self) -> List[CheetahBranch]:
        """List feature branches (feature/*, fix/*, hotfix/*), sorted newest first."""
        return self.list_cheetah_branches(pattern=r'^(feature|fix|hotfix)(%2F|[/_])', sort_newest_first=True)
    
    def get_branch_builds(self, branch_name: str, limit: int = 10) -> List[JenkinsBuild]:
        """Get recent builds for a branch."""
        encoded_branch = self._encode_branch(branch_name)
        endpoint = f"{self.CHEETAH_BASE}/job/{encoded_branch}"
        data = self._api_get(endpoint)
        
        if not data or 'builds' not in data:
            return []
        
        builds = []
        for build_ref in data['builds'][:limit]:
            build_num = build_ref.get('number')
            if build_num:
                build = self.get_build_info(branch_name, build_num)
                if build:
                    builds.append(build)
        
        return builds
    
    # =========================================================================
    # Build Information
    # =========================================================================
    
    def get_build_info(self, branch_name: str, build_number: int = None, latest: bool = False) -> Optional[JenkinsBuild]:
        """Get build information including artifacts.
        
        Args:
            branch_name: Jenkins branch name
            build_number: Specific build number, or None for latest/lastSuccessful
            latest: If True and build_number is None, fetch lastBuild (includes in-progress).
                    If False, fetch lastSuccessfulBuild (only completed successful builds).
        """
        encoded_branch = self._encode_branch(branch_name)
        
        if build_number:
            endpoint = f"{self.CHEETAH_BASE}/job/{encoded_branch}/{build_number}"
        elif latest:
            endpoint = f"{self.CHEETAH_BASE}/job/{encoded_branch}/lastBuild"
        else:
            endpoint = f"{self.CHEETAH_BASE}/job/{encoded_branch}/lastSuccessfulBuild"
        
        data = self._api_get(endpoint)
        if not data:
            return None
        
        params = self._extract_build_params(data)
        
        return JenkinsBuild(
            job_name=branch_name,
            build_number=data.get('number', 0),
            result=data.get('result', 'UNKNOWN'),
            timestamp=data.get('timestamp', 0),
            url=data.get('url', ''),
            artifacts=data.get('artifacts', []),
            building=data.get('building', False),
            duration=data.get('duration', 0),
            display_name=data.get('displayName', '') or f"#{data.get('number', 0)}",
            build_params=params,
        )
    
    @staticmethod
    def _extract_build_params(build_data: Dict) -> Dict:
        """Extract build parameters from Jenkins API actions array."""
        params = {}
        for action in build_data.get('actions', []):
            cls = action.get('_class', '')
            if 'Parameter' in cls:
                for p in action.get('parameters', []):
                    name = p.get('name', '')
                    value = p.get('value', '')
                    if name:
                        params[name] = value
        return params
    
    def get_last_successful_build(self, branch_name: str) -> Optional[JenkinsBuild]:
        """Get the last successful build for a branch."""
        return self.get_build_info(branch_name, build_number=None)
    
    # Patterns to exclude from "pure" builds (NIGHTLY, platform-specific, etc.)
    EXCLUDED_BUILD_PATTERNS = [
        'NIGHTLY',
        'EMUX',
        'SILICON',
        'NCPL',
        'NCP3',
        'Polaris',
        'WBOX',
        'NCM',
        'NCR',
        'NCP1',
        'NCP40',
        'SA2',
        'SANITY',
    ]
    
    def get_latest_pure_build(self, branch_name: str, limit: int = 30,
                              include_failed: bool = False) -> Optional[Dict]:
        """Get the latest "pure" build (no NIGHTLY, platform-specific, etc.).
        
        Args:
            branch_name: The branch to check (e.g., 'dev_v26_1')
            limit: Maximum builds to scan
            include_failed: If True, also consider FAILED builds that have image artifacts.
                           Useful for feature branches where builds fail on tests but
                           produce valid DNOS/GI/BaseOS images.
            
        Returns:
            Dict with:
                'build': JenkinsBuild object
                'has_baseos': bool - whether BaseOS artifact is available
                'has_dnos': bool
                'has_gi': bool
                'artifacts': list of artifact names
                'is_sanitizer': bool - whether build uses AddressSanitizer
            Or None if no pure build found.
        """
        encoded_branch = self._encode_branch(branch_name)
        endpoint = f"{self.CHEETAH_BASE}/job/{encoded_branch}"
        data = self._api_get(endpoint)
        
        if not data or 'builds' not in data:
            return None
        
        for build_ref in data['builds'][:limit]:
            build_num = build_ref.get('number')
            if not build_num:
                continue
            
            build_endpoint = f"{self.CHEETAH_BASE}/job/{encoded_branch}/{build_num}"
            build_data = self._api_get(build_endpoint)
            
            if not build_data:
                continue
            
            if build_data.get('building', False):
                continue
            
            result = build_data.get('result', '')
            if not include_failed and result != 'SUCCESS':
                continue
            
            display_name = build_data.get('displayName', '') or f"#{build_num}"
            
            is_excluded = False
            for pattern in self.EXCLUDED_BUILD_PATTERNS:
                if pattern.upper() in display_name.upper():
                    is_excluded = True
                    break
            
            if is_excluded:
                continue
            
            artifacts = build_data.get('artifacts', [])
            artifact_names = [a.get('fileName', '') for a in artifacts]
            
            has_dnos = any('dnos' in name.lower() and 'artifact' in name.lower() for name in artifact_names)
            has_gi = any(('gi_gi' in name.lower() or name.lower() == 'gi_artifact.txt') and 'artifact' in name.lower() for name in artifact_names)
            has_baseos = any(('baseos' in name.lower() or 'base_os' in name.lower()) and 'artifact' in name.lower() for name in artifact_names)
            
            # For failed builds, only include if they have image artifacts
            if result != 'SUCCESS' and not (has_dnos or has_gi):
                continue
            
            params = self._extract_build_params(build_data)
            
            build = JenkinsBuild(
                job_name=branch_name,
                build_number=build_data.get('number', 0),
                result=build_data.get('result', 'UNKNOWN'),
                timestamp=build_data.get('timestamp', 0),
                url=build_data.get('url', ''),
                artifacts=artifacts,
                building=False,
                duration=build_data.get('duration', 0),
                display_name=display_name,
                build_params=params,
            )
            
            return {
                'build': build,
                'display_name': display_name,
                'has_dnos': has_dnos,
                'has_gi': has_gi,
                'has_baseos': has_baseos,
                'artifacts': artifact_names,
                'is_sanitizer': build.is_sanitizer,
            }
        
        return None
    
    def get_recent_builds_with_artifacts(self, branch_name: str, limit: int = 15,
                                          max_results: int = 10) -> List[Dict]:
        """List recent builds (success AND failed) that have image artifacts.
        
        Scans recent builds for a branch and returns all that have DNOS/GI/BaseOS
        artifact files, regardless of build result. Flags sanitizer builds.
        
        Useful for feature branches where builds may fail on tests but still
        produce valid installable images.
        
        Args:
            branch_name: The branch to check
            limit: Maximum builds to scan from Jenkins
            max_results: Maximum results to return
            
        Returns:
            List of dicts, each with:
                'build': JenkinsBuild, 'display_name': str,
                'has_dnos': bool, 'has_gi': bool, 'has_baseos': bool,
                'is_sanitizer': bool, 'artifacts': list
        """
        encoded_branch = self._encode_branch(branch_name)
        endpoint = f"{self.CHEETAH_BASE}/job/{encoded_branch}"
        tree = 'builds[number,result,timestamp,url,building,duration,displayName,artifacts[fileName],actions[parameters[name,value]]]{0,%d}' % limit
        data = self._api_get(endpoint, params={'tree': tree})
        
        if not data or 'builds' not in data:
            return []
        
        results = []
        for build_data in data['builds']:
            if len(results) >= max_results:
                break
            
            if not build_data or not build_data.get('number'):
                continue
            
            if build_data.get('building', False):
                continue
            
            display_name = build_data.get('displayName', '') or f"#{build_data['number']}"
            
            is_excluded = False
            for pattern in self.EXCLUDED_BUILD_PATTERNS:
                if pattern.upper() in display_name.upper():
                    is_excluded = True
                    break
            if is_excluded:
                continue
            
            artifacts = build_data.get('artifacts', [])
            artifact_names = [a.get('fileName', '') for a in artifacts]
            
            has_dnos = any('dnos' in name.lower() and 'artifact' in name.lower() for name in artifact_names)
            has_gi = any(('gi_gi' in name.lower() or name.lower() == 'gi_artifact.txt') and 'artifact' in name.lower() for name in artifact_names)
            has_baseos = any(('baseos' in name.lower() or 'base_os' in name.lower()) and 'artifact' in name.lower() for name in artifact_names)
            
            if not (has_dnos or has_gi):
                continue
            
            params = self._extract_build_params(build_data)
            
            build = JenkinsBuild(
                job_name=branch_name,
                build_number=build_data.get('number', 0),
                result=build_data.get('result', 'UNKNOWN'),
                timestamp=build_data.get('timestamp', 0),
                url=build_data.get('url', ''),
                artifacts=artifacts,
                building=False,
                duration=build_data.get('duration', 0),
                display_name=display_name,
                build_params=params,
            )
            
            results.append({
                'build': build,
                'display_name': display_name,
                'has_dnos': has_dnos,
                'has_gi': has_gi,
                'has_baseos': has_baseos,
                'is_sanitizer': build.is_sanitizer,
                'artifacts': artifact_names,
            })
        
        return results
    
    def get_console_log(self, branch_name: str, build_number: int, 
                        tail_lines: int = 200) -> Tuple[bool, str]:
        """Fetch console log from a Jenkins build.
        
        Args:
            branch_name: The branch name (e.g., 'easraf/flowspec_vpn/wbox_side')
            build_number: The build number
            tail_lines: Number of lines from the end to return (default 200)
            
        Returns:
            Tuple of (success, log_content or error_message)
        """
        encoded_branch = self._encode_branch(branch_name)
        
        url = f"{self.config.url}{self.CHEETAH_BASE}/job/{encoded_branch}/{build_number}/consoleText"
        
        try:
            resp = self.session.get(url, timeout=60)
            resp.raise_for_status()
            
            full_log = resp.text
            
            # Return last N lines
            lines = full_log.split('\n')
            if len(lines) > tail_lines:
                return True, '\n'.join(lines[-tail_lines:])
            return True, full_log
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return False, f"Build #{build_number} not found"
            return False, f"HTTP Error: {e.response.status_code}"
        except Exception as e:
            return False, f"Error fetching log: {str(e)}"
    
    def get_failed_stage_log(self, branch_name: str, build_number: int) -> Tuple[bool, str, str]:
        """Get the console log focused on the failed stage.
        
        Returns:
            Tuple of (success, failed_stage_name, relevant_log_lines)
        """
        success, log = self.get_console_log(branch_name, build_number, tail_lines=500)
        if not success:
            return False, "", log
        
        # Look for common failure patterns in the log
        lines = log.split('\n')
        
        # Find lines with ERROR, FAILURE, or exception
        error_lines = []
        failed_stage = "Unknown"
        
        for i, line in enumerate(lines):
            line_lower = line.lower()
            
            # Detect stage name
            if '[pipeline]' in line_lower and 'stage' in line_lower:
                # Extract stage name from lines like "[Pipeline] stage (Declarative: Pre-Build)"
                match = re.search(r'stage\s*\(([^)]+)\)', line, re.IGNORECASE)
                if match:
                    failed_stage = match.group(1)
            
            # Collect error context
            if any(x in line_lower for x in ['error:', 'failure:', 'failed:', 'exception', 'fatal:']):
                # Get surrounding context (5 lines before, 10 after)
                start = max(0, i - 5)
                end = min(len(lines), i + 10)
                error_lines.extend(lines[start:end])
                error_lines.append("---")
        
        if error_lines:
            return True, failed_stage, '\n'.join(error_lines[-100:])  # Last 100 lines of errors
        
        # No specific errors found, return tail
        return True, failed_stage, '\n'.join(lines[-50:])
    
    # =========================================================================
    # Artifact Retrieval
    # =========================================================================
    
    def get_artifact_content(self, branch_name: str, artifact_name: str, 
                             build_number: int = None) -> Optional[str]:
        """Download artifact content as text."""
        encoded_branch = self._encode_branch(branch_name)
        
        if build_number:
            url = f"{self.config.url}{self.CHEETAH_BASE}/job/{encoded_branch}/{build_number}/artifact/{artifact_name}"
        else:
            url = f"{self.config.url}{self.CHEETAH_BASE}/job/{encoded_branch}/lastSuccessfulBuild/artifact/{artifact_name}"
        
        try:
            resp = self.session.get(url, timeout=30)
            resp.raise_for_status()
            return resp.text.strip()
        except Exception:
            return None
    
    def get_dnos_artifact_url(self, branch_name: str, build_number: int = None) -> Optional[str]:
        """Get DNOS package URL from build artifacts."""
        content = self.get_artifact_content(branch_name, "gi_DNOS_artifact.txt", build_number)
        return content if content else None
    
    def get_gi_artifact_url(self, branch_name: str, build_number: int = None) -> Optional[str]:
        """Get GI package URL from build artifacts."""
        content = self.get_artifact_content(branch_name, "gi_GI_artifact.txt", build_number)
        return content if content else None
    
    def get_baseos_artifact_url(self, branch_name: str, build_number: int = None) -> Optional[str]:
        """Get BaseOS package URL from build artifacts."""
        # Try lowercase first (newer format), then uppercase (older format)
        content = self.get_artifact_content(branch_name, "gi_base_os_artifact.txt", build_number)
        if not content:
            content = self.get_artifact_content(branch_name, "gi_BaseOS_artifact.txt", build_number)
        return content if content else None
    
    def get_stack_urls(self, branch_name: str, build_number: int = None) -> Dict[str, Optional[str]]:
        """Get all stack component URLs (DNOS, GI, BaseOS)."""
        return {
            'dnos': self.get_dnos_artifact_url(branch_name, build_number),
            'gi': self.get_gi_artifact_url(branch_name, build_number),
            'baseos': self.get_baseos_artifact_url(branch_name, build_number)
        }
    
    # =========================================================================
    # Build Triggering
    # =========================================================================
    
    # Known bad nodes that have infrastructure issues
    # Updated automatically when builds fail due to infra issues
    _bad_nodes: List[str] = []
    _bad_nodes_file = Path("db/jenkins_bad_nodes.json")
    
    # Infrastructure failure patterns that indicate node issues (not code issues)
    INFRA_FAILURE_PATTERNS = [
        "cant reach consul",
        "can't reach consul", 
        "cannot reach consul",
        "this node is not a swarm manager",
        "connection refused",
        "no space left on device",
        "disk quota exceeded",
        "unable to delete",
        "workspace cleanup failed",
    ]
    
    def is_infrastructure_failure(self, branch_name: str, build_number: int) -> Tuple[bool, str, str]:
        """Check if a build failed due to infrastructure issues (not code issues).
        
        Returns:
            Tuple of (is_infra_failure, failure_reason, node_name)
        """
        try:
            success, log = self.get_console_log(branch_name, build_number, tail_lines=500)
            if not success:
                return False, "", ""
            
            log_lower = log.lower()
            
            # Extract node name
            node_name = ""
            for line in log.split('\n'):
                if 'NODE_NAME=' in line:
                    node_name = line.split('NODE_NAME=')[1].split()[0].strip()
                    break
            
            # Check for infrastructure failure patterns
            for pattern in self.INFRA_FAILURE_PATTERNS:
                if pattern.lower() in log_lower:
                    return True, pattern, node_name
            
            # Also check if build failed very quickly (< 5 minutes) - likely infra issue
            build = self.get_build_info(branch_name, build_number)
            if build and build.result == "FAILURE":
                duration_minutes = build.duration / 60000  # duration is in ms
                if duration_minutes < 5:
                    # Build failed in < 5 minutes, check for early stage failures
                    if "skipped due to earlier failure" in log_lower:
                        return True, f"Early failure ({duration_minutes:.1f}min)", node_name
            
            return False, "", node_name
            
        except Exception as e:
            return False, str(e), ""
    
    def _load_bad_nodes(self) -> List[str]:
        """Load list of known bad Jenkins nodes."""
        try:
            if self._bad_nodes_file.exists():
                with open(self._bad_nodes_file) as f:
                    data = json.load(f)
                    # Expire entries older than 24 hours
                    current_time = time.time()
                    valid_nodes = []
                    for entry in data.get('bad_nodes', []):
                        if current_time - entry.get('timestamp', 0) < 86400:  # 24 hours
                            valid_nodes.append(entry['node'])
                    return valid_nodes
        except:
            pass
        return []
    
    def _save_bad_node(self, node_name: str, reason: str):
        """Save a bad node to the blocklist."""
        try:
            self._bad_nodes_file.parent.mkdir(parents=True, exist_ok=True)
            
            data = {'bad_nodes': []}
            if self._bad_nodes_file.exists():
                with open(self._bad_nodes_file) as f:
                    data = json.load(f)
            
            # Add new entry (or update existing)
            nodes = data.get('bad_nodes', [])
            nodes = [n for n in nodes if n.get('node') != node_name]  # Remove old entry
            nodes.append({
                'node': node_name,
                'reason': reason,
                'timestamp': time.time(),
            })
            
            data['bad_nodes'] = nodes
            with open(self._bad_nodes_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception:
            pass
    
    def trigger_build(self, branch_name: str, 
                      with_baseos: bool = True,
                      qa_version: bool = False,
                      with_sanitizer: bool = False,
                      parameters: Dict = None) -> Tuple[bool, str]:
        """Trigger a new build on a branch.
        
        Args:
            branch_name: The branch to build -- accepts raw (feature/branch)
                         or pre-encoded (feature%2Fbranch) names.
            with_baseos: Whether to build BaseOS containers
            qa_version: Whether this is a QA version (60-day retention)
            with_sanitizer: Whether to enable AddressSanitizer (ASAN) compilation
            parameters: Additional build parameters
            
        Returns:
            Tuple of (success, message/queue_url)
        """
        encoded_branch = self._encode_branch(branch_name)
        endpoint = f"{self.CHEETAH_BASE}/job/{encoded_branch}/buildWithParameters"
        
        params = {
            'SHOULD_LINT': 'Yes',
            'SHOULD_BUILD_DNOS_CONTAINERS': 'Yes',
            'SHOULD_BUILD_TARBALLS': 'Yes',
            'SHOULD_BUILD_BASEOS_CONTAINERS': 'Yes' if with_baseos else 'No',
            'SHOULD_RUN_SMOKE_TESTS': 'Yes',
            'SHOULD_ALLOW_DELTA_BUILD': 'No',
            'TESTS_TO_RUN': 'No Tests',
        }
        
        if with_sanitizer:
            params['TEST_NAMES'] = 'ENABLE_SANITIZER'
        
        if qa_version:
            params['QA_VERSION'] = 'true'
        
        if parameters:
            params.update(parameters)
        
        success, message = self._api_post(endpoint, params=params)
        
        if success:
            return True, f"Build triggered for {branch_name}"
        else:
            return False, f"Failed to trigger build: {message}"
    
    def get_queue_item(self, queue_id: int) -> Optional[Dict]:
        """Get information about a queued build."""
        data = self._api_get(f"/queue/item/{queue_id}")
        return data
    
    def wait_for_build_start(self, branch_name: str, timeout: int = 300, 
                             poll_interval: int = 5) -> Optional[int]:
        """Wait for a triggered build to start and return build number."""
        start_time = time.time()
        
        # Get current last build number
        current_build = self.get_build_info(branch_name)
        last_known = current_build.build_number if current_build else 0
        
        while time.time() - start_time < timeout:
            time.sleep(poll_interval)
            
            # Check for new build
            new_build = self.get_build_info(branch_name)
            if new_build and new_build.build_number > last_known:
                return new_build.build_number
        
        return None
    
    def wait_for_build_completion(self, branch_name: str, build_number: int,
                                   timeout: int = 3600, poll_interval: int = 30,
                                   progress_callback: Callable[[str, int], None] = None) -> Optional[JenkinsBuild]:
        """Wait for a build to complete.
        
        Args:
            branch_name: Branch name
            build_number: Build number to monitor
            timeout: Maximum wait time in seconds
            poll_interval: Time between status checks
            progress_callback: Optional callback(message, percent)
            
        Returns:
            Final build info or None on timeout
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            build = self.get_build_info(branch_name, build_number)
            
            if not build:
                time.sleep(poll_interval)
                continue
            
            if progress_callback:
                elapsed = int(time.time() - start_time)
                status = "Building..." if build.building else build.result
                progress_callback(f"Build #{build_number}: {status} ({elapsed}s)", 
                                  min(95, int((elapsed / timeout) * 100)))
            
            if not build.building and build.result:
                return build
            
            time.sleep(poll_interval)
        
        return None
    
    def trigger_build_with_retry(self, branch_name: str,
                                  with_baseos: bool = True,
                                  qa_version: bool = False,
                                  max_retries: int = 3,
                                  progress_callback: Callable[[str, int], None] = None) -> Tuple[bool, int, str]:
        """Trigger a build with automatic retry on infrastructure failures.
        
        This function will:
        1. Trigger a build
        2. Wait for it to complete
        3. If it fails due to infrastructure issues, automatically retry
        4. Track bad nodes to help future builds
        
        Args:
            branch_name: Branch to build
            with_baseos: Whether to include BaseOS
            qa_version: QA version flag
            max_retries: Maximum number of retry attempts
            progress_callback: Optional callback(message, percent)
            
        Returns:
            Tuple of (success, final_build_number, message)
        """
        attempt = 0
        last_error = ""
        
        while attempt < max_retries:
            attempt += 1
            
            if progress_callback:
                progress_callback(f"Attempt {attempt}/{max_retries}: Triggering build...", 5)
            
            # Trigger the build
            success, message = self.trigger_build(branch_name, with_baseos, qa_version)
            if not success:
                last_error = message
                continue
            
            # Wait for build to start
            if progress_callback:
                progress_callback(f"Attempt {attempt}/{max_retries}: Waiting for build to start...", 10)
            
            build_number = self.wait_for_build_start(branch_name, timeout=180)
            if not build_number:
                last_error = "Build did not start within timeout"
                continue
            
            if progress_callback:
                progress_callback(f"Attempt {attempt}/{max_retries}: Build #{build_number} started", 15)
            
            # Wait for completion with progress updates
            def internal_progress(msg, pct):
                if progress_callback:
                    # Scale progress: 15-90% for build phase
                    scaled_pct = 15 + int(pct * 0.75)
                    progress_callback(f"Attempt {attempt}: {msg}", scaled_pct)
            
            build = self.wait_for_build_completion(
                branch_name, build_number,
                timeout=3600,  # 1 hour
                poll_interval=30,
                progress_callback=internal_progress
            )
            
            if not build:
                last_error = "Build timed out"
                continue
            
            if build.result == "SUCCESS":
                if progress_callback:
                    progress_callback(f"Build #{build_number} SUCCESS!", 100)
                return True, build_number, f"Build #{build_number} completed successfully"
            
            # Build failed - check if it's an infrastructure issue
            is_infra, reason, node_name = self.is_infrastructure_failure(branch_name, build_number)
            
            if is_infra:
                if progress_callback:
                    progress_callback(f"Build #{build_number} failed (infra: {reason}) - retrying...", 15)
                
                # Track the bad node
                if node_name:
                    self._save_bad_node(node_name, reason)
                
                last_error = f"Infrastructure failure on {node_name}: {reason}"
                
                # Wait a bit before retry
                time.sleep(10)
                continue
            else:
                # Real build failure (code issue), don't retry
                if progress_callback:
                    progress_callback(f"Build #{build_number} FAILED (code issue)", 100)
                return False, build_number, f"Build #{build_number} failed: {build.result}"
        
        # All retries exhausted
        return False, 0, f"All {max_retries} attempts failed. Last error: {last_error}"
    
    # =========================================================================
    # URL Parsing and Direct Build Access
    # =========================================================================
    
    @staticmethod
    def parse_jenkins_url(url: str) -> Optional[ParsedJenkinsUrl]:
        """Parse a Jenkins URL (Blue Ocean or classic) to extract job/build info.
        
        Supported URL formats (with build number):
        1. Blue Ocean: .../blue/organizations/jenkins/drivenets%2Fcheetah/detail/PR-86760/5/pipeline
        2. Blue Ocean branch: .../blue/organizations/jenkins/drivenets%2Fcheetah/detail/dev_v26_1/123/pipeline
        3. Classic: .../job/drivenets/job/cheetah/job/dev_v26_1/123/
        4. Classic PR: .../job/drivenets/job/cheetah/view/change-requests/job/PR-86760/5/
        
        Branch-only formats (no build number -- resolves to lastSuccessfulBuild):
        5. Classic branch-only: .../job/drivenets/job/cheetah/job/feature%252Fdev_v26_2%252Fbranch_name
        6. Blue Ocean branch-only: .../blue/organizations/jenkins/drivenets%2Fcheetah/detail/dev_v26_1
        7. Classic PR-only: .../job/drivenets/job/cheetah/view/change-requests/job/PR-86760
        
        Returns:
            ParsedJenkinsUrl object or None if URL cannot be parsed.
            build_number will be None for branch-only URLs.
        """
        if not url:
            return None
        
        # Clean URL for end-anchored patterns (strip whitespace, query params, fragments, trailing slashes)
        clean = url.strip().split('?')[0].split('#')[0].rstrip('/')
        
        # --- Patterns WITH build number (try these first) ---
        
        # Blue Ocean URL pattern
        # Format: /blue/organizations/jenkins/{job_path_encoded}/detail/{branch_or_pr}/{build_number}/...
        blue_ocean_pattern = r'/blue/organizations/jenkins/([^/]+)/detail/([^/]+)/(\d+)'
        match = re.search(blue_ocean_pattern, url)
        
        if match:
            job_path_encoded = match.group(1)
            branch_or_pr = match.group(2)
            build_number = int(match.group(3))
            
            job_path = unquote(job_path_encoded)
            is_pr = branch_or_pr.upper().startswith('PR-')
            
            return ParsedJenkinsUrl(
                job_path=job_path,
                branch_or_pr=branch_or_pr,
                build_number=build_number,
                is_pr=is_pr,
                original_url=url
            )
        
        # Classic URL pattern for regular branches
        # Format: /job/drivenets/job/cheetah/job/{branch}/{build_number}/
        classic_pattern = r'/job/([^/]+)/job/([^/]+)/job/([^/]+)/(\d+)'
        match = re.search(classic_pattern, url)
        
        if match:
            org = match.group(1)
            repo = match.group(2)
            branch = match.group(3)
            build_number = int(match.group(4))
            
            branch = unquote(unquote(branch))
            
            return ParsedJenkinsUrl(
                job_path=f"{org}/{repo}",
                branch_or_pr=branch,
                build_number=build_number,
                is_pr=False,
                original_url=url
            )
        
        # Classic URL pattern for PRs
        # Format: /job/drivenets/job/cheetah/view/change-requests/job/PR-XXXX/{build_number}/
        classic_pr_pattern = r'/job/([^/]+)/job/([^/]+)/view/change-requests/job/(PR-\d+)/(\d+)'
        match = re.search(classic_pr_pattern, url)
        
        if match:
            org = match.group(1)
            repo = match.group(2)
            pr = match.group(3)
            build_number = int(match.group(4))
            
            return ParsedJenkinsUrl(
                job_path=f"{org}/{repo}",
                branch_or_pr=pr,
                build_number=build_number,
                is_pr=True,
                original_url=url
            )
        
        # --- Branch-only patterns (no build number) ---
        
        # Classic branch-only (handles double-encoded slashes like %252F in branch names)
        classic_branch_only = r'/job/([^/]+)/job/([^/]+)/job/([^/]+)$'
        match = re.search(classic_branch_only, clean)
        
        if match:
            org = match.group(1)
            repo = match.group(2)
            branch = match.group(3)
            branch = unquote(unquote(branch))
            
            return ParsedJenkinsUrl(
                job_path=f"{org}/{repo}",
                branch_or_pr=branch,
                build_number=None,
                is_pr=False,
                original_url=url
            )
        
        # Classic PR-only (no build number)
        classic_pr_only = r'/job/([^/]+)/job/([^/]+)/view/change-requests/job/(PR-\d+)$'
        match = re.search(classic_pr_only, clean)
        
        if match:
            org = match.group(1)
            repo = match.group(2)
            pr = match.group(3)
            
            return ParsedJenkinsUrl(
                job_path=f"{org}/{repo}",
                branch_or_pr=pr,
                build_number=None,
                is_pr=True,
                original_url=url
            )
        
        # Blue Ocean branch-only (no build number)
        blue_branch_only = r'/blue/organizations/jenkins/([^/]+)/detail/([^/]+)$'
        match = re.search(blue_branch_only, clean)
        
        if match:
            job_path = unquote(match.group(1))
            branch_or_pr = match.group(2)
            is_pr = branch_or_pr.upper().startswith('PR-')
            
            return ParsedJenkinsUrl(
                job_path=job_path,
                branch_or_pr=branch_or_pr,
                build_number=None,
                is_pr=is_pr,
                original_url=url
            )
        
        return None
    
    def get_build_from_url(self, url: str) -> Optional[JenkinsBuild]:
        """Get build information from a Jenkins URL (Blue Ocean or classic).
        
        For branch-only URLs (no build number), tries lastSuccessfulBuild
        then falls back to lastBuild.
        
        Args:
            url: A Jenkins URL in Blue Ocean or classic format
            
        Returns:
            JenkinsBuild object or None if build cannot be found
        """
        parsed = self.parse_jenkins_url(url)
        if not parsed:
            return None
        
        if parsed.build_number is not None:
            endpoint = f"{parsed.jenkins_job_path}/{parsed.build_number}"
            data = self._api_get(endpoint)
        else:
            data = self._api_get(f"{parsed.jenkins_job_path}/lastSuccessfulBuild")
            if not data:
                data = self._api_get(f"{parsed.jenkins_job_path}/lastBuild")
        
        if not data:
            return None
        
        return JenkinsBuild(
            job_name=parsed.branch_or_pr,
            build_number=data.get('number', 0),
            result=data.get('result', 'UNKNOWN'),
            timestamp=data.get('timestamp', 0),
            url=data.get('url', ''),
            artifacts=data.get('artifacts', []),
            building=data.get('building', False),
            duration=data.get('duration', 0)
        )
    
    def get_stack_urls_from_url(self, url: str) -> Dict[str, Optional[str]]:
        """Get all stack component URLs (DNOS, GI, BaseOS) from a Jenkins URL.
        
        Args:
            url: A Jenkins URL in Blue Ocean or classic format
            
        Returns:
            Dict with 'dnos', 'gi', 'baseos' keys containing URLs or None
        """
        parsed = self.parse_jenkins_url(url)
        if not parsed:
            return {'dnos': None, 'gi': None, 'baseos': None, 'error': 'Could not parse URL'}
        
        return self.get_stack_urls_from_parsed(parsed)
    
    def get_stack_urls_from_parsed(self, parsed: ParsedJenkinsUrl) -> Dict[str, Optional[str]]:
        """Get stack URLs using parsed URL info."""
        build_ref = str(parsed.build_number) if parsed.build_number is not None else 'lastSuccessfulBuild'
        base_url = f"{self.config.url}{parsed.jenkins_job_path}/{build_ref}/artifact"
        
        result = {}
        # Define artifacts with fallback filenames for baseos
        artifacts = [
            ('dnos', ['gi_DNOS_artifact.txt']),
            ('gi', ['gi_GI_artifact.txt']),
            ('baseos', ['gi_base_os_artifact.txt', 'gi_BaseOS_artifact.txt'])  # Try lowercase first
        ]
        
        for artifact_type, filenames in artifacts:
            result[artifact_type] = None
            for filename in filenames:
                try:
                    url = f"{base_url}/{filename}"
                    resp = self.session.get(url, timeout=30)
                    resp.raise_for_status()
                    result[artifact_type] = resp.text.strip()
                    break  # Found it, stop trying alternatives
                except Exception:
                    continue
        
        return result
    
    # =========================================================================
    # Utility Functions
    # =========================================================================
    
    def get_jobs(self, folder: str = None) -> List[Dict]:
        """Get list of jobs, optionally from a folder."""
        endpoint = f"/job/{folder}" if folder else "/"
        data = self._api_get(endpoint)
        
        if data and 'jobs' in data:
            return data['jobs']
        return []
    
    def search_jobs(self, pattern: str) -> List[Dict]:
        """Search for jobs matching a pattern (e.g., 'DNOS', 'image', 'release')."""
        all_jobs = []
        
        def search_recursive(path: str = ""):
            jobs = self.get_jobs(path.strip('/') if path else None)
            for job in jobs:
                job_class = job.get('_class', '')
                job_name = job.get('name', '')
                full_path = f"{path}/{job_name}".strip('/')
                
                # Check if matches pattern
                if re.search(pattern, job_name, re.IGNORECASE):
                    job['full_path'] = full_path
                    all_jobs.append(job)
                
                # If it's a folder, recurse (limit depth)
                if ('folder' in job_class.lower() or 'Folder' in job_class) and path.count('/') < 3:
                    search_recursive(full_path)
        
        search_recursive()
        return all_jobs
    
    def download_artifact(self, branch_name: str, artifact_path: str, 
                          build_number: int = None, dest_path: str = None) -> Optional[Path]:
        """Download an artifact from Jenkins."""
        encoded_branch = self._encode_branch(branch_name)
        if build_number:
            url = f"{self.config.url}{self.CHEETAH_BASE}/job/{encoded_branch}/{build_number}/artifact/{artifact_path}"
        else:
            url = f"{self.config.url}{self.CHEETAH_BASE}/job/{encoded_branch}/lastSuccessfulBuild/artifact/{artifact_path}"
        
        try:
            resp = self.session.get(url, stream=True, timeout=300)
            resp.raise_for_status()
            
            # Determine destination
            if not dest_path:
                dest_path = Path('/tmp') / Path(artifact_path).name
            else:
                dest_path = Path(dest_path)
            
            # Download with progress
            total_size = int(resp.headers.get('content-length', 0))
            downloaded = 0
            
            with open(dest_path, 'wb') as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
            
            return dest_path
            
        except Exception as e:
            return None


# =============================================================================
# Convenience Functions
# =============================================================================

def test_jenkins_connection() -> Tuple[bool, str]:
    """Quick test of Jenkins connection."""
    client = JenkinsClient()
    return client.test_connection()


def list_dev_branches() -> List[CheetahBranch]:
    """List available development branches."""
    client = JenkinsClient()
    return client.list_dev_branches()


def get_stack_for_branch(branch_name: str, build_number: int = None) -> Dict:
    """Get stack URLs for a specific branch and build."""
    client = JenkinsClient()
    
    build = client.get_build_info(branch_name, build_number)
    if not build:
        return {'error': 'Build not found'}
    
    urls = client.get_stack_urls(branch_name, build.build_number)
    
    return {
        'branch': branch_name,
        'build': build.build_number,
        'build_time': build.build_time.isoformat(),
        'age_hours': build.age_hours,
        'is_expired': build.is_expired,
        'result': build.result,
        'dnos_url': urls.get('dnos'),
        'gi_url': urls.get('gi'),
        'baseos_url': urls.get('baseos')
    }


def get_stack_from_url(url: str) -> Dict:
    """Get stack URLs from a Jenkins URL (Blue Ocean or classic format).
    
    Supports URLs like:
    - https://jenkins.dev.drivenets.net/blue/organizations/jenkins/drivenets%2Fcheetah/detail/PR-86760/5/pipeline
    - https://jenkins.dev.drivenets.net/blue/organizations/jenkins/drivenets%2Fcheetah/detail/dev_v26_1/123/pipeline
    - Classic job URLs as well
    
    Args:
        url: A Jenkins URL
        
    Returns:
        Dict with build info and stack URLs
    """
    client = JenkinsClient()
    
    parsed = client.parse_jenkins_url(url)
    if not parsed:
        return {'error': f'Could not parse Jenkins URL: {url}'}
    
    build = client.get_build_from_url(url)
    if not build:
        return {
            'error': 'Build not found',
            'parsed_job_path': parsed.jenkins_job_path,
            'parsed_branch': parsed.branch_or_pr,
            'parsed_build': parsed.build_number
        }
    
    # For branch-only URLs, update parsed with the resolved build number
    # so get_stack_urls_from_parsed uses the concrete number instead of lastSuccessfulBuild
    if parsed.build_number is None:
        parsed.build_number = build.build_number
    
    urls = client.get_stack_urls_from_parsed(parsed)
    
    return {
        'branch': parsed.branch_or_pr,
        'is_pr': parsed.is_pr,
        'job_path': parsed.job_path,
        'build': build.build_number,
        'build_time': build.build_time.isoformat(),
        'age_hours': build.age_hours,
        'is_expired': build.is_expired,
        'result': build.result,
        'building': build.building,
        'dnos_url': urls.get('dnos'),
        'gi_url': urls.get('gi'),
        'baseos_url': urls.get('baseos')
    }


def parse_jenkins_url(url: str) -> Optional[ParsedJenkinsUrl]:
    """Parse a Jenkins URL to extract components.
    
    Convenience wrapper around JenkinsClient.parse_jenkins_url()
    """
    return JenkinsClient.parse_jenkins_url(url)


if __name__ == "__main__":
    import sys
    
    # Check if a URL was provided as argument
    if len(sys.argv) > 1:
        url = sys.argv[1]
        print(f"Parsing Jenkins URL: {url}")
        
        parsed = parse_jenkins_url(url)
        if parsed:
            print(f"  Job Path: {parsed.job_path}")
            print(f"  Branch/PR: {parsed.branch_or_pr}")
            print(f"  Build #: {parsed.build_number}")
            print(f"  Is PR: {parsed.is_pr}")
            print(f"  Jenkins API Path: {parsed.jenkins_job_path}")
            
            print("\nFetching build info and stack URLs...")
            stack = get_stack_from_url(url)
            
            if 'error' in stack:
                print(f"  Error: {stack['error']}")
            else:
                print(f"  Result: {stack.get('result')}")
                print(f"  Building: {stack.get('building')}")
                print(f"  Age: {stack.get('age_hours', 0):.1f}hrs")
                print(f"  Expired: {stack.get('is_expired')}")
                print(f"  DNOS: {stack.get('dnos_url', 'N/A')}")
                print(f"  GI: {stack.get('gi_url', 'N/A')}")
                print(f"  BaseOS: {stack.get('baseos_url', 'N/A')}")
        else:
            print("  Could not parse URL!")
        
        sys.exit(0)
    
    # Test the connection
    print("Testing Jenkins connection...")
    success, message = test_jenkins_connection()
    print(f"{'✓' if success else '✗'} {message}")
    
    if success:
        print("\nListing development branches...")
        branches = list_dev_branches()
        for b in branches[:10]:
            print(f"  - {b.name} ({b.version})")
        
        if branches:
            # Get stack for first branch
            print(f"\nGetting stack for {branches[0].name}...")
            stack = get_stack_for_branch(branches[0].name)
            print(f"  Build: #{stack.get('build')}")
            print(f"  Age: {stack.get('age_hours', 0):.1f}hrs")
            print(f"  Expired: {stack.get('is_expired')}")
            print(f"  DNOS: {stack.get('dnos_url', 'N/A')[:80]}...")
        
        # Test URL parsing
        print("\n--- URL Parsing Examples ---")
        test_urls = [
            "https://jenkins.dev.drivenets.net/blue/organizations/jenkins/drivenets%2Fcheetah/detail/PR-86760/5/pipeline",
            "https://jenkins.dev.drivenets.net/blue/organizations/jenkins/drivenets%2Fcheetah/detail/dev_v26_1/123/pipeline",
            "https://jenkins.dev.drivenets.net/job/drivenets/job/cheetah/job/dev_v26_1/456/",
        ]
        
        for url in test_urls:
            parsed = parse_jenkins_url(url)
            if parsed:
                print(f"\n  URL: ...{url[-60:]}")
                print(f"  -> {parsed.branch_or_pr} #{parsed.build_number} (PR: {parsed.is_pr})")
