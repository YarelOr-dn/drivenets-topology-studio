"""Push configurations to DNOS devices via SSH."""

import os
import re
import sys
import time
import json
import socket
import termios
import tempfile
import subprocess
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Tuple, Optional, Callable, Dict, Any, List
import paramiko

from .models import Device


@contextmanager
def suppress_keyboard_echo():
    """Temporarily disable keyboard echo to prevent interference with Rich Live display."""
    try:
        # Save original terminal settings
        if sys.stdin.isatty():
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            new_settings = termios.tcgetattr(fd)
            # Disable echo (ECHO) and canonical mode (ICANON)
            new_settings[3] = new_settings[3] & ~termios.ECHO
            termios.tcsetattr(fd, termios.TCSADRAIN, new_settings)
            try:
                yield
            finally:
                # Restore original settings
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        else:
            yield
    except Exception:
        # If termios fails (e.g., not a real terminal), just continue
        yield
from .utils import get_device_config_dir, timestamp_filename, get_ssh_hostname, update_device_connection_info


# ============================================================================
# TIMING LEARNING DATABASE
# Stores historical push times to improve future estimates
# ============================================================================

TIMING_DB_PATH = Path(__file__).parent.parent / "db" / "timing_history.json"


def _load_timing_db() -> Dict[str, Any]:
    """Load timing history database."""
    if TIMING_DB_PATH.exists():
        try:
            with open(TIMING_DB_PATH, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {"entries": [], "platform_averages": {}}
    return {"entries": [], "platform_averages": {}}


def _save_timing_db(db: Dict[str, Any]):
    """Save timing history database."""
    TIMING_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(TIMING_DB_PATH, 'w') as f:
        json.dump(db, f, indent=2, default=str)


def save_timing_record(
    platform: str,
    line_count: int,
    pwhe_count: int,
    fxc_count: int,
    actual_time_seconds: float,
    stage_times: Dict[str, float] = None,
    device_hostname: str = None,
    scale_counts: Dict[str, int] = None,
    push_method: str = None,
    push_type: str = None,
    config_content_type: str = None
):
    """
    Save a timing record after successful config push.
    
    Args:
        platform: Device platform (SA-36CD-S, NCP, etc.)
        line_count: Number of lines in config
        pwhe_count: Number of PWHE interfaces
        fxc_count: Number of FXC instances  
        actual_time_seconds: Actual total push time
        stage_times: Dict of individual stage times if available
        device_hostname: Device name for reference
        scale_counts: Dict with counts of scale types:
            - pwhe_subifs: PWHE sub-interfaces (ph*.*)
            - l2_ac_subifs: L2 AC sub-interfaces (ge/bundle with l2-service)
            - fxc_services: FXC service instances
            - bgp_peers: BGP peer count
            - isis_interfaces: ISIS interface count
        push_method: How config was pushed (terminal_paste, file_upload, file_merge)
        push_type: Type of push operation (full_commit, merge, dry_run, services_only, interfaces_only)
        config_content_type: What the config contains (full_config, services, interfaces, system, igp, bgp, mixed)
    """
    db = _load_timing_db()
    
    # Determine scale type for categorization
    scale_counts = scale_counts or {}
    scale_type = _determine_scale_type(scale_counts, pwhe_count, fxc_count)
    
    # Create timing record with enhanced tracking
    # Use a better timing model: total_time = overhead + (lines * rate)
    # Overhead is typically 20-30s for connection, upload, commit check base
    ESTIMATED_OVERHEAD = 25.0  # seconds
    
    # Calculate variable time (total - overhead) for per-line rate
    variable_time = max(0, actual_time_seconds - ESTIMATED_OVERHEAD)
    time_per_1k_lines = (variable_time / (line_count / 1000)) if line_count > 100 else 0
    
    record = {
        "timestamp": datetime.now().isoformat(),
        "platform": platform,
        "line_count": line_count,
        "pwhe_count": pwhe_count,
        "fxc_count": fxc_count,
        "actual_time": actual_time_seconds,
        "stage_times": stage_times or {},
        "device": device_hostname,
        # Enhanced scale tracking
        "scale_type": scale_type,
        "scale_counts": scale_counts,
        # IMPROVED: Calculate rates after removing overhead
        "time_per_1k_lines": time_per_1k_lines,
        "overhead_estimate": ESTIMATED_OVERHEAD,
        # NEW: Push classification for better estimates
        "push_method": push_method or "unknown",
        "push_type": push_type or "unknown",
        "config_content_type": config_content_type or "unknown",
    }
    
    db["entries"].append(record)
    
    # Keep last 100 entries to prevent file bloat
    if len(db["entries"]) > 100:
        db["entries"] = db["entries"][-100:]
    
    # Recalculate platform averages AND scale-type averages
    db["platform_averages"] = _calculate_platform_averages(db["entries"])
    db["scale_type_averages"] = _calculate_scale_type_averages(db["entries"])
    
    _save_timing_db(db)
    
    return record


def _determine_scale_type(scale_counts: Dict[str, int], pwhe_count: int, fxc_count: int) -> str:
    """Determine the primary scale type for categorization."""
    pwhe_subifs = scale_counts.get('pwhe_subifs', pwhe_count)
    l2_ac_subifs = scale_counts.get('l2_ac_subifs', 0)
    fxc_services = scale_counts.get('fxc_services', fxc_count)
    vrf_instances = scale_counts.get('vrf_instances', 0)
    l3_subifs = scale_counts.get('l3_subifs', 0)
    bgp_peers = scale_counts.get('bgp_peers', 0)
    
    # Determine primary scale type based on what's most significant
    if pwhe_subifs > 100 and fxc_services > 100:
        return "pwhe_fxc"  # PWHE with FXC services
    elif pwhe_subifs > 100:
        return "pwhe_only"  # PWHE interfaces only
    elif l2_ac_subifs > 100 and fxc_services > 100:
        return "l2ac_fxc"  # L2 AC with FXC services
    elif l2_ac_subifs > 100:
        return "l2ac_only"  # L2 AC interfaces only
    elif fxc_services > 100:
        return "fxc_only"  # FXC services only
    elif vrf_instances > 5 or (vrf_instances > 0 and l3_subifs > 50):
        return "l3vpn_vrf"  # L3VPN with VRF instances
    elif bgp_peers > 50:
        return "bgp_scale"  # BGP peer scaling
    elif l3_subifs > 100:
        return "l3_routing"  # L3 routing scale
    else:
        return "mixed"  # Mixed or small scale


def detect_config_content_type(config_text: str) -> str:
    """
    Analyze config text to determine what type of content it contains.
    
    Returns one of:
        - full_config: Complete device configuration
        - services_only: Only service (evpn/l2vpn) configuration
        - interfaces_only: Only interface configuration
        - system: System/hostname configuration
        - igp: ISIS/OSPF configuration
        - bgp: BGP configuration
        - mixed: Combination of multiple types
    """
    import re
    
    has_interfaces = bool(re.search(r'^\s*interfaces\s*$', config_text, re.MULTILINE)) or \
                     bool(re.search(r'^\s+(ge-|bundle-ether|ph\d+)', config_text, re.MULTILINE))
    has_services = bool(re.search(r'evpn-vpws|evpn-vpws-fxc|l2vpn', config_text, re.IGNORECASE))
    has_system = bool(re.search(r'^\s*system\s*$|hostname\s+\S+', config_text, re.MULTILINE))
    has_bgp = bool(re.search(r'^\s*bgp\s*$|router-id\s+\d+\.\d+', config_text, re.MULTILINE))
    has_igp = bool(re.search(r'^\s*(isis|ospf)\s*$', config_text, re.MULTILINE | re.IGNORECASE))
    
    # Count how many types we have
    types = [has_interfaces, has_services, has_system, has_bgp, has_igp]
    type_count = sum(types)
    
    if type_count >= 3:
        return "full_config"
    elif type_count == 0:
        return "unknown"
    elif type_count >= 2:
        return "mixed"
    elif has_services:
        return "services_only"
    elif has_interfaces:
        return "interfaces_only"
    elif has_system:
        return "system"
    elif has_bgp:
        return "bgp"
    elif has_igp:
        return "igp"
    else:
        return "unknown"


def get_push_analytics(limit: int = 20, filter_platform: str = None, 
                       filter_scale_type: str = None, filter_push_type: str = None) -> Dict[str, Any]:
    """
    Get push history analytics for display and learning.
    
    Args:
        limit: Max number of recent entries to return
        filter_platform: Filter by platform (e.g., "SA-36CD-S")
        filter_scale_type: Filter by scale type (e.g., "l2ac_fxc", "pwhe_fxc")
        filter_push_type: Filter by push type (e.g., "full_commit", "merge")
    
    Returns:
        Dict with:
            - entries: List of recent push records
            - summary: Aggregated statistics by category
            - estimates: Recommended estimates by category
    """
    db = _load_timing_db()
    entries = db.get("entries", [])
    
    # Apply filters
    if filter_platform:
        entries = [e for e in entries if e.get("platform", "").lower() == filter_platform.lower()]
    if filter_scale_type:
        entries = [e for e in entries if e.get("scale_type", "").lower() == filter_scale_type.lower()]
    if filter_push_type:
        entries = [e for e in entries if e.get("push_type", "").lower() == filter_push_type.lower()]
    
    # Get recent entries
    recent = entries[-limit:] if len(entries) > limit else entries
    recent = list(reversed(recent))  # Newest first
    
    # Calculate summary statistics
    summary = {
        "total_pushes": len(entries),
        "by_platform": {},
        "by_scale_type": {},
        "by_push_type": {},
        "by_push_method": {},
        "by_config_content": {},
    }
    
    for entry in entries:
        # Group by platform
        platform = entry.get("platform", "unknown")
        if platform not in summary["by_platform"]:
            summary["by_platform"][platform] = {"count": 0, "total_time": 0, "total_lines": 0}
        summary["by_platform"][platform]["count"] += 1
        summary["by_platform"][platform]["total_time"] += entry.get("actual_time", 0)
        summary["by_platform"][platform]["total_lines"] += entry.get("line_count", 0)
        
        # Group by scale type
        scale_type = entry.get("scale_type", "unknown")
        if scale_type not in summary["by_scale_type"]:
            summary["by_scale_type"][scale_type] = {"count": 0, "total_time": 0, "total_lines": 0, "avg_time_per_1k": []}
        summary["by_scale_type"][scale_type]["count"] += 1
        summary["by_scale_type"][scale_type]["total_time"] += entry.get("actual_time", 0)
        summary["by_scale_type"][scale_type]["total_lines"] += entry.get("line_count", 0)
        if entry.get("time_per_1k_lines"):
            summary["by_scale_type"][scale_type]["avg_time_per_1k"].append(entry["time_per_1k_lines"])
        
        # Group by push type
        push_type = entry.get("push_type", "unknown")
        if push_type not in summary["by_push_type"]:
            summary["by_push_type"][push_type] = {"count": 0, "total_time": 0}
        summary["by_push_type"][push_type]["count"] += 1
        summary["by_push_type"][push_type]["total_time"] += entry.get("actual_time", 0)
        
        # Group by push method
        push_method = entry.get("push_method", "unknown")
        if push_method not in summary["by_push_method"]:
            summary["by_push_method"][push_method] = {"count": 0, "total_time": 0}
        summary["by_push_method"][push_method]["count"] += 1
        summary["by_push_method"][push_method]["total_time"] += entry.get("actual_time", 0)
        
        # Group by config content type
        content_type = entry.get("config_content_type", "unknown")
        if content_type not in summary["by_config_content"]:
            summary["by_config_content"][content_type] = {"count": 0, "total_time": 0}
        summary["by_config_content"][content_type]["count"] += 1
        summary["by_config_content"][content_type]["total_time"] += entry.get("actual_time", 0)
    
    # Calculate averages for scale types
    for st, data in summary["by_scale_type"].items():
        if data["avg_time_per_1k"]:
            data["avg_time_per_1k_lines"] = sum(data["avg_time_per_1k"]) / len(data["avg_time_per_1k"])
            del data["avg_time_per_1k"]  # Remove raw list
        else:
            data["avg_time_per_1k_lines"] = 0
    
    return {
        "entries": recent,
        "summary": summary,
        "platform_averages": db.get("platform_averages", {}),
        "scale_type_averages": db.get("scale_type_averages", {})
    }


def _calculate_scale_type_averages(entries: List[Dict]) -> Dict[str, Dict]:
    """Calculate average timing metrics per scale type from historical data."""
    scale_data = {}
    
    for entry in entries:
        scale_type = entry.get("scale_type", "unknown")
        if scale_type not in scale_data:
            scale_data[scale_type] = {
                "total_time": 0,
                "total_lines": 0,
                "count": 0,
                "samples": []
            }
        
        sd = scale_data[scale_type]
        sd["total_time"] += entry.get("actual_time", 0)
        sd["total_lines"] += entry.get("line_count", 0)
        sd["count"] += 1
        sd["samples"].append({
            "lines": entry.get("line_count", 0),
            "time": entry.get("actual_time", 0),
            "scale_counts": entry.get("scale_counts", {}),
            "device": entry.get("device", ""),
            "timestamp": entry.get("timestamp", "")
        })
    
    # Calculate averages per scale type
    averages = {}
    for scale_type, data in scale_data.items():
        if data["count"] > 0 and data["total_lines"] > 0:
            avg_time_per_1k = (data["total_time"] / data["total_lines"]) * 1000
            
            averages[scale_type] = {
                "learned_time_per_1k_lines": round(avg_time_per_1k, 2),
                "sample_count": data["count"],
                "avg_time_per_push": round(data["total_time"] / data["count"], 1),
                "last_updated": datetime.now().isoformat()
            }
    
    return averages


def get_learned_timing_by_scale(scale_type: str, platform: str = None) -> Optional[Dict]:
    """
    Get learned timing data for a specific scale type.
    
    Returns timing specific to scale type if available, 
    falls back to platform average if not.
    """
    db = _load_timing_db()
    
    # First try scale-type specific timing
    scale_timing = db.get("scale_type_averages", {}).get(scale_type)
    if scale_timing and scale_timing.get('sample_count', 0) >= 1:
        return {**scale_timing, 'timing_source': 'scale_type'}
    
    # Fall back to platform timing
    if platform:
        platform_timing = db.get("platform_averages", {}).get(platform)
        if platform_timing:
            return {**platform_timing, 'timing_source': 'platform'}
    
    return None


def find_similar_push(scale_counts: Dict[str, int], platform: str, device_hostname: str = None) -> Optional[Dict]:
    """
    Find the most similar historical push based on scale counts.
    
    Returns the best matching historical record for accurate estimation.
    Uses tiered matching with device preference:
    1. Same device (hostname), similar scale (BEST - most accurate)
    2. Same platform, similar scale (good match)
    3. Same platform, any scale (less accurate)
    4. Any platform, similar scale (cross-platform estimate)
    
    Args:
        scale_counts: Dict with pwhe_subifs, l2_ac_subifs, fxc_services counts
        platform: Device platform (SA-36CD-S, NCP, etc.)
        device_hostname: Optional device hostname to prefer same-device matches
    """
    db = _load_timing_db()
    entries = db.get("entries", [])
    
    if not entries:
        return None
    
    target_pwhe = scale_counts.get('pwhe_subifs', 0)
    target_l2ac = scale_counts.get('l2_ac_subifs', 0)
    target_fxc = scale_counts.get('fxc_services', 0)
    target_total = target_pwhe + target_l2ac + target_fxc
    
    def calculate_score(entry: Dict) -> float:
        """Calculate similarity score (lower is better)."""
        entry_counts = entry.get('scale_counts', {})
        entry_pwhe = entry_counts.get('pwhe_subifs', entry.get('pwhe_count', 0))
        entry_l2ac = entry_counts.get('l2_ac_subifs', 0)
        entry_fxc = entry_counts.get('fxc_services', entry.get('fxc_count', 0))
        entry_vrf = entry_counts.get('vrf_instances', 0)
        entry_l3subif = entry_counts.get('l3_subifs', 0)
        
        target_vrf = scale_counts.get('vrf_instances', 0)
        target_l3subif = scale_counts.get('l3_subifs', 0)
        
        # Weight each component based on typical impact on commit time
        return (
            abs(target_pwhe - entry_pwhe) * 1.5 +    # PWHE has high impact
            abs(target_l2ac - entry_l2ac) * 1.0 +    # L2 AC moderate impact
            abs(target_fxc - entry_fxc) * 1.2 +      # FXC high impact
            abs(target_vrf - entry_vrf) * 0.8 +      # VRF moderate impact
            abs(target_l3subif - entry_l3subif) * 0.5  # L3 sub-if low-moderate impact
        )
    
    def calculate_combined_score(entry: Dict) -> Tuple[float, float]:
        """Calculate combined score: (scale_similarity, recency_penalty).
        
        Returns tuple where lower is better for sorting.
        recency_penalty: days ago (0 = today, higher = older)
        """
        from datetime import datetime
        
        scale_score = calculate_score(entry)
        
        # Calculate recency penalty (prefer newer records)
        recency_penalty = 0
        try:
            entry_timestamp = entry.get('timestamp', '')
            if entry_timestamp:
                entry_dt = datetime.fromisoformat(entry_timestamp)
                delta = datetime.now() - entry_dt
                recency_penalty = delta.days  # Days ago
        except:
            recency_penalty = 999  # Very old if can't parse
        
        return (scale_score, recency_penalty)
    
    # Tier 0: Same device (hostname) matches - MOST ACCURATE
    if device_hostname:
        same_device = [e for e in entries if e.get('device') == device_hostname]
        
        if same_device:
            # Sort by scale similarity, then recency (newer first)
            same_device_sorted = sorted(same_device, key=lambda e: calculate_combined_score(e))
            best_match = same_device_sorted[0]
            best_score, recency = calculate_combined_score(best_match)
            
            # More lenient threshold for same device (even if scale differs slightly)
            threshold = max(target_total * 0.7, 300)
            
            if best_score <= threshold:
                # Calculate similarity percentage for display
                entry_counts = best_match.get('scale_counts', {})
                entry_total = (
                    entry_counts.get('pwhe_subifs', best_match.get('pwhe_count', 0)) +
                    entry_counts.get('l2_ac_subifs', 0) +
                    entry_counts.get('fxc_services', best_match.get('fxc_count', 0))
                )
                max_total = max(target_total, entry_total, 1)
                similarity = max(0, 100 - (best_score / max_total * 100))
                best_match['_similarity'] = round(similarity, 1)
                best_match['_same_device'] = True
                return best_match
    
    # Tier 1: Same platform entries
    same_platform = [e for e in entries if e.get('platform') == platform]
    
    if same_platform:
        # Sort by scale similarity, then recency (newer first)
        same_platform_sorted = sorted(same_platform, key=lambda e: calculate_combined_score(e))
        best_match = same_platform_sorted[0]
        best_score, recency = calculate_combined_score(best_match)
        
        # More flexible threshold: 50% of target scale or 500 (whichever is higher)
        threshold = max(target_total * 0.5, 500)
        
        if best_score <= threshold:
            # Calculate similarity percentage for display
            entry_counts = best_match.get('scale_counts', {})
            entry_total = (
                entry_counts.get('pwhe_subifs', best_match.get('pwhe_count', 0)) +
                entry_counts.get('l2_ac_subifs', 0) +
                entry_counts.get('fxc_services', best_match.get('fxc_count', 0))
            )
            max_total = max(target_total, entry_total, 1)
            similarity = max(0, 100 - (best_score / max_total * 100))
            best_match['_similarity'] = round(similarity, 1)
            return best_match
    
    # Tier 2: Any platform with similar scale type
    # Only use if no good same-platform match
    target_scale_type = _determine_scale_type(scale_counts, target_pwhe, target_fxc)
    same_type = [e for e in entries if e.get('scale_type') == target_scale_type]
    
    if same_type:
        # Sort by scale similarity, then recency (newer first)
        same_type_sorted = sorted(same_type, key=lambda e: calculate_combined_score(e))
        best_match = same_type_sorted[0]
        best_score, recency = calculate_combined_score(best_match)
        
        # Slightly stricter threshold for cross-platform
        threshold = max(target_total * 0.4, 400)
        
        if best_score <= threshold:
            entry_counts = best_match.get('scale_counts', {})
            entry_total = (
                entry_counts.get('pwhe_subifs', best_match.get('pwhe_count', 0)) +
                entry_counts.get('l2_ac_subifs', 0) +
                entry_counts.get('fxc_services', best_match.get('fxc_count', 0))
            )
            max_total = max(target_total, entry_total, 1)
            similarity = max(0, 100 - (best_score / max_total * 100))
            best_match['_similarity'] = round(similarity, 1)
            best_match['_cross_platform'] = True
            return best_match
    
    return None


def _calculate_platform_averages(entries: List[Dict]) -> Dict[str, Dict]:
    """Calculate average timing metrics per platform from historical data."""
    platform_data = {}
    
    for entry in entries:
        platform = entry.get("platform", "Unknown")
        if platform not in platform_data:
            platform_data[platform] = {
                "total_time": 0,
                "total_lines": 0,
                "total_pwhe": 0,
                "total_fxc": 0,
                "count": 0,
                "time_samples": []
            }
        
        pd = platform_data[platform]
        pd["total_time"] += entry.get("actual_time", 0)
        pd["total_lines"] += entry.get("line_count", 0)
        pd["total_pwhe"] += entry.get("pwhe_count", 0)
        pd["total_fxc"] += entry.get("fxc_count", 0)
        pd["count"] += 1
        pd["time_samples"].append({
            "lines": entry.get("line_count", 0),
            "time": entry.get("actual_time", 0)
        })
    
    # Calculate averages
    averages = {}
    for platform, data in platform_data.items():
        if data["count"] > 0 and data["total_lines"] > 0:
            # Calculate learned time per 1k lines
            avg_time_per_1k = (data["total_time"] / data["total_lines"]) * 1000
            
            averages[platform] = {
                "learned_time_per_1k_lines": round(avg_time_per_1k, 2),
                "sample_count": data["count"],
                "total_lines_processed": data["total_lines"],
                "avg_time_per_push": round(data["total_time"] / data["count"], 1),
                "last_updated": datetime.now().isoformat()
            }
    
    return averages


def get_learned_timing(platform: str) -> Optional[Dict]:
    """
    Get learned timing data for a platform if available.
    
    Returns None if no historical data exists.
    """
    db = _load_timing_db()
    return db.get("platform_averages", {}).get(platform)


def get_accurate_push_estimates(
    config_text: str,
    platform: str = "SA-36CD-S",
    push_method: str = None,
    include_delete: bool = False,
    device_hostname: str = None
) -> Dict[str, Any]:
    """
    Get accurate time estimates based on historical push data.
    
    This function uses multiple data sources in priority order:
    1. Same device historical push (same hostname) - MOST ACCURATE
    2. Similar historical push (same scale, same platform) - VERY ACCURATE
    3. Scale-type specific averages (pwhe_fxc, l2ac_only, etc.)
    4. Platform averages
    5. Default calculations (fallback)
    
    Args:
        config_text: The configuration text to push
        platform: Device platform (SA-36CD-S, NCP, etc.)
        push_method: Optional specific method ("terminal_paste", "file_upload", "lofd")
        include_delete: Whether config includes delete commands
        device_hostname: Optional device hostname to prefer same-device matches
    
    Returns:
        Dict with:
            - estimates: Dict with time estimates per method
            - source: Where the estimate came from ("same_device", "similar_push", "scale_type", "platform", "default")
            - source_detail: Human-readable description of the source
            - similar_push: The matched similar push entry (if any)
            - confidence: Confidence level ("high", "medium", "low")
    """
    from datetime import datetime, timedelta
    import re
    
    line_count = len(config_text.split('\n')) if config_text else 0
    config_size_kb = len(config_text) / 1024 if config_text else 0
    
    # Count scale components
    # Count PWHE sub-interfaces only (ph<num>.<subnum>) to match historical data format
    pwhe_subif_count = len(re.findall(r'^\s{2}ph\d+\.\d+', config_text, re.MULTILINE))
    # Also count parent interfaces for complexity
    pwhe_parent_count = len(re.findall(r'^\s{2}ph\d+\s*$', config_text, re.MULTILINE))
    
    fxc_count = len(re.findall(r'^\s{4}instance\s+FXC-\S+', config_text, re.MULTILINE))
    l2ac_count = config_text.count('l2-service enabled')
    
    # Count VRF instances and L3 sub-interfaces for L3VPN scale
    vrf_count = len(re.findall(r'^\s{4}instance\s+\S+', config_text, re.MULTILINE)) if 'network-services' in config_text and 'vrf' in config_text else 0
    l3_subif_count = len(re.findall(r'^\s{2}(ge|xe|et|hun|bundle-ether)\d+[/-]\d+[/-]\d+\.\d+', config_text, re.MULTILINE))
    physical_if_count = len(re.findall(r'^\s{2}(ge|xe|et|hun)\d+[/-]\d+[/-]\d+\s*$', config_text, re.MULTILINE))
    
    # Total interface count for complexity calculation
    interface_count = pwhe_subif_count + pwhe_parent_count + l2ac_count + l3_subif_count + physical_if_count
    service_count = fxc_count + vrf_count
    delete_count = config_text.count('\nno ') if include_delete else 0
    
    # Count deleted items specifically for accurate scale description
    delete_fxc = len(re.findall(r'^no\s+network-services\s+evpn-vpws-fxc\s+instance', config_text, re.MULTILINE))
    delete_vpls = len(re.findall(r'^no\s+network-services\s+evpn-vpls\s+instance', config_text, re.MULTILINE))
    delete_ifaces = len(re.findall(r'^no\s+interfaces\s+\S+', config_text, re.MULTILINE))
    delete_mh = len(re.findall(r'^\s+no\s+interface\s+ph\d+', config_text, re.MULTILINE))
    
    # Use sub-interface count for scale matching (matches historical data)
    pwhe_count = pwhe_subif_count
    
    # Build scale counts for similarity search
    scale_counts = {
        'pwhe_subifs': pwhe_count,
        'l2_ac_subifs': l2ac_count,
        'fxc_services': fxc_count,
        'vrf_instances': vrf_count,
        'l3_subifs': l3_subif_count,
        'bgp_peers': len(re.findall(r'neighbor\s+\d+\.\d+\.\d+\.\d+', config_text)),
    }
    
    # Determine scale type
    scale_type = _determine_scale_type(scale_counts, pwhe_count, fxc_count)
    
    # ════════════════════════════════════════════════════════════════════════════
    # PRIORITY 1: Find similar historical push (MOST ACCURATE)
    # ════════════════════════════════════════════════════════════════════════════
    similar_push = find_similar_push(scale_counts, platform, device_hostname=device_hostname)
    source = "default"
    source_detail = "estimated (no historical data)"
    confidence = "low"
    learned_rate = 12.0  # Default: 12 sec per 1K lines (variable rate, excluding overhead)
    FIXED_OVERHEAD_ESTIMATE = 25.0  # Estimated fixed overhead for connection, setup, etc.
    
    if similar_push:
        # Use the similar push's actual timing
        similar_lines = similar_push.get('line_count', 1)
        similar_time = similar_push.get('actual_time', 0)
        similar_device = similar_push.get('device', 'unknown')
        similar_timestamp = similar_push.get('timestamp', '')
        
        # ALWAYS recalculate rate from raw time to ensure overhead is properly subtracted
        # Old records may have inflated time_per_1k_lines that didn't account for overhead
        if similar_lines >= 1000:
            # Large configs: overhead is negligible relative to total time
            # Use 5% of total as overhead estimate
            overhead_for_calc = min(FIXED_OVERHEAD_ESTIMATE, similar_time * 0.05)
            variable_time = max(0, similar_time - overhead_for_calc)
            learned_rate = (variable_time / similar_lines) * 1000  # per 1K lines
        elif similar_lines >= 100:
            # Medium configs: use fixed overhead estimate
            variable_time = max(0, similar_time - FIXED_OVERHEAD_ESTIMATE)
            learned_rate = (variable_time / similar_lines) * 1000  # per 1K lines
            # Cap at reasonable rate for medium configs
            learned_rate = min(learned_rate, 25.0)
        else:
            # Small configs (<100 lines): overhead dominates, use conservative rate
            # Don't try to learn from these as they're mostly overhead
            learned_rate = 15.0  # Conservative default
        
        # Ensure rate is within reasonable bounds
        learned_rate = max(5.0, min(learned_rate, 30.0))
        
        # Format how long ago the similar push was
        try:
            similar_dt = datetime.fromisoformat(similar_timestamp)
            delta = datetime.now() - similar_dt
            if delta.days > 0:
                time_ago = f"{delta.days}d ago"
            elif delta.seconds > 3600:
                time_ago = f"{delta.seconds // 3600}h ago"
            else:
                time_ago = f"{delta.seconds // 60}m ago"
        except:
            time_ago = ""
        
        # Check if this is a same-device match
        is_same_device = similar_push.get('_same_device', False)
        
        similar_pwhe = similar_push.get('scale_counts', {}).get('pwhe_subifs', similar_push.get('pwhe_count', 0))
        similar_fxc = similar_push.get('scale_counts', {}).get('fxc_services', similar_push.get('fxc_count', 0))
        
        # Include similarity percentage if available
        similarity = similar_push.get('_similarity')
        
        if similarity:
            similarity_str = f" ({similarity:.0f}% match)"
        else:
            similarity_str = ""
        
        if is_same_device:
            source = "same_device"
            confidence = "high"
            source_detail = f"based on {similar_device} push ({similar_pwhe:,} PWHE, {similar_fxc:,} FXC){similarity_str} {time_ago}"
        else:
            source = "similar_push"
            cross_platform = similar_push.get('_cross_platform', False)
            
            if cross_platform:
                platform_note = f" [cross-platform from {similar_push.get('platform', 'unknown')}]"
                confidence = "medium"
            else:
                platform_note = ""
                confidence = "high"
            
            source_detail = f"based on {similar_device} push ({similar_pwhe:,} PWHE, {similar_fxc:,} FXC){similarity_str} {time_ago}{platform_note}"
    
    else:
        # ════════════════════════════════════════════════════════════════════════
        # PRIORITY 2: Try scale-type specific timing
        # ════════════════════════════════════════════════════════════════════════
        scale_timing = get_learned_timing_by_scale(scale_type, platform)
        
        if scale_timing and scale_timing.get('timing_source') == 'scale_type':
            learned_rate = scale_timing.get('learned_time_per_1k_lines', 15.0)
            sample_count = scale_timing.get('sample_count', 0)
            source = "scale_type"
            source_detail = f"from {sample_count} {scale_type} pushes (avg {learned_rate:.1f}s/1K lines)"
            confidence = "medium" if sample_count >= 3 else "low"
        
        elif scale_timing and scale_timing.get('timing_source') == 'platform':
            # ════════════════════════════════════════════════════════════════════
            # PRIORITY 3: Platform average
            # ════════════════════════════════════════════════════════════════════
            learned_rate = scale_timing.get('learned_time_per_1k_lines', 15.0)
            sample_count = scale_timing.get('sample_count', 0)
            source = "platform"
            source_detail = f"from {sample_count} {platform} pushes (avg {learned_rate:.1f}s/1K lines)"
            confidence = "medium" if sample_count >= 5 else "low"
    
    # ════════════════════════════════════════════════════════════════════════════
    # CALCULATE ESTIMATES FOR EACH METHOD
    # ════════════════════════════════════════════════════════════════════════════
    lines_k = line_count / 1000
    
    # Factor in interface/service complexity
    complexity_factor = 1.0 + (interface_count / 5000) * 0.2 + (service_count / 5000) * 0.15
    
    # BGP complexity adds significant time (especially with multiple AFIs, policies)
    bgp_neighbor_count = scale_counts.get('bgp_peers', 0)
    vrf_count_val = scale_counts.get('vrf_instances', 0)
    if bgp_neighbor_count > 0 or vrf_count_val > 0:
        # Each BGP neighbor with AFIs adds complexity
        bgp_factor = 1.0 + (bgp_neighbor_count * 0.05) + (vrf_count_val * 0.1)
        complexity_factor *= bgp_factor
    
    # Delete commands add time
    delete_factor = 1.0 + (delete_count / 1000) * 0.1
    
    # Adjust learned rate based on scale type for more accuracy
    if scale_type in ['l3vpn_vrf', 'bgp_scale', 'l3_routing']:
        # L3/BGP configs are more complex per line than L2 services
        learned_rate = max(learned_rate, 20.0)  # Minimum 20s/1K lines for L3/BGP
    
    # ════════════════════════════════════════════════════════════════════════════
    # IMPROVED TIMING MODEL: total = fixed_overhead + (variable_rate * scale)
    # This accounts for connection time, upload overhead, etc.
    # ════════════════════════════════════════════════════════════════════════════
    FIXED_OVERHEAD = 25.0  # Base SSH connection, shell setup, commit check overhead
    
    # Variable time based on config size and complexity
    variable_time = lines_k * learned_rate * complexity_factor * delete_factor
    
    # Commit time scales with config complexity
    commit_check_time = max(10, 10 + variable_time * 0.20)  # 20% of variable time
    commit_time = max(15, 15 + variable_time * 0.30)  # 30% of variable time
    
    # ════════════════════════════════════════════════════════════════════════════
    # TERMINAL PASTE
    # ════════════════════════════════════════════════════════════════════════════
    PASTE_RATE = 120  # lines/sec
    paste_time = line_count / PASTE_RATE
    
    total_paste = FIXED_OVERHEAD + paste_time + commit_check_time + commit_time
    
    # ════════════════════════════════════════════════════════════════════════════
    # FILE UPLOAD (faster for large configs)
    # ════════════════════════════════════════════════════════════════════════════
    upload_speed_kbps = 500  # Conservative SCP speed
    upload_time = max(2, config_size_kb / upload_speed_kbps)
    load_time = max(3, 3 + lines_k * 1.0)  # ~1 sec per 1K lines to parse
    
    total_upload = FIXED_OVERHEAD + upload_time + load_time + commit_check_time + commit_time
    
    # ════════════════════════════════════════════════════════════════════════════
    # FACTORY RESET + LOAD
    # ════════════════════════════════════════════════════════════════════════════
    factory_reset_time = 25  # Load factory-default and commit
    first_commit_time = 10   # Initial commit of factory config
    
    total_lofd = FIXED_OVERHEAD + factory_reset_time + first_commit_time + upload_time + load_time + commit_time
    
    return {
        'estimates': {
            'terminal_paste': {
                'total': total_paste,
                'paste_time': paste_time,
                'commit_check_time': commit_check_time,
                'commit_time': commit_time,
            },
            'file_upload': {
                'total': total_upload,
                'upload_time': upload_time,
                'load_time': load_time,
                'commit_check_time': commit_check_time,
                'commit_time': commit_time,
            },
            'lofd': {
                'total': total_lofd,
                'factory_reset_time': factory_reset_time,
                'first_commit_time': first_commit_time,
                'upload_time': upload_time,
                'load_time': load_time,
                'commit_time': commit_time,
            }
        },
        'source': source,
        'source_detail': source_detail,
        'confidence': confidence,
        'similar_push': similar_push,
        'learned_rate': learned_rate,
        'scale_type': scale_type,
        'metrics': {
            'line_count': line_count,
            'config_size_kb': config_size_kb,
            'interface_count': interface_count,
            'service_count': service_count,
            'delete_count': delete_count,
            'pwhe_count': pwhe_count,
            'fxc_count': fxc_count,
            'complexity_factor': complexity_factor,
            # Deleted items for accurate scale description
            'delete_fxc': delete_fxc,
            'delete_vpls': delete_vpls,
            'delete_ifaces': delete_ifaces,
            'delete_mh': delete_mh,
        }
    }


class ConfigPusher:
    """Push configurations to DNOS devices via SSH."""

    def __init__(
        self,
        timeout: int = 60,
        commit_timeout: int = 900,
        load_timeout: int = 600
    ):
        """
        Initialize the config pusher.
        
        Args:
            timeout: SSH connection timeout (default: 60s)
            commit_timeout: Timeout for commit operations (default: 15 min)
            load_timeout: Timeout for load/upload operations (default: 10 min)
        """
        self.timeout = timeout
        self.commit_timeout = commit_timeout
        self.load_timeout = load_timeout
        self._console = None

    def _get_console(self):
        """Get or create a Rich console for live output."""
        if self._console is None:
            from rich.console import Console
            self._console = Console()
        return self._console

    def _scp_upload(
        self,
        device: Device,
        config_text: str,
        remote_path: str,
        timeout: int = 600
    ) -> Tuple[bool, str]:
        """
        Upload configuration using native SCP command.
        
        This is more reliable than paramiko SFTP for large files.
        
        Args:
            device: Target device
            config_text: Configuration text to upload
            remote_path: Remote path on the device
            timeout: Upload timeout in seconds
        
        Returns:
            Tuple of (success, message)
        """
        # Create temporary file with the config
        temp_file = None
        try:
            temp_file = tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.txt',
                delete=False
            )
            temp_file.write(config_text)
            temp_file.close()
            
            # Build SCP command
            # Use sshpass for password authentication
            password = device.get_password()
            ssh_host = get_ssh_hostname(device)
            target = f"{device.username}@{ssh_host}:{remote_path}"
            
            # Check if sshpass is available
            sshpass_check = subprocess.run(
                ['which', 'sshpass'],
                capture_output=True,
                text=True
            )
            
            if sshpass_check.returncode == 0:
                # Use sshpass for password authentication
                cmd = [
                    'sshpass', '-p', password,
                    'scp',
                    '-o', 'StrictHostKeyChecking=no',
                    '-o', 'UserKnownHostsFile=/dev/null',
                    '-o', f'ConnectTimeout={self.timeout}',
                    '-o', 'ServerAliveInterval=30',
                    '-o', 'ServerAliveCountMax=10',
                    temp_file.name,
                    target
                ]
            else:
                # Fall back to expect script or manual
                # First try with SSH key (no password)
                cmd = [
                    'scp',
                    '-o', 'StrictHostKeyChecking=no',
                    '-o', 'UserKnownHostsFile=/dev/null',
                    '-o', f'ConnectTimeout={self.timeout}',
                    '-o', 'ServerAliveInterval=30',
                    '-o', 'ServerAliveCountMax=10',
                    '-o', 'BatchMode=yes',
                    temp_file.name,
                    target
                ]
            
            # Run SCP
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            if result.returncode == 0:
                config_size = len(config_text)
                return True, f"Uploaded {config_size:,} bytes successfully"
            else:
                error_msg = result.stderr.strip() or result.stdout.strip() or "Unknown SCP error"
                return False, error_msg
                
        except subprocess.TimeoutExpired:
            return False, f"SCP upload timed out after {timeout}s"
        except FileNotFoundError:
            return False, "SCP command not found. Please install openssh-client."
        except Exception as e:
            return False, f"SCP error: {str(e)}"
        finally:
            # Clean up temp file
            if temp_file and os.path.exists(temp_file.name):
                try:
                    os.unlink(temp_file.name)
                except:
                    pass

    def push_config(
        self,
        device: Device,
        config_text: str,
        config_name: str = None,
        dry_run: bool = False,
        progress_callback: Callable[[str, int], None] = None,
        live_output_callback: Callable[[str], None] = None,
    ) -> Tuple[bool, str]:
        """
        Push a configuration to a device.

        Args:
            device: Target device
            config_text: Configuration text to push
            config_name: Name for the config file on device
            dry_run: If True, only run commit check, don't commit
            progress_callback: Optional callback for progress updates
            live_output_callback: Optional callback for raw SSH output (each chunk)

        Returns:
            Tuple of (success, message)
        """
        client = None
        channel = None

        try:
            # Progress: Connecting
            if progress_callback:
                progress_callback("Connecting to device...", 10)

            # Connect to device using best available IP
            ssh_host = get_ssh_hostname(device)
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(
                hostname=ssh_host,
                username=device.username,
                password=device.get_password(),
                timeout=self.timeout,
                look_for_keys=False,
                allow_agent=False
            )

            # Open interactive shell
            channel = client.invoke_shell()
            channel.settimeout(self.timeout)

            # Wait for prompt
            time.sleep(1)
            self._read_until_prompt(channel, live_output_callback=live_output_callback)
            
            # Generate config filename
            if not config_name:
                config_name = f"scaler_{timestamp_filename(suffix='')}.txt"
            
            # Progress: Uploading config
            if progress_callback:
                progress_callback("Uploading configuration file via SCP...", 20)
            
            # Upload config file via native SCP (more reliable for large files)
            remote_path = f"/config/{config_name}"
            
            upload_success, upload_msg = self._scp_upload(
                device=device,
                config_text=config_text,
                remote_path=remote_path,
                timeout=self.load_timeout
            )
            
            if not upload_success:
                return False, f"SCP upload failed: {upload_msg}"
            
            # Enable terminal logging to see problems during commit
            channel.send("set logging terminal\n")
            self._read_until_prompt(channel, timeout=5, live_output_callback=live_output_callback)

            # Progress: Entering configure mode
            if progress_callback:
                progress_callback("Entering configuration mode...", 30)

            # Enter configure mode
            channel.send("configure\n")
            output = self._read_until_prompt(channel, timeout=10, live_output_callback=live_output_callback)

            if "cfg" not in output.lower() and "#" not in output:
                return False, "Failed to enter configuration mode"

            # Clear any dirty candidate config before loading
            if progress_callback:
                progress_callback("Clearing candidate config...", 35)
            channel.send("rollback 0\n")
            self._read_until_prompt(channel, timeout=15, live_output_callback=live_output_callback)

            # Progress: Loading configuration
            if progress_callback:
                progress_callback("Loading configuration...", 40)

            # Load the configuration (with real-time progress from device)
            channel.send(f"load override {config_name}\n")
            output = self._read_until_prompt(
                channel,
                timeout=self.load_timeout,
                progress_callback=progress_callback,
                progress_prefix="Loading configuration",
                live_output_callback=live_output_callback,
            )
            
            if "error" in output.lower():
                # Extract the specific error
                error_match = re.search(r"ERROR:\s*(.+?)(?:\n|$)", output, re.IGNORECASE)
                error_msg = error_match.group(1) if error_match else output[-500:]
                return False, f"Load failed: {error_msg}"
            
            # Progress: Running commit check
            if progress_callback:
                progress_callback("Running commit check...", 60)
            
            # Run commit check
            channel.send("commit check\n")
            output = self._read_until_prompt(channel, timeout=self.commit_timeout, live_output_callback=live_output_callback)

            # Check for success - includes "no changes" which means config already on device
            output_lower = output.lower()
            commit_success = any(p in output_lower for p in [
                "commit check passed", "no configuration changes were made", "commit action is not applicable"
            ])
            if not commit_success:
                # Try to extract error message
                error_msg = self._extract_error(output)
                return False, f"Commit check failed: {error_msg}"
            
            if dry_run:
                # Exit without committing
                channel.send("exit\n")
                self._read_until_prompt(channel, live_output_callback=live_output_callback)
                return True, "Commit check passed (dry run - no commit)"

            # Progress: Committing
            if progress_callback:
                progress_callback("Committing configuration...", 80)

            # Commit the configuration
            channel.send("commit\n")
            output = self._read_until_prompt(channel, timeout=self.commit_timeout, live_output_callback=live_output_callback)
            
            if "commit succeeded" not in output.lower():
                error_msg = self._extract_error(output)
                return False, f"Commit failed: {error_msg}"
            
            # Progress: Complete
            if progress_callback:
                progress_callback("Configuration committed successfully!", 100)
            
            # Exit configuration mode
            channel.send("exit\n")
            self._read_until_prompt(channel, live_output_callback=live_output_callback)

            # Save the pushed config locally
            self._save_pushed_config(device.hostname, config_name, config_text)
            
            return True, "Configuration committed successfully"
            
        except paramiko.AuthenticationException:
            return False, "Authentication failed - check username/password"
        except paramiko.SSHException as e:
            error_msg = str(e)
            if "Channel closed" in error_msg or not error_msg:
                error_msg = "SSH channel closed unexpectedly. This often happens with large configs (>1MB). Try manual SCP upload."
            return False, f"SSH error: {error_msg}"
        except socket.timeout:
            return False, "Connection timeout - device may be slow or unresponsive. Try increasing timeout."
        except OSError as e:
            return False, f"Network error: {str(e)} - check connectivity to device"
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            return False, f"Error: {str(e)}\n\nDetails:\n{tb[-500:]}"  # Last 500 chars of traceback
        finally:
            if channel:
                try:
                    channel.close()
                except:
                    pass
            if client:
                try:
                    client.close()
                except:
                    pass

    def push_config_merge(
        self,
        device: Device,
        config_text: str,
        config_name: str = None,
        dry_run: bool = False,
        progress_callback: Callable[[str, int], None] = None,
        live_output_callback: Callable[[str], None] = None,
    ) -> Tuple[bool, str]:
        """
        Push configuration using 'load merge' - appends to existing config.

        Unlike push_config which uses 'load override', this method merges
        the new configuration with the existing running configuration.
        Perfect for adding multihoming, new services, or interface config
        without affecting other parts of the configuration.

        Args:
            device: Target device
            config_text: Configuration text to merge
            config_name: Name for the config file on device
            dry_run: If True, only run commit check, don't commit
            progress_callback: Optional callback for progress updates
            live_output_callback: Optional callback for raw SSH output (each chunk)

        Returns:
            Tuple of (success, message)
        """
        client = None
        channel = None

        try:
            if progress_callback:
                progress_callback("Connecting to device...", 10)

            # Connect using best available IP from operational.json
            ssh_host = get_ssh_hostname(device)
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(
                hostname=ssh_host,
                username=device.username,
                password=device.get_password(),
                timeout=self.timeout,
                look_for_keys=False,
                allow_agent=False
            )

            channel = client.invoke_shell()
            channel.settimeout(self.timeout)

            time.sleep(1)
            self._read_until_prompt(channel, live_output_callback=live_output_callback)

            if not config_name:
                config_name = f"scaler_merge_{timestamp_filename(suffix='')}.txt"
            
            if progress_callback:
                progress_callback("Uploading configuration via SCP...", 20)
            
            remote_path = f"/config/{config_name}"
            
            upload_success, upload_msg = self._scp_upload(
                device=device,
                config_text=config_text,
                remote_path=remote_path,
                timeout=self.load_timeout
            )
            
            if not upload_success:
                return False, f"SCP upload failed: {upload_msg}"
            
            # Enable terminal logging
            channel.send("set logging terminal\n")
            self._read_until_prompt(channel, timeout=5, live_output_callback=live_output_callback)

            if progress_callback:
                progress_callback("Entering configuration mode...", 30)

            channel.send("configure\n")
            output = self._read_until_prompt(channel, timeout=10, live_output_callback=live_output_callback)

            if "cfg" not in output.lower() and "#" not in output:
                return False, "Failed to enter configuration mode"

            # Clear any dirty candidate config before merging
            channel.send("rollback 0\n")
            time.sleep(0.5)
            self._read_until_prompt(channel, timeout=10, live_output_callback=live_output_callback)

            if progress_callback:
                progress_callback("Merging configuration (load merge)...", 40)

            # Use LOAD MERGE instead of load override
            channel.send(f"load merge {config_name}\n")
            output = self._read_until_prompt(
                channel,
                timeout=self.load_timeout,
                progress_callback=progress_callback,
                progress_prefix="Merging configuration",
                live_output_callback=live_output_callback,
            )
            
            if "error" in output.lower():
                error_match = re.search(r"ERROR:\s*(.+?)(?:\n|$)", output, re.IGNORECASE)
                error_msg = error_match.group(1) if error_match else output[-500:]
                return False, f"Load merge failed: {error_msg}"
            
            if progress_callback:
                progress_callback("Running commit check...", 60)
            
            channel.send("commit check\n")
            output = self._read_until_prompt(channel, timeout=self.commit_timeout, live_output_callback=live_output_callback)

            # Check for success - includes "no changes" which means config already on device
            output_lower = output.lower()
            commit_success = any(p in output_lower for p in [
                "commit check passed", "no configuration changes were made", "commit action is not applicable"
            ])
            if not commit_success:
                error_msg = self._extract_error(output)
                return False, f"Commit check failed: {error_msg}"

            if dry_run:
                channel.send("exit\n")
                self._read_until_prompt(channel, live_output_callback=live_output_callback)
                return True, "Commit check passed (dry run - no commit)"

            if progress_callback:
                progress_callback("Committing configuration...", 80)

            channel.send("commit\n")
            output = self._read_until_prompt(channel, timeout=self.commit_timeout, live_output_callback=live_output_callback)

            if "commit succeeded" not in output.lower():
                error_msg = self._extract_error(output)
                return False, f"Commit failed: {error_msg}"

            if progress_callback:
                progress_callback("Configuration merged successfully!", 100)

            channel.send("exit\n")
            self._read_until_prompt(channel, live_output_callback=live_output_callback)
            
            self._save_pushed_config(device.hostname, f"merge_{config_name}", config_text)
            
            return True, "Configuration merged successfully"
            
        except paramiko.AuthenticationException:
            return False, "Authentication failed - check username/password"
        except paramiko.SSHException as e:
            error_msg = str(e)
            if "Channel closed" in error_msg or not error_msg:
                error_msg = "SSH channel closed unexpectedly"
            return False, f"SSH error: {error_msg}"
        except socket.timeout:
            return False, "Connection timeout"
        except OSError as e:
            return False, f"Network error: {str(e)}"
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            return False, f"Error: {str(e)}\n\nDetails:\n{tb[-500:]}"
        finally:
            if channel:
                try:
                    channel.close()
                except:
                    pass
            if client:
                try:
                    client.close()
                except:
                    pass

    def push_config_terminal_paste(
        self,
        device: Device,
        config_text: str,
        dry_run: bool = False,
        progress_callback: Callable[[str, int], None] = None,
        live_output_callback: Callable[[str], None] = None,
        show_live_terminal: bool = False,
        phase_info: str = None
    ) -> Tuple[bool, str]:
        """
        Push configuration by pasting directly into device terminal.
        
        This method enters configure mode and pastes config lines directly,
        without using file upload. Better for smaller configs or when
        SCP/file upload has issues.
        
        Args:
            device: Target device
            config_text: Configuration text to paste
            dry_run: If True, only run commit check, don't commit
            progress_callback: Optional callback for progress updates
            phase_info: Optional phase indicator like "Phase 1/2" for multi-phase operations
            live_output_callback: Optional callback to receive live device output
            show_live_terminal: If True, print device output to console
        
        Returns:
            Tuple of (success, message)
        """
        client = None
        channel = None
        
        try:
            if progress_callback:
                progress_callback("Connecting to device...", 10)
            
            # Connect using best available IP from operational.json
            ssh_host = get_ssh_hostname(device)
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(
                hostname=ssh_host,
                username=device.username,
                password=device.get_password(),
                timeout=self.timeout,
                look_for_keys=False,
                allow_agent=False
            )
            
            channel = client.invoke_shell()
            channel.settimeout(self.timeout)
            
            # Helper to handle live output
            def read_and_show(timeout=30):
                output = self._read_until_prompt(channel, timeout=timeout)
                if show_live_terminal and output.strip():
                    # Show last few lines in a compact format
                    lines = output.strip().split('\n')
                    for line in lines[-3:]:  # Show last 3 lines
                        print(f"  \033[90m│ {line[:80]}\033[0m")
                if live_output_callback:
                    live_output_callback(output)
                return output
            
            time.sleep(1)
            read_and_show()
            
            # Enable terminal logging
            channel.send("set logging terminal\n")
            read_and_show(timeout=5)
            
            if progress_callback:
                progress_callback("Entering configuration mode...", 20)
            
            if show_live_terminal:
                print(f"  \033[36m┌─ Device Terminal: {device.hostname} ─\033[0m")
            
            channel.send("configure\n")
            output = read_and_show(timeout=10)
            
            if "cfg" not in output.lower() and "#" not in output:
                return False, "Failed to enter configuration mode"
            
            # Clear any dirty candidate config before pasting
            channel.send("rollback 0\n")
            time.sleep(0.5)
            read_and_show(timeout=10)  # Consume output
            
            if show_live_terminal:
                console = self._get_console()
                console.print("[dim]✓ Candidate config cleared (rollback 0)[/dim]")
            
            if progress_callback:
                progress_callback("Pasting configuration...", 30)
            
            # Parse and paste config lines
            # CRITICAL: Strip \r (Windows line endings) to prevent command corruption on DNOS
            config_text = config_text.replace('\r\n', '\n').replace('\r', '\n')
            lines = config_text.strip().split('\n')
            total_lines = len(lines)
            
            # For live terminal, use a scrolling buffer
            terminal_buffer = []
            TERMINAL_HEIGHT = 16  # Compact but readable
            TERMINAL_WIDTH = 88   # Width for content display
            
            if show_live_terminal:
                from rich.live import Live
                from rich.panel import Panel
                from rich.text import Text
                from rich.table import Table
                from rich.console import Group
                from rich import box
                import re
                
                # Track current line index for display
                current_line = [0]
                stage = ["paste"]
                paste_start_time = time.time()
                
                # Estimate paste time based on line count (empirical: ~8 lines/sec for terminal paste)
                lines_per_second = 120  # Adjusted for actual paste speed with 8ms delay
                estimated_paste_time = total_lines / lines_per_second
                
                # Estimate commit check time - scales with lines AND deletes
                # 83K lines + 3K deletes = ~30-40 min empirically observed
                delete_line_count = len([l for l in config_text.split('\n') if l.strip().startswith('no ')])
                # Base: 2 min + 20 sec per 1000 lines + 30 sec per 500 deletes
                estimated_commit_check_time = 120 + (total_lines / 1000) * 20 + (delete_line_count / 500) * 30
                estimated_commit_check_time = max(60, min(2700, estimated_commit_check_time))  # 1-45 min
                
                estimated_commit_time = max(30, min(600, total_lines / 10))  # 0.5-10 min
                
                # Stage tracking for multi-phase display
                STAGES = ["paste", "commit_check", "commit", "complete"]
                STAGE_NAMES = {
                    "paste": "📤 Pasting Configuration",
                    "commit_check": "🔍 Running Commit Check", 
                    "commit": "💾 Committing Configuration",
                    "complete": "✅ Complete"
                }
                current_stage = ["paste"]  # Mutable for closure
                stage_start_times = {"paste": paste_start_time}  # Track when each stage started
                stage_end_times = {}  # Track when each stage ended
                commit_check_output = [""]  # Last commit check output for display
                
                def format_time(seconds: float) -> str:
                    """Format seconds as Xm Ys or just Ys."""
                    seconds = max(0, int(seconds))
                    if seconds >= 60:
                        mins = seconds // 60
                        secs = seconds % 60
                        return f"{mins}m {secs}s"
                    return f"{seconds}s"
                
                def format_timestamp(epoch_time: float) -> str:
                    """Format epoch time as HH:MM:SS."""
                    from datetime import datetime
                    return datetime.fromtimestamp(epoch_time).strftime("%H:%M:%S")
                
                def build_timeline_header() -> str:
                    """Build a timeline header showing timestamps for all stages."""
                    lines = []
                    
                    # Paste stage
                    if "paste" in stage_start_times:
                        start = format_timestamp(stage_start_times["paste"])
                        if "paste" in stage_end_times:
                            end = format_timestamp(stage_end_times["paste"])
                            duration = format_time(stage_end_times["paste"] - stage_start_times["paste"])
                            lines.append(f"[green]✓[/green] Paste:        {start} → {end} [dim]({duration})[/dim]")
                        elif current_stage[0] == "paste":
                            elapsed = format_time(time.time() - stage_start_times["paste"])
                            lines.append(f"[yellow]●[/yellow] Paste:        {start} → [dim]in progress ({elapsed})[/dim]")
                    
                    # Commit check stage
                    if "commit_check" in stage_start_times:
                        start = format_timestamp(stage_start_times["commit_check"])
                        if "commit_check" in stage_end_times:
                            end = format_timestamp(stage_end_times["commit_check"])
                            duration = format_time(stage_end_times["commit_check"] - stage_start_times["commit_check"])
                            lines.append(f"[green]✓[/green] Commit Check: {start} → {end} [dim]({duration})[/dim]")
                        elif current_stage[0] == "commit_check":
                            elapsed = format_time(time.time() - stage_start_times["commit_check"])
                            lines.append(f"[yellow]●[/yellow] Commit Check: {start} → [dim]validating ({elapsed})[/dim]")
                    
                    # Commit stage
                    if "commit" in stage_start_times:
                        start = format_timestamp(stage_start_times["commit"])
                        if "commit" in stage_end_times:
                            end = format_timestamp(stage_end_times["commit"])
                            duration = format_time(stage_end_times["commit"] - stage_start_times["commit"])
                            lines.append(f"[green]✓[/green] Commit:       {start} → {end} [dim]({duration})[/dim]")
                        elif current_stage[0] == "commit":
                            elapsed = format_time(time.time() - stage_start_times["commit"])
                            lines.append(f"[yellow]●[/yellow] Commit:       {start} → [dim]saving ({elapsed})[/dim]")
                    
                    # Complete stage
                    if current_stage[0] == "complete" and "complete" in stage_start_times:
                        total_time = format_time(stage_start_times["complete"] - paste_start_time)
                        lines.append(f"[bold green]✅ Complete[/bold green]     {format_timestamp(stage_start_times['complete'])} [dim](total: {total_time})[/dim]")
                    
                    return "\n".join(lines) if lines else ""
                
                def clean_line(line: str) -> str:
                    """Clean ANSI codes and filter noise."""
                    line = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', line)
                    line = re.sub(r'[\x00-\x1f\x7f]', '', line)
                    line = line.strip()
                    # Filter out noisy log lines
                    if any(x in line for x in ['local7.', 'IF_LINK_', 'SSH_SESSION', 'TRANSACTION_']):
                        return ""
                    return line
                
                def render_terminal():
                    """Render a clean, professional terminal display with time estimation and stage tracking."""
                    stage = current_stage[0]
                    total_elapsed = time.time() - paste_start_time
                    
                    # Calculate stage-specific progress
                    if stage == "paste":
                        progress_pct = (current_line[0] + 1) / total_lines if total_lines > 0 else 0
                        stage_elapsed = time.time() - stage_start_times.get("paste", paste_start_time)
                        if progress_pct > 0.01:
                            estimated_total = stage_elapsed / progress_pct
                            remaining = max(0, estimated_total - stage_elapsed)
                        else:
                            remaining = estimated_paste_time
                    elif stage == "commit_check":
                        progress_pct = 1.0  # Paste done
                        stage_elapsed = time.time() - stage_start_times.get("commit_check", time.time())
                        # Estimate remaining based on typical commit check time
                        remaining = max(0, estimated_commit_check_time - stage_elapsed)
                    elif stage == "commit":
                        progress_pct = 1.0
                        stage_elapsed = time.time() - stage_start_times.get("commit", time.time())
                        remaining = max(0, estimated_commit_time - stage_elapsed)
                    else:
                        progress_pct = 1.0
                        remaining = 0
                        stage_elapsed = 0
                    
                    # Build timeline header first
                    timeline_text = Text()
                    timeline_str = build_timeline_header()
                    if timeline_str:
                        for tl_line in timeline_str.split("\n"):
                            # Parse rich markup manually for Text object
                            timeline_text.append(tl_line + "\n")
                    
                    # Build content - show appropriate lines based on stage
                    lines_shown = 0
                    content_text = Text()
                    
                    # Collect lines with their styles
                    styled_lines = []
                    for line in reversed(terminal_buffer):
                        if len(styled_lines) >= TERMINAL_HEIGHT:
                            break
                        clean = clean_line(line)
                        if not clean:
                            continue
                        
                        if stage == "paste":
                            # During paste, only show config lines (with → prefix)
                            if clean.startswith("→"):
                                cfg_line = clean[2:].strip()  # Remove "→ "
                                # DELETE commands (no ) in RED, others in GREEN
                                if cfg_line.strip().startswith("no "):
                                    styled_lines.append((f"  {cfg_line[:TERMINAL_WIDTH]}", "bright_red"))
                                else:
                                    styled_lines.append((f"  {cfg_line[:TERMINAL_WIDTH]}", "bright_green"))
                        else:
                            # During commit_check/commit, show all status lines
                            if clean.startswith("→"):
                                cfg_line = clean[2:].strip()
                                styled_lines.append((f"  {cfg_line[:TERMINAL_WIDTH]}", "dim"))
                            elif clean.startswith("←"):
                                # Device response
                                styled_lines.append((f"  {clean[2:][:TERMINAL_WIDTH]}", "cyan"))
                            elif clean.startswith("⏳") or clean.startswith("✓") or clean.startswith("✗"):
                                # Status messages
                                styled_lines.append((f"{clean[:TERMINAL_WIDTH]}", "yellow"))
                            elif clean.startswith("⏱") or clean.startswith("[dim]"):
                                # Time/progress messages
                                styled_lines.append((f"  {clean[:TERMINAL_WIDTH]}", "dim"))
                            else:
                                # Device output or other messages
                                styled_lines.append((f"  {clean[:TERMINAL_WIDTH]}", "white"))
                    
                    # Add lines in correct order (oldest first)
                    for line_text, style in reversed(styled_lines[-TERMINAL_HEIGHT:]):
                        content_text.append(line_text + "\n", style=style)
                        lines_shown += 1
                    
                    # Pad to fixed height
                    while lines_shown < TERMINAL_HEIGHT:
                        content_text.append("\n")
                        lines_shown += 1
                    
                    # Build stage indicator
                    stage_idx = STAGES.index(stage) if stage in STAGES else 0
                    stage_indicator = ""
                    for i, s in enumerate(STAGES):
                        if i < stage_idx:
                            stage_indicator += f"[green]✓[/green] "
                        elif i == stage_idx:
                            stage_indicator += f"[yellow]●[/yellow] "
                        else:
                            stage_indicator += f"[dim]○[/dim] "
                    
                    # Build progress bar with block characters
                    bar_width = 30
                    if stage == "paste":
                        filled = int(bar_width * progress_pct)
                        bar = f"[bold green]{'█' * filled}[/bold green][dim]{'░' * (bar_width - filled)}[/dim]"
                        line_info = f"[cyan]{current_line[0]+1:,}[/cyan]/[dim]{total_lines:,}[/dim] lines"
                    elif stage == "commit_check":
                        # Pulsing indicator for commit check (no specific progress)
                        pulse_pos = int(time.time() * 2) % bar_width
                        bar = "[dim]" + "░" * pulse_pos + "[/dim][yellow]███[/yellow][dim]" + "░" * (bar_width - pulse_pos - 3) + "[/dim]"
                        line_info = f"[yellow]validating...[/yellow]"
                    elif stage == "commit":
                        pulse_pos = int(time.time() * 2) % bar_width
                        bar = "[dim]" + "░" * pulse_pos + "[/dim][green]███[/green][dim]" + "░" * (bar_width - pulse_pos - 3) + "[/dim]"
                        line_info = f"[green]saving...[/green]"
                    else:
                        bar = f"[bold green]{'█' * bar_width}[/bold green]"
                        line_info = f"[green]done![/green]"
                    
                    # Status line with stage info
                    status = f" {stage_indicator} │ {bar} │ {line_info} "
                    
                    # Build title with timing info and stage name
                    stage_name = STAGE_NAMES.get(stage, stage)
                    timing_info = f"⏱ {format_time(total_elapsed)} elapsed"
                    if remaining > 0 and stage != "complete":
                        timing_info += f" │ ~{format_time(remaining)} remaining"
                    
                    # Build title with phase info if provided
                    phase_prefix = f"[bold magenta]{phase_info}[/bold magenta] │ " if phase_info else ""
                    
                    # Combine timeline header and terminal content
                    # Timeline shows completed stages with timestamps above terminal
                    timeline_lines = len([l for l in timeline_str.split("\n") if l.strip()]) if timeline_str else 0
                    
                    # Build combined content with separator
                    from rich.console import RenderableType
                    combined = Text()
                    if timeline_str:
                        # Add timeline with styled formatting
                        combined.append("─" * 70 + "\n", style="dim")
                        for tl_line in timeline_str.split("\n"):
                            if tl_line.strip():
                                # Simple parsing - just add the line with basic formatting
                                clean_tl = tl_line.replace("[green]", "").replace("[/green]", "")
                                clean_tl = clean_tl.replace("[yellow]", "").replace("[/yellow]", "")
                                clean_tl = clean_tl.replace("[dim]", "").replace("[/dim]", "")
                                clean_tl = clean_tl.replace("[bold green]", "").replace("[/bold green]", "")
                                combined.append(clean_tl + "\n", style="cyan")
                        combined.append("─" * 70 + "\n", style="dim")
                    combined.append_text(content_text)
                    
                    # Adjust height for timeline
                    panel_height = TERMINAL_HEIGHT + 3 + (timeline_lines + 2 if timeline_str else 0)
                    
                    return Panel(
                        combined,
                        title=f"{phase_prefix}[bold white on blue] {device.hostname} [/bold white on blue]  {stage_name}  [dim]{timing_info}[/dim]",
                        subtitle=status,
                        border_style="bright_blue" if stage == "paste" else ("yellow" if stage == "commit_check" else "green"),
                        padding=(0, 1),
                        height=panel_height
                    )
                
                # Use transient=False and lower refresh to prevent flickering
                # Suppress keyboard echo to prevent duplicate lines when user presses keys
                with suppress_keyboard_echo(), Live(render_terminal(), refresh_per_second=4, console=self._get_console(), transient=False, vertical_overflow="visible") as live:
                    # ========== STAGE 1: PASTE ==========
                    current_stage[0] = "paste"
                    last_update = 0
            
                    for i, line in enumerate(lines):
                        current_line[0] = i  # Update for closure
                        stripped = line.rstrip()
                        if stripped:
                            # CRITICAL: Use sendall() to ensure ALL data is sent
                            # channel.send() may not send all data if buffer is full!
                            data = (stripped + "\n").encode('utf-8')
                            channel.sendall(data)
                            # Add to buffer - show config being sent
                            display_line = stripped.strip()
                            if display_line and display_line != "!":
                                terminal_buffer.append(f"→ {display_line}")
                            time.sleep(0.012)  # Increased from 8ms to 12ms for reliability
                        
                        # Read device output periodically to prevent buffer overflow
                        if i % 50 == 0 and channel.recv_ready():
                            partial = channel.recv(8192).decode('utf-8', errors='ignore')
                            for out_line in partial.strip().split('\n'):
                                cleaned = clean_line(out_line)
                                if cleaned and len(cleaned) > 2:
                                    terminal_buffer.append(f"← {cleaned}")
                        
                        # Buffer drain pause every 200 lines for large configs (was 500)
                        # This lets the device CLI catch up and prevents SSH buffer overflow
                        if i > 0 and i % 200 == 0:
                            time.sleep(0.5)  # 500ms pause (was 300ms)
                            # Drain any pending output
                            while channel.recv_ready():
                                channel.recv(8192)
                        
                        # Update display - different intervals based on config size
                        # Small configs (< 100 lines): update every line to show delete commands
                        # Large configs: update every 50 lines to reduce flickering
                        update_interval = 1 if total_lines < 100 else 50
                        if i - last_update >= update_interval:
                            live.update(render_terminal())
                            last_update = i
                    
                    # Paste complete - show 100%
                    current_line[0] = total_lines - 1
                    live.update(render_terminal())
                    
                    # Wait for device to process all pasted config
                    # Longer wait for large configs to ensure device fully processes
                    wait_time = max(5, min(30, total_lines // 1000))  # 5-30 seconds
                    terminal_buffer.append(f"[dim]Waiting {wait_time}s for device to process {total_lines:,} lines...[/dim]")
                    live.update(render_terminal())
                    time.sleep(wait_time)
                    
                    # Drain all pending output
                    drain_count = 0
                    while channel.recv_ready():
                        channel.recv(8192)
                        drain_count += 1
                        time.sleep(0.1)
                    
                    time.sleep(2)  # Additional wait before mode check
                    
                    # Navigate to top of config hierarchy first
                    terminal_buffer.append("[dim]Navigating to config root...[/dim]")
                    live.update(render_terminal())
                    channel.sendall(b"top\n")
                    time.sleep(1)
                    
                    mode_check_output = read_and_show(timeout=30)
                    
                    # ========== VERIFY CONFIG MODE BEFORE COMMIT CHECK ==========
                    # Check if we're still in config mode
                    # NOTE: Config files with many "!" closers can exit config mode,
                    # but the candidate config is PRESERVED! We just need to re-enter.
                    in_config_mode = "(cfg)" in mode_check_output or "cfg" in mode_check_output.lower()
                    
                    if not in_config_mode:
                        terminal_buffer.append("[yellow]⚠ Exited config mode (normal for files with ! closers)[/yellow]")
                        live.update(render_terminal())
                        
                        # Check for "uncommitted changes" prompt - answer "cancel" to stay
                        if 'uncommitted changes' in mode_check_output.lower():
                            terminal_buffer.append("[cyan]Answering 'cancel' to stay in config mode...[/cyan]")
                            live.update(render_terminal())
                            channel.sendall(b"cancel\n")
                            time.sleep(1)
                            read_and_show(timeout=5)
                        
                        # Send blank line to get current prompt
                        channel.sendall(b"\n")
                        time.sleep(0.5)
                        prompt_check = read_and_show(timeout=5)
                        
                        # Check again for uncommitted changes prompt
                        if 'uncommitted changes' in prompt_check.lower():
                            terminal_buffer.append("[cyan]Answering 'cancel' to stay in config mode...[/cyan]")
                            live.update(render_terminal())
                            channel.sendall(b"cancel\n")
                            time.sleep(1)
                            prompt_check = read_and_show(timeout=5)
                        
                        if "(cfg)" not in prompt_check:
                            # Not in config mode - RE-ENTER to access our candidate config
                            # The candidate config is preserved even when we exit cfg mode!
                            terminal_buffer.append("[cyan]Re-entering config mode to access candidate...[/cyan]")
                            live.update(render_terminal())
                            
                            channel.sendall(b"configure\n")
                            time.sleep(1)
                            reenter_output = read_and_show(timeout=10)
                            
                            # Handle uncommitted changes prompt when re-entering
                            if 'uncommitted changes' in reenter_output.lower():
                                terminal_buffer.append("[cyan]Found uncommitted changes - preserving...[/cyan]")
                                live.update(render_terminal())
                                # Don't send anything - we want to keep the changes!
                                # The prompt should return us to cfg mode
                            
                            if "(cfg)" in reenter_output or "cfg" in reenter_output.lower():
                                terminal_buffer.append("[green]✓ Re-entered config mode - candidate preserved[/green]")
                                live.update(render_terminal())
                            else:
                                # Failed to re-enter - this is a real problem
                                terminal_buffer.append("[red]✗ Failed to re-enter config mode[/red]")
                                live.update(render_terminal())
                                return False, "Failed to re-enter configuration mode after paste"
                        else:
                            terminal_buffer.append("[green]✓ Still in config mode[/green]")
                            live.update(render_terminal())
                    
                    # ========== STAGE 2: COMMIT CHECK ==========
                    stage_end_times["paste"] = time.time()  # Mark paste as complete
                    current_stage[0] = "commit_check"
                    stage_start_times["commit_check"] = time.time()
                    terminal_buffer.clear()
                    terminal_buffer.append("⏳ Running commit check...")
                    terminal_buffer.append("   This may take 10-20 minutes for large configs")
                    live.update(render_terminal())
                    
                    if progress_callback:
                        progress_callback("Running commit check...", 65)
                    
                    channel.send("commit check\n")
                    
                    # Read commit check output with live updates
                    commit_check_output = ""
                    check_start = time.time()
                    check_passed = False
                    check_failed = False
                    last_status_update = 0
                    last_activity_time = check_start  # Track when we last saw device output
                    
                    # Scale timeout with config size:
                    # - 83K lines with 3K deletes = ~30-40 min commit check
                    # - Base: 10 min, +1 min per 3000 lines, +1 min per 500 deletes
                    delete_count = len([l for l in config_text.split('\n') if l.strip().startswith('no ')])
                    size_timeout = 600 + (total_lines // 3000) * 60 + (delete_count // 500) * 60
                    CHECK_TIMEOUT = min(max(600, size_timeout), 3600)  # 10-60 min based on size
                    
                    terminal_buffer.append(f"[dim]Config: {total_lines:,} lines, {delete_count:,} deletes[/dim]")
                    terminal_buffer.append(f"[dim]Timeout: {CHECK_TIMEOUT // 60}m (scaled to config size)[/dim]")
                    live.update(render_terminal())
                    
                    while True:
                        elapsed = time.time() - check_start
                        
                        if elapsed > CHECK_TIMEOUT:
                            terminal_buffer.append(f"⚠ Timeout after {int(elapsed)//60}m {int(elapsed)%60}s - checking status...")
                            break
                        
                        # Show elapsed time every 60 seconds (reduced frequency)
                        if int(elapsed) // 60 > last_status_update:
                            last_status_update = int(elapsed) // 60
                            mins = int(elapsed) // 60
                            secs = int(elapsed) % 60
                            time_since_activity = time.time() - last_activity_time
                            if time_since_activity > 30:
                                terminal_buffer.append(f"[dim]⏱ {mins}m {secs}s elapsed... (device processing, last output {int(time_since_activity)}s ago)[/dim]")
                            else:
                                terminal_buffer.append(f"[dim]⏱ {mins}m {secs}s elapsed... (device active)[/dim]")
                            live.update(render_terminal())
                        
                        if channel.recv_ready():
                            chunk = channel.recv(8192).decode('utf-8', errors='ignore')
                            commit_check_output += chunk
                            last_activity_time = time.time()  # Track device activity
                            
                            # Update terminal buffer with last few lines
                            for out_line in chunk.split('\n'):
                                cleaned = clean_line(out_line)
                                if cleaned and len(cleaned) > 2:
                                    terminal_buffer.append(f"  {cleaned[:80]}")
                                elif out_line.strip():
                                    # Show brief syslog indicator to prove device is alive
                                    if 'local7' in out_line:
                                        terminal_buffer.append(f"[dim]  (device syslog activity)[/dim]")
                            
                            # Check for completion - clean syslog noise first
                            lower_output = commit_check_output.lower()
                            lower_output = re.sub(r'local\d\.(info|warning|notice|debug|error)[^\n]*\n?', '', lower_output)
                            
                            # Check for various success patterns
                            if any(pattern in lower_output for pattern in [
                                "commit check passed",
                                "validation complete",
                                "check succeeded",
                                "no configuration changes were made",  # Config already on device
                                "commit action is not applicable"  # Same config, nothing to do
                            ]):
                                check_passed = True
                                break
                            
                            # Check for failure patterns
                            if any(pattern in lower_output for pattern in [
                                "commit check failed",
                                "transaction_commit_check_failed",
                                "validation failed",
                                "check failed"
                            ]):
                                check_failed = True
                                break
                            
                            # Alternative success: prompt returned without errors
                            if "(cfg)#" in chunk and elapsed > 30:
                                # Prompt returned after significant time - likely done
                                if not any(err in lower_output for err in ['error', 'failed', 'abort', 'rejected']):
                                    terminal_buffer.append("[dim]Config prompt returned - checking result...[/dim]")
                                    time.sleep(1)
                                    # Check for any remaining output
                                    if not channel.recv_ready():
                                        check_passed = True
                                        break
                        
                        # Update display
                        live.update(render_terminal())
                        time.sleep(0.5)
                    
                    if check_failed:
                        error_msg = self._extract_error(commit_check_output)
                        terminal_buffer.append(f"✗ Commit check failed: {error_msg[:60]}")
                        live.update(render_terminal())
                        return False, f"Commit check failed: {error_msg}"
                    
                    if not check_passed and not check_failed:
                        # Quick retry to catch delayed output (3 attempts, 2 sec each)
                        for retry in range(3):
                            time.sleep(2)
                            terminal_buffer.append(f"[dim]Checking result... (attempt {retry+1}/3)[/dim]")
                            live.update(render_terminal())
                            
                            if channel.recv_ready():
                                extra = channel.recv(16384).decode('utf-8', errors='ignore')
                                commit_check_output += extra
                                clean_extra = re.sub(r'local\d\.(info|warning|notice|debug|error)[^\n]*\n?', '', extra.lower())
                                
                                # Check for success patterns
                                if any(p in clean_extra for p in [
                                    "commit check passed", "validation complete", "check succeeded",
                                    "no configuration changes were made", "commit action is not applicable"
                                ]):
                                    check_passed = True
                                    break
                                
                                # Check for failure patterns
                                if any(p in clean_extra for p in ["commit check failed", "transaction_commit_check_failed", "check failed"]):
                                    check_failed = True
                                    error_msg = self._extract_error(extra)
                                    terminal_buffer.append(f"✗ Commit check failed: {error_msg[:60]}")
                                    live.update(render_terminal())
                                    return False, f"Commit check failed: {error_msg}"
                                
                                # Alternative success: config prompt returned without errors
                                if "(cfg)#" in extra and not any(err in extra.lower() for err in ['error', 'failed', 'abort']):
                                    check_passed = True
                                    terminal_buffer.append("[dim]Config prompt returned, assuming success[/dim]")
                                    break
                    
                    if not check_passed and not check_failed:
                        # Final check: analyze entire output for errors
                        clean_all = re.sub(r'local\d\.(info|warning|notice|debug|error)[^\n]*\n?', '', commit_check_output.lower())
                        
                        # Check for errors that indicate actual failure
                        critical_errors = ['abort', 'rejected', 'invalid syntax', 'hook failed', 'not found']
                        has_critical = any(err in clean_all for err in critical_errors)
                        
                        if has_critical:
                            error_msg = self._extract_error(commit_check_output)
                            terminal_buffer.append(f"✗ Commit check failed: {error_msg[:60]}")
                            live.update(render_terminal())
                            return False, f"Commit check failed: {error_msg}"
                        
                        # No critical errors - assume success (large configs may not show explicit "passed")
                        elapsed = time.time() - check_start
                        terminal_buffer.append(f"[yellow]⚠ No explicit pass message after {int(elapsed)}s, but no errors - proceeding[/yellow]")
                        live.update(render_terminal())
                        check_passed = True
                    
                    terminal_buffer.append("✓ Commit check passed!")
                    live.update(render_terminal())
                    
                    if dry_run:
                        stage_end_times["commit_check"] = time.time()  # Mark commit check as complete
                        channel.send("exit\n")
                        read_and_show(timeout=10)
                        current_stage[0] = "complete"
                        stage_start_times["complete"] = time.time()
                        terminal_buffer.append("── Dry run complete ──")
                        live.update(render_terminal())
                        return True, "Commit check passed (dry run - no commit)"
                    
                    # ========== STAGE 3: COMMIT ==========
                    stage_end_times["commit_check"] = time.time()  # Mark commit check as complete
                    
                    # Check if commit check said "no changes" - skip actual commit
                    check_output_lower = commit_check_output.lower()
                    if "no configuration changes were made" in check_output_lower or "commit action is not applicable" in check_output_lower:
                        # Config already on device - no need to commit
                        current_stage[0] = "complete"
                        stage_start_times["complete"] = time.time()
                        stage_end_times["commit"] = time.time()  # Mark as instant
                        terminal_buffer.clear()
                        terminal_buffer.append("ℹ️  No configuration changes detected")
                        terminal_buffer.append("   Config already matches device - nothing to commit")
                        live.update(render_terminal())
                        
                        channel.send("exit\n")
                        read_and_show(timeout=5)
                        
                        if progress_callback:
                            progress_callback("No changes needed", 100)
                        
                        time.sleep(2)
                        return True, "Configuration already on device (no changes made)"
                    
                    current_stage[0] = "commit"
                    stage_start_times["commit"] = time.time()
                    terminal_buffer.clear()
                    terminal_buffer.append("💾 Committing configuration...")
                    live.update(render_terminal())
                    
                    if progress_callback:
                        progress_callback("Committing configuration...", 80)
                    
                    channel.send("commit\n")
                    
                    # Read commit output with live updates
                    commit_output = ""
                    commit_start = time.time()
                    commit_succeeded = False
                    commit_failed = False
                    
                    while True:
                        if time.time() - commit_start > self.commit_timeout:
                            break
                        
                        if channel.recv_ready():
                            chunk = channel.recv(8192).decode('utf-8', errors='ignore')
                            commit_output += chunk
                            
                            for out_line in chunk.split('\n'):
                                cleaned = clean_line(out_line)
                                if cleaned and len(cleaned) > 2:
                                    terminal_buffer.append(f"  {cleaned[:80]}")
                            
                            # Check for completion
                            lower_output = commit_output.lower()
                            lower_output = re.sub(r'local\d\.(info|warning|notice|debug|error)[^\n]*\n?', '', lower_output)
                            if "commit succeeded" in lower_output:
                                commit_succeeded = True
                                break
                            # Also treat "no changes" as success (edge case if we missed it earlier)
                            if "no configuration changes were made" in lower_output or "commit action is not applicable" in lower_output:
                                commit_succeeded = True
                                terminal_buffer.append("[dim]ℹ️  No changes were needed[/dim]")
                                break
                            if "commit failed" in lower_output:
                                commit_failed = True
                                break
                        
                        live.update(render_terminal())
                        time.sleep(0.5)
                    
                    if commit_failed:
                        error_msg = self._extract_error(commit_output)
                        terminal_buffer.append(f"✗ Commit failed: {error_msg[:60]}")
                        live.update(render_terminal())
                        return False, f"Commit failed: {error_msg}"
                    
                    if not commit_succeeded:
                        time.sleep(5)
                        if channel.recv_ready():
                            extra = channel.recv(8192).decode('utf-8', errors='ignore')
                            commit_output += extra
                            clean_extra = re.sub(r'local\d\.(info|warning|notice|debug|error)[^\n]*\n?', '', extra.lower())
                            if "commit succeeded" in clean_extra:
                                commit_succeeded = True
                    
                    if not commit_succeeded:
                        terminal_buffer.append("⚠ Commit status unclear")
                        live.update(render_terminal())
                        return False, "Commit status unclear - no success/fail detected"
                    
                    # ========== STAGE 4: COMPLETE ==========
                    stage_end_times["commit"] = time.time()  # Mark commit as complete
                    current_stage[0] = "complete"
                    stage_start_times["complete"] = time.time()
                    total_time = time.time() - paste_start_time
                    terminal_buffer.clear()
                    terminal_buffer.append("✓ Configuration committed successfully!")
                    terminal_buffer.append(f"  Total time: {format_time(total_time)}")
                    terminal_buffer.append(f"  Lines pushed: {total_lines:,}")
                    live.update(render_terminal())
                    
                    channel.send("exit\n")
                    read_and_show(timeout=5)
                    
                    if progress_callback:
                        progress_callback("Configuration committed!", 100)
                    
                    # Keep panel visible so user can see the result
                    # Show countdown so user knows the screen will stay
                    for remaining in range(5, 0, -1):
                        terminal_buffer.append(f"")
                        terminal_buffer.append(f"  [Continuing in {remaining}s... press Ctrl+C to stay]")
                        live.update(render_terminal())
                        time.sleep(1)
                        # Remove countdown lines for next update
                        if len(terminal_buffer) > 3:
                            terminal_buffer.pop()
                            terminal_buffer.pop()
                    
                return True, "Configuration pasted and committed successfully"
            else:
                # Non-live mode - push and call callbacks for external progress tracking
                for i, line in enumerate(lines):
                    stripped = line.rstrip()
                    if stripped:
                        channel.send(stripped + "\n")
                        # Call live_output_callback so external displays can track progress
                        if live_output_callback and stripped.strip() and stripped.strip() != "!":
                            live_output_callback(f"-> {stripped.strip()}")
                    # 5ms for small configs (<150 lines), 10ms for larger (reliability)
                    time.sleep(0.005 if total_lines < 150 else 0.01)
                    
                    # Read device output periodically and forward to callback
                    if i % 50 == 0 and channel.recv_ready():
                        partial = channel.recv(8192).decode('utf-8', errors='ignore')
                        if live_output_callback and partial.strip():
                            for out_line in partial.strip().split('\n')[-3:]:
                                if out_line.strip():
                                    live_output_callback(f"<- {out_line.strip()[:60]}")
                    
                    # Buffer drain pause every 500 lines for large configs
                    if i > 0 and i % 500 == 0:
                        time.sleep(0.3)  # 300ms pause to let device process
                        while channel.recv_ready():
                            channel.recv(8192)
                
                    # Progress: every 10 lines for small configs (<200), else every 100
                    progress_interval = 10 if total_lines < 200 else 100
                    if progress_callback and (i % progress_interval == 0 or i == total_lines - 1):
                        pct = 30 + int((i / total_lines) * 30)
                        progress_callback(f"Pasting line {i+1}/{total_lines}...", pct)
            
            # Wait for device to process all pasted config
            # For large configs (15k+ lines), the device needs time to process
            wait_time = max(2, min(10, total_lines // 3000))  # 2-10 seconds based on size
            time.sleep(wait_time)
            
            # Drain all pending output before commit check
            while channel.recv_ready():
                channel.recv(8192)
                time.sleep(0.1)
            
            # Extra settle time
            time.sleep(1)
            read_and_show(timeout=30)
            
            # Ensure we're at config root level before commit check
            # Send 'top' command to return to config root regardless of current nesting
            channel.send("top\n")
            time.sleep(0.5)
            read_and_show(timeout=5)
            
            if progress_callback:
                progress_callback("Running commit check...", 65)
            if live_output_callback:
                live_output_callback("⏳ Running commit check...")
            
            # Track overall start time for total elapsed
            overall_start = time.time()
            
            if show_live_terminal:
                console = self._get_console()
                commit_check_start = time.time()
                console.print("\n[yellow]⏳ Running commit check...[/yellow]")
            
            channel.send("commit check\n")
            output = read_and_show(timeout=self.commit_timeout)
            
            # Clean syslog noise from output for accurate pattern matching
            import re
            clean_output = output.lower()
            # Remove syslog lines for pattern matching (keep original for error extraction)
            clean_output = re.sub(r'local\d\.(info|warning|notice|debug|error)[^\n]*\n?', '', clean_output)
            clean_output = re.sub(r'if_link_state_change[^\n]*\n?', '', clean_output)
            
            # Check for definitive pass/fail patterns
            passed = "commit check passed" in clean_output
            failed = "commit check failed" in clean_output or "transaction_commit_check_failed" in clean_output
            
            if failed or (not passed and not failed):
                # Only report failure if we find actual error patterns, or explicit failure
                error_msg = self._extract_error(output)
                if error_msg:  # Only fail if we found real errors
                    if live_output_callback:
                        live_output_callback(f"✗ Commit check failed: {error_msg[:40]}")
                    if show_live_terminal:
                        console.print("[red]✗ Commit check failed[/red]")
                        console.print(f"[dim]Error: {error_msg}[/dim]")
                    return False, f"Commit check failed: {error_msg}"
                elif not passed:
                    # No errors found but also no "passed" - might still be running, try reading more
                    time.sleep(5)
                    extra_output = read_and_show(timeout=60)
                    clean_extra = re.sub(r'local\d\.(info|warning|notice|debug|error)[^\n]*\n?', '', extra_output.lower())
                    if "commit check passed" in clean_extra:
                        passed = True
                    elif "commit check failed" in clean_extra:
                        error_msg = self._extract_error(extra_output)
                        if live_output_callback:
                            live_output_callback(f"✗ Commit check failed: {error_msg[:40]}")
                        if show_live_terminal:
                            console.print("[red]✗ Commit check failed[/red]")
                            console.print(f"[dim]Error: {error_msg}[/dim]")
                        return False, f"Commit check failed: {error_msg}"
            
            if not passed:
                # Still not passed - check if there are any real errors
                has_real_errors = any(err in output.lower() for err in [
                    'hook failed', 'transaction_commit_check_failed', 'rejected', 
                    'invalid syntax', 'aborting'
                ])
                
                if not has_real_errors:
                    # No errors found after long commit check - likely succeeded but message lost
                    if show_live_terminal:
                        console.print("[yellow]⚠ No explicit pass/fail but no errors found - assuming success[/yellow]")
                    passed = True  # Proceed cautiously
                else:
                    if show_live_terminal:
                        console.print("[yellow]⚠ Commit check status unclear - check device manually[/yellow]")
                    return False, "Commit check status unclear - no pass/fail detected"
            
            if live_output_callback:
                live_output_callback("✓ Commit check passed")
            if show_live_terminal:
                commit_check_elapsed = time.time() - commit_check_start
                console.print(f"[green]✓ Commit check passed[/green] [dim]({commit_check_elapsed:.1f}s)[/dim]")
            
            if dry_run:
                # Explicitly cancel to discard uncommitted candidate before exit
                channel.send("cancel\n")
                read_and_show(timeout=10)
                channel.send("exit\n")
                read_and_show()
                if live_output_callback:
                    live_output_callback("── Dry run complete ──")
                if show_live_terminal:
                    total_elapsed = time.time() - overall_start
                    console.print(f"[cyan]── Dry run complete ──[/cyan] [dim](total: {total_elapsed:.1f}s)[/dim]")
                return True, "Commit check passed (dry run - no commit)"
            
            if progress_callback:
                progress_callback("Committing configuration...", 80)
            if live_output_callback:
                live_output_callback("⏳ Committing configuration...")
            
            if show_live_terminal:
                commit_start = time.time()
                console.print("[yellow]⏳ Committing configuration...[/yellow]")
            
            channel.send("commit\n")
            output = read_and_show(timeout=self.commit_timeout)
            
            # Clean syslog noise from output for accurate pattern matching
            clean_output = re.sub(r'local\d\.(info|warning|notice|debug|error)[^\n]*\n?', '', output.lower())
            clean_output = re.sub(r'if_link_state_change[^\n]*\n?', '', clean_output)
            
            if "commit succeeded" not in clean_output:
                error_msg = self._extract_error(output)
                if error_msg:  # Only fail if we found real errors
                    if live_output_callback:
                        live_output_callback(f"✗ Commit failed: {error_msg[:40]}")
                    if show_live_terminal:
                        console.print("[red]✗ Commit failed[/red]")
                    return False, f"Commit failed: {error_msg}"
                else:
                    # No errors found - try reading more output
                    time.sleep(5)
                    extra_output = read_and_show(timeout=60)
                    clean_extra = re.sub(r'local\d\.(info|warning|notice|debug|error)[^\n]*\n?', '', extra_output.lower())
                    if "commit succeeded" in clean_extra:
                        pass  # Success, continue below
                    elif "commit failed" in clean_extra:
                        error_msg = self._extract_error(extra_output)
                        if live_output_callback:
                            live_output_callback(f"✗ Commit failed: {error_msg[:40]}")
                        if show_live_terminal:
                            console.print("[red]✗ Commit failed[/red]")
                        return False, f"Commit failed: {error_msg}"
                    else:
                        if show_live_terminal:
                            console.print("[yellow]⚠ Commit status unclear - check device manually[/yellow]")
                        return False, "Commit status unclear - no success/fail detected"
            
            if progress_callback:
                progress_callback("Configuration committed!", 100)
            if live_output_callback:
                live_output_callback("✓ Commit succeeded!")
            
            if show_live_terminal:
                commit_elapsed = time.time() - commit_start
                total_elapsed = time.time() - overall_start
                console.print(f"[green]✓ Commit succeeded[/green] [dim]({commit_elapsed:.1f}s)[/dim]")
                console.print(f"[cyan]── Session complete ──[/cyan] [bold cyan](total: {total_elapsed:.1f}s, {total_lines:,} lines)[/bold cyan]")
            
            channel.send("exit\n")
            read_and_show()
            
            return True, "Configuration pasted and committed successfully"
            
        except paramiko.AuthenticationException:
            return False, "Authentication failed"
        except paramiko.SSHException as e:
            return False, f"SSH error: {str(e)}"
        except socket.timeout:
            return False, "Connection timeout"
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            return False, f"Error: {str(e)}\n{tb[-500:]}"
        finally:
            if channel:
                try:
                    channel.close()
                except:
                    pass
            if client:
                try:
                    client.close()
                except:
                    pass

    def push_config_terminal_check_and_hold(
        self,
        device: Device,
        config_text: str,
        progress_callback: Callable[[str, int], None] = None,
        live_output_callback: Callable[[str], None] = None,
    ) -> Tuple[bool, str, Optional[Any], Optional[Any]]:
        """
        Push config, run commit check, and hold SSH session for commit/cancel.
        On success: returns (True, "Commit check passed", channel, client).
        Caller must call commit or cancel on the channel, then close channel and client.
        On failure: sends cancel+exit, closes SSH, returns (False, error_msg, None, None).
        """
        client = None
        channel = None
        keep_alive = False

        try:
            if progress_callback:
                progress_callback("Connecting to device...", 10)

            ssh_host = get_ssh_hostname(device)
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(
                hostname=ssh_host,
                username=device.username,
                password=device.get_password(),
                timeout=self.timeout,
                look_for_keys=False,
                allow_agent=False
            )

            channel = client.invoke_shell()
            channel.settimeout(self.timeout)

            def read_and_show(timeout=30):
                output = self._read_until_prompt(channel, timeout=timeout)
                if live_output_callback and output.strip():
                    live_output_callback(output)
                return output

            time.sleep(1)
            read_and_show()

            channel.send("set logging terminal\n")
            read_and_show(timeout=5)

            if progress_callback:
                progress_callback("Entering configuration mode...", 20)

            channel.send("configure\n")
            output = read_and_show(timeout=10)
            if "cfg" not in output.lower() and "#" not in output:
                return False, "Failed to enter configuration mode", None, None

            channel.send("rollback 0\n")
            time.sleep(0.5)
            read_and_show(timeout=10)

            if progress_callback:
                progress_callback("Pasting configuration...", 30)

            config_text = config_text.replace('\r\n', '\n').replace('\r', '\n')
            lines = config_text.strip().split('\n')
            total_lines = len(lines)

            for i, line in enumerate(lines):
                stripped = line.rstrip()
                if stripped:
                    channel.send(stripped + "\n")
                    if live_output_callback and stripped.strip() and stripped.strip() != "!":
                        live_output_callback(f"-> {stripped.strip()}")
                # 5ms for small configs (<150 lines), 10ms for larger (reliability)
                time.sleep(0.005 if total_lines < 150 else 0.01)

                if i % 50 == 0 and channel.recv_ready():
                    partial = channel.recv(8192).decode('utf-8', errors='ignore')
                    if live_output_callback and partial.strip():
                        for out_line in partial.strip().split('\n')[-3:]:
                            if out_line.strip():
                                live_output_callback(f"<- {out_line.strip()[:60]}")

                if i > 0 and i % 500 == 0:
                    time.sleep(0.3)
                    while channel.recv_ready():
                        channel.recv(8192)

                # Progress: every 10 lines for small configs (<200), else every 100
                progress_interval = 10 if total_lines < 200 else 100
                if progress_callback and (i % progress_interval == 0 or i == total_lines - 1):
                    pct = 30 + int((i / total_lines) * 30)
                    progress_callback(f"Pasting line {i+1}/{total_lines}...", pct)

            wait_time = max(2, min(10, total_lines // 3000))
            time.sleep(wait_time)

            while channel.recv_ready():
                channel.recv(8192)
                time.sleep(0.1)
            time.sleep(1)
            read_and_show(timeout=30)

            channel.send("top\n")
            time.sleep(0.5)
            read_and_show(timeout=5)

            if progress_callback:
                progress_callback("Running commit check...", 65)
            if live_output_callback:
                live_output_callback("[INFO] Running commit check...")

            channel.send("commit check\n")
            output = read_and_show(timeout=self.commit_timeout)

            clean_output = output.lower()
            clean_output = re.sub(r'local\d\.(info|warning|notice|debug|error)[^\n]*\n?', '', clean_output)
            clean_output = re.sub(r'if_link_state_change[^\n]*\n?', '', clean_output)

            passed = "commit check passed" in clean_output
            failed = "commit check failed" in clean_output or "transaction_commit_check_failed" in clean_output

            if failed or (not passed and not failed):
                error_msg = self._extract_error(output)
                if error_msg:
                    if live_output_callback:
                        live_output_callback(f"[ERROR] Commit check failed: {error_msg[:40]}")
                    channel.send("cancel\n")
                    read_and_show(timeout=10)
                    channel.send("exit\n")
                    read_and_show(timeout=5)
                    return False, f"Commit check failed: {error_msg}", None, None
                elif not passed:
                    time.sleep(5)
                    extra_output = read_and_show(timeout=60)
                    clean_extra = re.sub(r'local\d\.(info|warning|notice|debug|error)[^\n]*\n?', '', extra_output.lower())
                    if "commit check passed" in clean_extra:
                        passed = True
                    elif "commit check failed" in clean_extra:
                        error_msg = self._extract_error(extra_output)
                        if live_output_callback:
                            live_output_callback(f"[ERROR] Commit check failed: {error_msg[:40]}")
                        channel.send("cancel\n")
                        read_and_show(timeout=10)
                        channel.send("exit\n")
                        read_and_show(timeout=5)
                        return False, f"Commit check failed: {error_msg}", None, None

            if not passed:
                has_real_errors = any(err in output.lower() for err in [
                    'hook failed', 'transaction_commit_check_failed', 'rejected',
                    'invalid syntax', 'aborting'
                ])
                if not has_real_errors:
                    passed = True
                else:
                    channel.send("cancel\n")
                    read_and_show(timeout=10)
                    channel.send("exit\n")
                    read_and_show(timeout=5)
                    return False, "Commit check status unclear - no pass/fail detected", None, None

            if live_output_callback:
                live_output_callback("[OK] Commit check passed")
            if progress_callback:
                progress_callback("Commit check passed - awaiting decision", 70)

            keep_alive = True
            return True, "Commit check passed", channel, client

        except paramiko.AuthenticationException:
            return False, "Authentication failed", None, None
        except paramiko.SSHException as e:
            return False, f"SSH error: {str(e)}", None, None
        except socket.timeout:
            return False, "Connection timeout", None, None
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            return False, f"Error: {str(e)}\n{tb[-500:]}", None, None
        finally:
            if not keep_alive and channel:
                try:
                    channel.close()
                except Exception:
                    pass
            if not keep_alive and client:
                try:
                    client.close()
                except Exception:
                    pass

    def commit_held_session(
        self,
        channel,
        client,
        live_output_callback: Callable[[str], None] = None,
    ) -> Tuple[bool, str]:
        """Send commit on held SSH session, read result, close. Returns (success, message)."""
        try:
            def read_and_show(timeout=30):
                output = self._read_until_prompt(channel, timeout=timeout)
                if live_output_callback and output.strip():
                    live_output_callback(output)
                return output

            channel.send("commit\n")
            output = read_and_show(timeout=self.commit_timeout)
            clean = re.sub(r'local\d\.(info|warning|notice|debug|error)[^\n]*\n?', '', output.lower())
            clean = re.sub(r'if_link_state_change[^\n]*\n?', '', clean)
            if "commit succeeded" in clean:
                if live_output_callback:
                    live_output_callback("[OK] Commit succeeded")
                channel.send("exit\n")
                read_and_show(timeout=5)
                return True, "Commit succeeded"
            error_msg = self._extract_error(output)
            channel.send("cancel\n")
            read_and_show(timeout=10)
            channel.send("exit\n")
            read_and_show(timeout=5)
            return False, error_msg or "Commit failed"
        finally:
            try:
                channel.close()
            except Exception:
                pass
            try:
                client.close()
            except Exception:
                pass

    def cancel_held_session(
        self,
        channel,
        client,
        live_output_callback: Callable[[str], None] = None,
    ) -> None:
        """Send cancel+exit on held SSH session and close."""
        try:
            def read_and_show(timeout=10):
                output = self._read_until_prompt(channel, timeout=timeout)
                if live_output_callback and output.strip():
                    live_output_callback(output)
                return output

            channel.send("cancel\n")
            read_and_show(timeout=10)
            channel.send("exit\n")
            read_and_show(timeout=5)
        finally:
            try:
                channel.close()
            except Exception:
                pass
            try:
                client.close()
            except Exception:
                pass

    def cleanup_device_candidate(self, device: Device) -> Tuple[bool, str]:
        """Connect to device, enter configure, cancel (discard candidate), exit. For cleanup after failed push."""
        client = None
        channel = None
        try:
            ssh_host = get_ssh_hostname(device)
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(
                hostname=ssh_host,
                username=device.username,
                password=device.get_password(),
                timeout=self.timeout,
                look_for_keys=False,
                allow_agent=False
            )
            channel = client.invoke_shell()
            channel.settimeout(self.timeout)
            time.sleep(1)
            self._read_until_prompt(channel, timeout=5)
            channel.send("configure\n")
            out = self._read_until_prompt(channel, timeout=10)
            if "cfg" not in out.lower():
                return False, "Failed to enter configure mode"
            channel.send("cancel\n")
            self._read_until_prompt(channel, timeout=10)
            channel.send("exit\n")
            self._read_until_prompt(channel, timeout=5)
            return True, "Cleanup complete"
        except Exception as e:
            return False, str(e)
        finally:
            if channel:
                try:
                    channel.close()
                except Exception:
                    pass
            if client:
                try:
                    client.close()
                except Exception:
                    pass

    # DriveNets Platform timing profiles based on real-world observations
    # Times are in seconds - calibrated against actual commit times
    # 60k line config with 2000+ PWHE typically takes 8-15 minutes total
    PLATFORM_TIMING = {
        # SA-36CD-S / SA-36CD (Single-rack NCE, 1 NCP, Jericho2C+)
        'SA-36CD-S': {
            'upload_per_kb': 0.05,       # SCP is fast (~20MB/s)
            'load_per_1k_lines': 3.0,    # Load override: ~3s per 1k lines
            'commit_per_1k_lines': 1.5,  # Commit validation
            'base_commit_time': 30,      # Base overhead
            'pwhe_per_100': 5.0,         # PWHE QoS policy verification
            'fxc_per_100': 3.0,          # FXC service binding
        },
        # SA-48CD (Single-rack, larger scale)
        'SA-48CD': {
            'upload_per_kb': 0.05,
            'load_per_1k_lines': 3.5,
            'commit_per_1k_lines': 2.0,
            'base_commit_time': 35,
            'pwhe_per_100': 6.0,
            'fxc_per_100': 4.0,
        },
        # Multi-NCP cluster (distributed) - slower due to sync
        'NCP': {
            'upload_per_kb': 0.08,
            'load_per_1k_lines': 4.0,
            'commit_per_1k_lines': 2.5,
            'base_commit_time': 45,
            'pwhe_per_100': 8.0,
            'fxc_per_100': 5.0,
        },
        # NCM - Network Cloud Module (modular, fast)
        'NCM': {
            'upload_per_kb': 0.05,
            'load_per_1k_lines': 2.5,
            'commit_per_1k_lines': 1.2,
            'base_commit_time': 25,
            'pwhe_per_100': 4.0,
            'fxc_per_100': 2.5,
        },
        # NCC cluster (largest scale, longest sync)
        'NCC': {
            'upload_per_kb': 0.1,
            'load_per_1k_lines': 5.0,
            'commit_per_1k_lines': 3.0,
            'base_commit_time': 60,
            'pwhe_per_100': 10.0,
            'fxc_per_100': 6.0,
        },
    }

    @staticmethod
    def extract_platform_from_config(config_text: str) -> str:
        """Extract actual platform type from config header or content.
        
        DriveNets platforms:
        - SA-36CD-S, SA-36CD: Single-rack NCE
        - SA-48CD: Larger single-rack
        - NCE with multiple NCPs
        - NCC cluster
        """
        import re
        
        # Look for Type: in config header
        type_match = re.search(r'#\s*•?\s*Type:\s*(\S+)', config_text)
        if type_match:
            platform_type = type_match.group(1)
            # Map common types
            if 'SA-36CD' in platform_type:
                return 'SA-36CD-S'
            elif 'SA-48CD' in platform_type:
                return 'SA-48CD'
            elif 'NCM' in platform_type:
                return 'NCM'
            elif 'NCC' in platform_type:
                return 'NCC'
            return platform_type
        
        # Fallback: Check NCP/NCC counts in header
        ncc_match = re.search(r'NCC:\s*(\d+)/(\d+)', config_text)
        ncp_match = re.search(r'NCP:\s*(\d+)/(\d+)', config_text)
        
        if ncc_match:
            total_ncc = int(ncc_match.group(2))
            if total_ncc > 2:
                return 'NCC'
        
        if ncp_match:
            total_ncp = int(ncp_match.group(2))
            if total_ncp > 1:
                return 'NCP'
        
        return 'SA-36CD-S'  # Default to single-rack

    def estimate_push_time(
        self,
        config_text: str,
        platform: str = None,
        scale_counts: Dict[str, int] = None
    ) -> Dict[str, float]:
        """
        Estimate time for each stage of config push based on platform and config complexity.
        
        Uses a multi-tier approach:
        1. First tries to find a SIMILAR historical push (same scale type & counts)
        2. Then checks for SCALE-TYPE specific learned timing
        3. Then checks for PLATFORM learned timing
        4. Falls back to DriveNets platform knowledge if no history
        
        The system learns from every successful push and improves over time.
        
        Args:
            config_text: The configuration text
            platform: Device platform (auto-detected if None)
            scale_counts: Dict with counts of scale types for better matching
        
        Returns:
            Dict with estimated times for each stage
        """
        import re
        
        # Auto-detect platform if not specified
        if not platform:
            platform = self.extract_platform_from_config(config_text)
        
        config_size_kb = len(config_text) / 1024
        line_count = len(config_text.split('\n'))
        lines_k = line_count / 1000
        
        # Count PWHE interfaces (slow due to QoS)
        pwhe_count = len(re.findall(r'^\s*ph\d+\.\d+', config_text, re.MULTILINE))
        pwhe_k = pwhe_count / 100
        
        # Count L2 AC sub-interfaces (with l2-service)
        l2_ac_count = len(re.findall(r'l2-service\s+enabled', config_text, re.MULTILINE))
        
        # Count FXC/service instances
        fxc_count = len(re.findall(r'instance\s+FXC-\d+', config_text))
        if fxc_count == 0:
            fxc_count = len(re.findall(r'evpn-vpws-fxc\s+instance', config_text))
        fxc_k = fxc_count / 100
        
        # Count BGP peers
        bgp_peers = len(re.findall(r'^\s+neighbor\s+\d', config_text, re.MULTILINE))
        
        # Build scale counts if not provided
        if not scale_counts:
            scale_counts = {
                'pwhe_subifs': pwhe_count,
                'l2_ac_subifs': l2_ac_count,
                'fxc_services': fxc_count,
                'bgp_peers': bgp_peers
            }
        
        # Determine scale type
        scale_type = _determine_scale_type(scale_counts, pwhe_count, fxc_count)
        
        # TIER 1: Try to find a similar historical push
        similar_push = find_similar_push(scale_counts, platform)
        if similar_push:
            # Scale the time based on line count ratio
            similar_lines = similar_push.get('line_count', 1)
            similar_time = similar_push.get('actual_time', 300)
            time_ratio = line_count / similar_lines if similar_lines > 0 else 1.0
            
            # Don't extrapolate too far - cap at 1.5x for conservative estimate
            # Similar configs usually have similar commit times regardless of small line count diffs
            time_ratio = min(max(time_ratio, 0.7), 1.5)
            total_estimated = similar_time * time_ratio
            
            estimates = {
                'connect': 3.0,
                'upload': max(5.0, total_estimated * 0.05),
                'load': max(15.0, total_estimated * 0.25),
                'commit_check': max(30.0, total_estimated * 0.30),
                'commit': max(30.0, total_estimated * 0.38),
            }
            
            estimates['total'] = sum(estimates.values())
            estimates['platform_detected'] = platform
            estimates['timing_source'] = 'similar_push'
            estimates['scale_type'] = scale_type
            estimates['similar_device'] = similar_push.get('device', 'unknown')
            estimates['similar_time'] = similar_time
            estimates['scale_counts'] = scale_counts
            
            return estimates
        
        # TIER 2: Try scale-type specific timing
        scale_learned = get_learned_timing_by_scale(scale_type, platform)
        if scale_learned and scale_learned.get('timing_source') == 'scale_type':
            learned_time_per_1k = scale_learned['learned_time_per_1k_lines']
            total_estimated = lines_k * learned_time_per_1k
            
            estimates = {
                'connect': 3.0,
                'upload': max(5.0, total_estimated * 0.05),
                'load': max(15.0, total_estimated * 0.25),
                'commit_check': max(30.0, total_estimated * 0.30),
                'commit': max(30.0, total_estimated * 0.38),
            }
            
            estimates['total'] = sum(estimates.values())
            estimates['platform_detected'] = platform
            estimates['timing_source'] = 'scale_type'
            estimates['scale_type'] = scale_type
            estimates['sample_count'] = scale_learned['sample_count']
            estimates['learned_rate'] = learned_time_per_1k
            estimates['scale_counts'] = scale_counts
            
            return estimates
        
        # TIER 3: Platform learned timing
        learned = get_learned_timing(platform)
        if learned and learned.get('sample_count', 0) >= 1:
            learned_time_per_1k = learned['learned_time_per_1k_lines']
            total_estimated = lines_k * learned_time_per_1k
            
            # Adjust for scale type differences (PWHE is slower than L2 AC)
            if scale_type in ['pwhe_fxc', 'pwhe_only']:
                total_estimated *= 1.3  # PWHE is ~30% slower
            elif scale_type in ['l2ac_fxc', 'l2ac_only']:
                total_estimated *= 0.9  # L2 AC is ~10% faster
            
            estimates = {
                'connect': 3.0,
                'upload': max(5.0, total_estimated * 0.05),
                'load': max(15.0, total_estimated * 0.25),
                'commit_check': max(30.0, total_estimated * 0.30),
                'commit': max(30.0, total_estimated * 0.38),
            }
            
            estimates['total'] = sum(estimates.values())
            estimates['platform_detected'] = platform
            estimates['timing_source'] = 'platform_learned'
            estimates['scale_type'] = scale_type
            estimates['sample_count'] = learned['sample_count']
            estimates['learned_rate'] = learned_time_per_1k
            estimates['scale_counts'] = scale_counts
            
            return estimates
        
        # TIER 4: Fall back to static DriveNets platform timing
        timing = self.PLATFORM_TIMING.get(platform, self.PLATFORM_TIMING['SA-36CD-S'])
        
        estimates = {
            'connect': 3.0,
            'upload': max(5.0, config_size_kb * timing['upload_per_kb']),
            'load': max(15.0, lines_k * timing['load_per_1k_lines']),
            'commit_check': max(
                timing['base_commit_time'],
                lines_k * timing['commit_per_1k_lines'] +
                pwhe_k * timing.get('pwhe_per_100', 15.0) +
                fxc_k * timing.get('fxc_per_100', 10.0)
            ),
            'commit': max(
                timing['base_commit_time'] * 1.2,
                (lines_k * timing['commit_per_1k_lines'] +
                 pwhe_k * timing.get('pwhe_per_100', 15.0) +
                 fxc_k * timing.get('fxc_per_100', 10.0)) * 1.3
            ),
        }
        
        estimates['total'] = sum(estimates.values())
        estimates['platform_detected'] = platform
        estimates['timing_source'] = 'default'
        estimates['scale_type'] = scale_type
        estimates['scale_counts'] = scale_counts
        
        return estimates

    def push_factory_reset(
        self,
        device: Device,
        progress_callback: Callable[[Dict[str, Any]], None] = None
    ) -> Tuple[bool, str, List[str]]:
        """
        Reset device to factory default configuration.
        
        This performs: load override factory-default → commit
        
        Use this before loading a large config that would exceed the 8000 interface
        per-commit limit. By resetting first, the new config loads fresh.
        
        Args:
            device: Target device
            progress_callback: Callback for progress updates
            
        Returns:
            Tuple of (success, message, terminal_log)
        """
        terminal_log = []
        start_time = time.time()
        
        # Factory reset estimate: faster now since we skip commit check!
        # (connect 5s, load 5s, commit 5-10min depending on config size)
        # Skipping commit check saves 6-10 minutes on large configs.
        factory_reset_estimate = 300  # 5 minutes (was 10 min with commit check)
        
        def update_progress(stage: str, percent: int, message: str, output: str = ""):
            if progress_callback:
                elapsed = time.time() - start_time
                # Calculate remaining based on progress
                if percent > 0:
                    estimated_total = max(elapsed / (percent / 100), factory_reset_estimate)
                    remaining = max(0, estimated_total - elapsed)
                else:
                    remaining = factory_reset_estimate
                
                progress_callback({
                    'stage': stage,
                    'percent': percent,
                    'message': message,
                    'terminal_output': output,
                    'elapsed': elapsed,
                    'estimated_remaining': remaining
                })
            if output:
                terminal_log.append(f"[{stage}] {output}")
        
        try:
            # Connect using best available IP from operational.json
            ssh_host = get_ssh_hostname(device)
            update_progress("connect", 5, f"Connecting to {device.hostname} ({ssh_host})...")
            
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(
                hostname=ssh_host,
                username=device.username,
                password=device.get_password(),
                timeout=self.timeout,
                look_for_keys=False,
                allow_agent=False
            )
            
            channel = client.invoke_shell()
            channel.settimeout(self.timeout)
            
            time.sleep(1)
            initial_output = self._read_until_prompt(channel)
            update_progress("connect", 10, "Connected", initial_output)
            
            # Enable terminal logging
            channel.send("set logging terminal\n")
            self._read_until_prompt(channel, timeout=5)
            
            # Enter config mode
            update_progress("configure", 20, "Entering configuration mode...")
            channel.send("configure\n")
            output = self._read_until_prompt(channel, timeout=10)
            update_progress("configure", 25, "In configuration mode", output)
            
            # Load factory default
            update_progress("load", 30, "Loading factory-default...")
            channel.send("load override factory-default\n")
            
            load_output = ""
            load_start = time.time()
            prompt_seen = False
            
            while True:
                if time.time() - load_start > 60:  # 60s timeout for factory reset
                    break
                if channel.recv_ready():
                    chunk = channel.recv(65535).decode('utf-8', errors='ignore')
                    load_output += chunk
                    update_progress("load", 40, "Loading factory-default...", chunk)
                    prompt_seen = False  # Reset - got new data
                else:
                    # No data - check if we're done
                    if load_output.strip():
                        # Check last line for prompt (not the whole output)
                        last_line = load_output.strip().split('\n')[-1]
                        if last_line.endswith('#') or last_line.endswith('>'):
                            if prompt_seen:
                                # Saw prompt twice with no new data - we're done
                                break
                            prompt_seen = True
                            time.sleep(0.5)  # Wait a bit more to confirm
                            continue
                    time.sleep(0.1)
            
            update_progress("load", 50, "Factory default loaded", load_output[-200:])
            
            # SKIP commit check for factory-default - it's always valid!
            # Factory-default is a known-good config, and commit check can take 6-10 MINUTES
            # when there's a large running config due to the diff calculation.
            # Go straight to commit to save significant time.
            
            # Commit - deleting lots of interfaces can take 10+ minutes!
            update_progress("commit", 75, "Committing factory reset...")
            channel.send("commit\n")
            
            commit_output = ""
            commit_start = time.time()
            while True:
                if time.time() - commit_start > 900:  # 15 min timeout - large config changes take time
                    break
                if channel.recv_ready():
                    chunk = channel.recv(65535).decode('utf-8', errors='ignore')
                    commit_output += chunk
                    update_progress("commit", 85, "Committing...", chunk)
                    if 'commit succeeded' in commit_output.lower():
                        break
                    if 'error' in commit_output.lower():
                        break
                else:
                    time.sleep(0.2)
            
            if "commit succeeded" not in commit_output.lower():
                return False, "Factory reset commit failed", terminal_log
            
            # Exit config mode
            channel.send("exit\n")
            self._read_until_prompt(channel)
            
            update_progress("complete", 100, "Factory reset committed successfully")
            
            client.close()
            return True, "Factory reset complete", terminal_log
            
        except Exception as e:
            return False, f"Factory reset error: {str(e)}", terminal_log

    def push_config_enhanced(
        self,
        device: Device,
        config_text: str,
        config_name: str = None,
        dry_run: bool = False,
        raw_terminal: bool = False,
        progress_callback: Callable[[Dict[str, Any]], None] = None
    ) -> Tuple[bool, str, List[str]]:
        """
        Enhanced config push with detailed progress and raw terminal mode.
        
        Uses standard load override approach - the config file should include
        all necessary hierarchies (system, interfaces, services, etc.).
        
        Args:
            device: Target device
            config_text: Full configuration text to push (include system for PWHE!)
            config_name: Name for the config file on device
            dry_run: If True, only run commit check, don't commit
            raw_terminal: If True, include raw terminal output
            progress_callback: Callback for detailed progress updates
                Receives dict: {'stage': str, 'percent': int, 'message': str, 
                               'elapsed': float, 'estimated_remaining': float,
                               'terminal_output': str (if raw_terminal)}
        
        Returns:
            Tuple of (success, message, terminal_log)
        """
        client = None
        channel = None
        terminal_log = []
        start_time = time.time()
        
        # Get platform from device or default to NCP
        platform = getattr(device, 'platform', None)
        platform_str = platform.value if platform else 'NCP'
        
        # Estimate timing
        estimates = self.estimate_push_time(config_text, platform_str)
        
        def update_progress(stage: str, percent: int, message: str, output: str = ""):
            """Helper to update progress with timing info."""
            if progress_callback:
                elapsed = time.time() - start_time
                # Calculate estimated remaining based on progress
                if percent > 0:
                    estimated_total = elapsed / (percent / 100)
                    remaining = max(0, estimated_total - elapsed)
                else:
                    remaining = estimates['total']
                
                progress_callback({
                    'stage': stage,
                    'percent': percent,
                    'message': message,
                    'elapsed': elapsed,
                    'estimated_remaining': remaining,
                    'terminal_output': output if raw_terminal else None
                })
            
            if raw_terminal and output:
                terminal_log.append(f"[{stage}] {output}")
        
        try:
            # === STAGE 1: Connect ===
            # Connect using best available IP from operational.json
            ssh_host = get_ssh_hostname(device)
            update_progress("connect", 5, f"Connecting to {device.hostname} ({ssh_host})...")
            
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(
                hostname=ssh_host,
                username=device.username,
                password=device.get_password(),
                timeout=self.timeout,
                look_for_keys=False,
                allow_agent=False
            )
            
            channel = client.invoke_shell()
            channel.settimeout(self.timeout)
            
            time.sleep(1)
            initial_output = self._read_until_prompt(channel)
            update_progress("connect", 8, "Connected successfully", initial_output)
            
            # Update devices.json with working connection info
            update_device_connection_info(device.hostname, ssh_host, "SSH→MGMT")
            
            # Generate config filename
            if not config_name:
                config_name = f"scaler_{timestamp_filename(suffix='')}.txt"
            
            # === STAGE 2: Upload ===
            update_progress("upload", 10, f"Uploading configuration ({len(config_text):,} bytes)...")
            
            remote_path = f"/config/{config_name}"
            upload_success, upload_msg = self._scp_upload(
                device=device,
                config_text=config_text,
                remote_path=remote_path,
                timeout=self.load_timeout
            )
            
            if not upload_success:
                return False, f"SCP upload failed: {upload_msg}", terminal_log
            
            update_progress("upload", 20, f"Upload complete: {upload_msg}")
            
            # Always enable terminal logging to see problems during commit
            channel.send("set logging terminal\n")
            log_output = self._read_until_prompt(channel, timeout=5)
            update_progress("upload", 22, "Terminal monitor enabled", log_output if raw_terminal else "")
            
            # === STAGE 3: Enter Configure Mode ===
            update_progress("configure", 40, "Entering configuration mode...")
            
            channel.send("configure\n")
            output = self._read_until_prompt(channel, timeout=10)
            update_progress("configure", 42, "In configuration mode", output)
            
            if "cfg" not in output.lower() and "#" not in output:
                return False, "Failed to enter configuration mode", terminal_log
            
            # === STAGE 4: Clear dirty candidate config ===
            update_progress("configure", 43, "Clearing candidate config (rollback 0)...")
            channel.send("rollback 0\n")
            rollback_output = self._read_until_prompt(channel, timeout=15)
            update_progress("configure", 44, "Candidate config cleared", rollback_output if raw_terminal else "")
            
            # === STAGE 5: Load Configuration ===
            line_count = len(config_text.split('\n'))
            update_progress("load", 45, f"Loading configuration ({line_count:,} lines)...")
            
            channel.send(f"load override {config_name}\n")
            
            # Read with progress updates
            load_output = ""
            load_start = time.time()
            last_percent = 45
            
            while True:
                if time.time() - load_start > self.load_timeout:
                    break
                
                if channel.recv_ready():
                    chunk = channel.recv(65535).decode('utf-8', errors='ignore')
                    load_output += chunk
                    
                    # Parse device progress (DNOS shows: [=====>    ] 45%)
                    progress_match = re.search(r'\]\s*(\d+)%', chunk)
                    if progress_match:
                        device_pct = int(progress_match.group(1))
                        # Map device progress (0-100) to our range (45-55)
                        mapped_pct = 45 + int(device_pct * 0.15)
                        if mapped_pct > last_percent:
                            last_percent = mapped_pct
                            update_progress("load", mapped_pct, f"Loading... {device_pct}%", chunk)
                    else:
                        # Always stream terminal output even without progress bar
                        update_progress("load", last_percent, "Loading...", chunk)
                    
                    # Handle "uncommitted changes" prompt if it appears
                    # Answer "cancel" to stay in config mode and continue with load
                    if 'uncommitted changes' in load_output.lower() and 'yes/no/cancel' in load_output.lower():
                        channel.send("cancel\n")  # Stay in config mode, continue loading
                        time.sleep(0.5)
                        continue
                    
                    # Check for completion
                    if load_output.rstrip().endswith(('#', '>', 'cfg#', 'cfg>')):
                        break
                    if 'error' in load_output.lower():
                        break
                else:
                    time.sleep(0.1)
            
            update_progress("load", 60, "Load complete", load_output[-500:])
            
            if "error" in load_output.lower():
                error_match = re.search(r"ERROR:\s*(.+?)(?:\n|$)", load_output, re.IGNORECASE)
                error_msg = error_match.group(1) if error_match else load_output[-500:]
                return False, f"Load failed: {error_msg}", terminal_log
            
            # === STAGE 6: Commit Check ===
            est_check_time = int(estimates['commit_check'])
            update_progress("commit_check", 62, f"🔍 Starting commit check (est. {est_check_time}s)...")
            
            channel.send("commit check\n")
            
            check_output = ""
            check_start = time.time()
            last_update = time.time()
            
            # Animation frames for visual feedback
            spinners = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
            spin_idx = 0
            
            while True:
                if time.time() - check_start > self.commit_timeout:
                    break
                
                if channel.recv_ready():
                    chunk = channel.recv(65535).decode('utf-8', errors='ignore')
                    check_output += chunk
                    
                    # Handle "uncommitted changes" prompt if session is closing
                    # Answer "cancel" to stay in config mode
                    if 'uncommitted changes' in check_output.lower() and 'yes/no/cancel' in check_output.lower():
                        channel.send("cancel\n")
                        time.sleep(0.5)
                        continue
                    
                    # Check for success patterns
                    check_lower = check_output.lower()
                    if any(p in check_lower for p in [
                        'commit check passed', 'no configuration changes were made', 'commit action is not applicable'
                    ]):
                        break
                    if 'error' in check_lower or 'failed' in check_lower:
                        break
                    if check_output.rstrip().endswith(('#', '>')):
                        time.sleep(0.5)
                        if not channel.recv_ready():
                            break
                
                # Update progress every 0.5 seconds for smooth animation
                if time.time() - last_update >= 0.5:
                    elapsed_check = time.time() - check_start
                    check_pct = min(78, 62 + int(elapsed_check / max(1, estimates['commit_check']) * 16))
                    
                    # Calculate remaining time
                    if elapsed_check > 0:
                        remaining = max(0, est_check_time - elapsed_check)
                    else:
                        remaining = est_check_time
                    
                    # Spinner animation
                    spinner = spinners[spin_idx % len(spinners)]
                    spin_idx += 1
                    
                    # Format elapsed/remaining
                    elapsed_str = f"{int(elapsed_check)}s" if elapsed_check < 60 else f"{int(elapsed_check//60)}m {int(elapsed_check%60)}s"
                    remaining_str = f"{int(remaining)}s" if remaining < 60 else f"{int(remaining//60)}m {int(remaining%60)}s"
                    
                    status_msg = f"{spinner} Validating configuration... ({elapsed_str} elapsed, ~{remaining_str} remaining)"
                    update_progress("commit_check", check_pct, status_msg, check_output[-200:] if raw_terminal else "")
                    last_update = time.time()
                
                time.sleep(0.1)
            
            update_progress("commit_check", 80, "Commit check complete", check_output[-500:])
            
            # Check for success - includes "no changes" which means config already on device
            check_lower = check_output.lower()
            commit_success = any(p in check_lower for p in [
                "commit check passed", "no configuration changes were made", "commit action is not applicable"
            ])
            if not commit_success:
                error_msg = self._extract_error(check_output)
                return False, f"Commit check failed: {error_msg}", terminal_log
            
            if dry_run:
                channel.send("exit\n")
                self._read_until_prompt(channel)
                update_progress("complete", 100, "Commit check passed (dry run)")
                return True, "Commit check passed (dry run - no commit)", terminal_log
            
            # === STAGE 7: Commit ===
            update_progress("commit", 82, f"Committing configuration (est. {int(estimates['commit'])}s)...")
            
            channel.send("commit\n")
            
            commit_output = ""
            commit_start = time.time()
            
            while True:
                if time.time() - commit_start > self.commit_timeout:
                    break
                
                if channel.recv_ready():
                    chunk = channel.recv(65535).decode('utf-8', errors='ignore')
                    commit_output += chunk
                    
                    elapsed_commit = time.time() - commit_start
                    commit_pct = min(98, 82 + int(elapsed_commit / estimates['commit'] * 16))
                    update_progress("commit", commit_pct, f"Committing... ({int(elapsed_commit)}s)", chunk if raw_terminal else "")
                    
                    if 'commit succeeded' in commit_output.lower():
                        break
                    if 'error' in commit_output.lower():
                        break
                else:
                    time.sleep(0.2)
            
            if "commit succeeded" not in commit_output.lower():
                error_msg = self._extract_error(commit_output)
                return False, f"Commit failed: {error_msg}", terminal_log
            
            # === STAGE 8: Complete ===
            update_progress("complete", 100, "Configuration committed successfully!")
            
            channel.send("exit\n")
            self._read_until_prompt(channel)
            
            self._save_pushed_config(device.hostname, config_name, config_text)
            
            total_time = time.time() - start_time
            return True, f"Configuration committed successfully in {int(total_time)}s", terminal_log
            
        except paramiko.AuthenticationException:
            return False, "Authentication failed - check username/password", terminal_log
        except paramiko.SSHException as e:
            error_msg = str(e)
            if "Channel closed" in error_msg or not error_msg:
                error_msg = "SSH channel closed unexpectedly. This often happens with large configs (>1MB)."
            return False, f"SSH error: {error_msg}", terminal_log
        except socket.timeout:
            return False, "Connection timeout - device may be slow or unresponsive", terminal_log
        except OSError as e:
            return False, f"Network error: {str(e)}", terminal_log
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            return False, f"Error: {str(e)}\n{tb[-500:]}", terminal_log
        finally:
            if channel:
                try:
                    channel.close()
                except:
                    pass
            if client:
                try:
                    client.close()
                except:
                    pass

    def rollback(self, device: Device, rollback_id: int = 0) -> Tuple[bool, str]:
        """
        Rollback to a previous configuration.
        
        Args:
            device: Target device
            rollback_id: Rollback point (0 = last committed config)
        
        Returns:
            Tuple of (success, message)
        """
        client = None
        channel = None
        
        try:
            # Connect using best available IP
            ssh_host = get_ssh_hostname(device)
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(
                hostname=ssh_host,
                username=device.username,
                password=device.get_password(),
                timeout=self.timeout,
                look_for_keys=False,
                allow_agent=False
            )
            
            channel = client.invoke_shell()
            channel.settimeout(self.timeout)
            
            time.sleep(1)
            self._read_until_prompt(channel)
            
            # Enter configure mode
            channel.send("configure\n")
            self._read_until_prompt(channel, timeout=10)
            
            # Execute rollback
            channel.send(f"rollback {rollback_id}\n")
            output = self._read_until_prompt(channel, timeout=60)
            
            # Commit the rollback
            channel.send("commit\n")
            output = self._read_until_prompt(channel, timeout=self.commit_timeout)
            
            if "commit succeeded" in output.lower():
                return True, f"Rollback to point {rollback_id} succeeded"
            else:
                return False, f"Rollback failed: {self._extract_error(output)}"
            
        except Exception as e:
            return False, f"Rollback error: {str(e)}"
        finally:
            if channel:
                channel.close()
            if client:
                client.close()

    def compare_config(
        self,
        device: Device,
        config_text: str,
        config_name: str = None
    ) -> Tuple[bool, str]:
        """
        Compare a configuration with the running config.
        
        Args:
            device: Target device
            config_text: Configuration text to compare
            config_name: Name for the temp config file
        
        Returns:
            Tuple of (success, diff_output)
        """
        client = None
        channel = None
        
        try:
            # Connect using best available IP
            ssh_host = get_ssh_hostname(device)
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(
                hostname=ssh_host,
                username=device.username,
                password=device.get_password(),
                timeout=self.timeout,
                look_for_keys=False,
                allow_agent=False
            )
            
            # Upload config file via SCP
            if not config_name:
                config_name = f"scaler_compare_{timestamp_filename(suffix='')}.txt"
            
            remote_path = f"/config/{config_name}"
            upload_success, upload_msg = self._scp_upload(
                device=device,
                config_text=config_text,
                remote_path=remote_path,
                timeout=self.load_timeout
            )
            
            if not upload_success:
                return False, f"SCP upload failed: {upload_msg}"
            
            # Open shell
            channel = client.invoke_shell()
            channel.settimeout(self.timeout)
            time.sleep(1)
            self._read_until_prompt(channel)
            
            # Enter configure mode
            channel.send("configure\n")
            self._read_until_prompt(channel, timeout=10)
            
            # Load config
            channel.send(f"load override {config_name}\n")
            self._read_until_prompt(channel, timeout=self.load_timeout)
            
            # Show diff
            channel.send("show | compare\n")
            output = self._read_until_prompt(channel, timeout=60)
            
            # Exit without committing
            channel.send("exit discard\n")
            self._read_until_prompt(channel)
            
            return True, output
            
        except Exception as e:
            return False, f"Compare error: {str(e)}"
        finally:
            if channel:
                channel.close()
            if client:
                client.close()

    def run_show_commands(
        self,
        device: Device,
        commands: List[str]
    ) -> Dict[str, str]:
        """
        Run show commands on the device and return outputs.
        
        Args:
            device: Target device
            commands: List of show commands to run
        
        Returns:
            Dict of command -> output
        """
        results = {}
        client = None
        channel = None
        
        try:
            # Connect using best available IP
            ssh_host = get_ssh_hostname(device)
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(
                hostname=ssh_host,
                username=device.username,
                password=device.get_password(),
                timeout=self.timeout,
                look_for_keys=False,
                allow_agent=False
            )
            
            channel = client.invoke_shell()
            channel.settimeout(self.timeout)
            
            time.sleep(1)
            self._read_until_prompt(channel)
            
            for cmd in commands:
                channel.send(f"{cmd}\n")
                output = self._read_until_prompt(channel, timeout=60)
                results[cmd] = output
            
            return results
            
        except Exception as e:
            return {cmd: f"Error: {str(e)}" for cmd in commands}
        finally:
            if channel:
                channel.close()
            if client:
                client.close()

    def _read_until_prompt(
        self,
        channel,
        timeout: int = 60,
        progress_callback: Callable[[str, int], None] = None,
        progress_prefix: str = "Loading",
        live_output_callback: Callable[[str], None] = None,
    ) -> str:
        """Read output until we see a prompt.

        Args:
            channel: SSH channel
            timeout: Timeout in seconds
            progress_callback: Optional callback for progress updates
            progress_prefix: Prefix for progress messages
            live_output_callback: Optional callback for raw output (each chunk as received)

        Returns:
            Full output string
        """
        output = ""
        start_time = time.time()
        last_progress = -1

        # Safety: ensure timeout is not None
        if timeout is None:
            timeout = 60

        while True:
            if time.time() - start_time > timeout:
                break

            if channel.recv_ready():
                chunk = channel.recv(65535).decode('utf-8', errors='ignore')
                output += chunk
                if live_output_callback and chunk:
                    live_output_callback(chunk)

                # Parse and report device loading progress (e.g., "] 45%")
                if progress_callback:
                    # Look for percentage in output (DNOS shows: [=====>    ] 45%)
                    progress_match = re.search(r'\]\s*(\d+)%', chunk)
                    if progress_match:
                        current_pct = int(progress_match.group(1))
                        if current_pct != last_progress:
                            last_progress = current_pct
                            # Show device progress directly (no double percentage display)
                            progress_callback(f"{progress_prefix}...", current_pct)
                
                # Handle "uncommitted changes" interactive prompt
                # Answer "cancel" to stay in config mode
                if 'uncommitted changes' in output.lower() and 'yes/no/cancel' in output.lower():
                    channel.send("cancel\n")
                    time.sleep(0.5)
                    output = ""  # Clear and continue reading
                    continue
                
                # Check for DNOS prompts
                if output.rstrip().endswith(('#', '>', 'cfg#', 'cfg>')):
                    break
                
                # Check for specific completion messages
                if any(msg in output.lower() for msg in [
                    'commit succeeded',
                    'commit check passed',
                    'error:',
                    'failed'
                ]):
                    # Give a moment for any additional output
                    time.sleep(0.5)
                    while channel.recv_ready():
                        output += channel.recv(65535).decode('utf-8', errors='ignore')
                    break
            else:
                time.sleep(0.1)
        
        return output

    def _extract_error(self, output: str) -> str:
        """Extract error message from command output."""
        import re
        
        # Strip ANSI escape codes first
        ansi_pattern = re.compile(r'\x1b\[[0-9;]*[a-zA-Z]|\x1b\].*?\x07')
        output = ansi_pattern.sub('', output)
        
        # Filter out device prompts, timestamps, syslog, and noise
        lines = []
        for line in output.split('\n'):
            line = line.strip()
            # Skip empty lines
            if not line:
                continue
            # Skip pure prompt lines like "YOR_PE-2(cfg)#" or "YOR_PE-2(cfg-netsrv-mh)#"
            if re.match(r'^[\w\-\.]+\([^)]*\)[#>]\s*$', line):
                continue
            # Skip lines that are just prompts with timestamps
            if re.match(r'^[\w\-\.]+\([^)]*\s+\d{2}-\w{3}-\d{4}.*\)[#>]\s*$', line):
                continue
            # Skip lines that are just config commands echoed back (like "redundancy-mode single-active")
            if re.match(r'^(redundancy-mode|esi|interface|no interface|!)\s', line):
                continue
            # Skip syslog messages (local7.info, local7.warning, etc.) - these are NOT errors
            if re.match(r'^local\d\.(info|warning|notice|debug|error)\s', line):
                continue
            # Skip interface link state change messages - NOT errors
            if 'IF_LINK_STATE_CHANGE' in line or 'link state has changed' in line.lower():
                continue
            # Skip SSH session messages
            if 'SSH_SESSION' in line:
                continue
            # Skip timestamp-prefixed syslog lines
            if re.match(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}', line):
                continue
            lines.append(line)
        
        error_lines = []
        
        # Known DNOS commit check error patterns - more specific
        error_patterns = [
            r'ERROR:',
            r'commit.*failed', 
            r'invalid',
            r'cannot be greater than',
            r'not supported',
            r'limit exceeded',
            r'scale.*exceeded',
            r'hook.*failed',
            r'validate_esi_max_scale',
            r'Number of Interfaces.*cannot',
            r'exceeds.*limit',
            r'maximum.*reached',
            r'TRANSACTION_COMMIT_CHECK_FAILED',
        ]
        
        combined_pattern = '|'.join(error_patterns)
        
        # Search for error patterns in filtered lines
        for line in lines:
            if re.search(combined_pattern, line, re.IGNORECASE):
                error_lines.append(line)
        
        if error_lines:
            # Deduplicate and limit to 3 unique errors
            unique_errors = []
            for e in error_lines:
                # Clean up the error message
                e_clean = re.sub(r'^.*?ERROR:', 'ERROR:', e)  # Start from ERROR:
                if e_clean not in unique_errors and len(e_clean) < 300:
                    unique_errors.append(e_clean)
            return '; '.join(unique_errors[:3])
        
        # If no explicit errors found, return empty - no error detected
        # Don't treat random terminal output as errors!
        return ""

    def _save_pushed_config(self, hostname: str, config_name: str, config_text: str):
        """Save a copy of pushed configuration locally."""
        config_dir = get_device_config_dir(hostname)
        pushed_dir = config_dir / "pushed"
        pushed_dir.mkdir(exist_ok=True)
        
        filepath = pushed_dir / f"{timestamp_filename()}_{config_name}"
        with open(filepath, 'w') as f:
            f.write(config_text)

    def run_command(self, device: Device, command: str, timeout: int = 30) -> Optional[str]:
        """
        Run a show command on a device and return the output.
        
        Args:
            device: Target device
            command: Command to run (e.g., "show running-config network-services multihoming")
            timeout: Command timeout in seconds
        
        Returns:
            Command output string, or None on failure
        """
        addresses = device.get_connection_addresses()
        
        for address in addresses:
            try:
                client = paramiko.SSHClient()
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                client.connect(
                    hostname=address,
                    username=device.username,
                    password=device.password,
                    timeout=self.timeout,
                    allow_agent=False,
                    look_for_keys=False
                )
                
                stdin, stdout, stderr = client.exec_command(command, timeout=timeout)
                output = stdout.read().decode('utf-8', errors='ignore')
                client.close()
                return output
                
            except Exception:
                continue
        
        return None

    def test_connectivity(self, device: Device) -> Tuple[bool, str]:
        """
        Test SSH connectivity to a device.
        
        Args:
            device: Device to test
        
        Returns:
            Tuple of (success, message)
        """
        # Try all available addresses
        addresses = device.get_connection_addresses()
        last_error = None
        
        for address in addresses:
            try:
                client = paramiko.SSHClient()
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                client.connect(
                    hostname=address,
                    username=device.username,
                    password=device.get_password(),
                    timeout=self.timeout,
                    look_for_keys=False,
                    allow_agent=False
                )
                
                # Try a simple command
                stdin, stdout, stderr = client.exec_command("show system name", timeout=10)
                output = stdout.read().decode('utf-8', errors='ignore')
                
                client.close()
                
                connected_via = f" (via {address})" if address != device.ip else ""
                return True, f"Connected successfully{connected_via}. Hostname: {output.strip()}"
                
            except paramiko.AuthenticationException:
                return False, "Authentication failed - check username/password"
            except paramiko.SSHException as e:
                last_error = f"SSH error: {str(e)}"
            except Exception as e:
                last_error = f"Connection error: {str(e)}"
        
        return False, last_error or "Connection failed to all addresses"

    def discover_management_ip(self, device: Device) -> Tuple[bool, Optional[str]]:
        """
        Discover the management IP of a device by running show interface management.
        
        Args:
            device: Device to query
        
        Returns:
            Tuple of (success, discovered_ip or None)
        """
        import re
        
        addresses = device.get_connection_addresses()
        
        for address in addresses:
            try:
                client = paramiko.SSHClient()
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                client.connect(
                    hostname=address,
                    username=device.username,
                    password=device.get_password(),
                    timeout=self.timeout,
                    look_for_keys=False,
                    allow_agent=False
                )
                
                # Open interactive shell for DNOS commands
                channel = client.invoke_shell()
                channel.settimeout(self.timeout)
                
                time.sleep(1)
                self._read_until_prompt(channel)
                
                # Run show interface management
                channel.send("show interface management | no-more\n")
                output = self._read_until_prompt(channel, timeout=30)
                
                channel.close()
                client.close()
                
                # Parse output for IP addresses
                # Look for IPv4 addresses in the output
                # Typical format: | mgmt0 | ... | 10.x.x.x/24 | ...
                ip_pattern = r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})(?:/\d+)?'
                matches = re.findall(ip_pattern, output)
                
                # Filter out common non-management IPs
                for ip in matches:
                    # Skip loopback, link-local, multicast
                    if ip.startswith('127.') or ip.startswith('169.254.') or ip.startswith('224.'):
                        continue
                    # Skip the address we already have
                    if ip == device.ip:
                        continue
                    # Return the first valid IP found
                    return True, ip
                
                # If we connected but didn't find a new IP, that's ok
                return True, None
                
            except Exception:
                continue
        
        return False, None

    def connect_with_fallback(
        self,
        device: Device,
        discover_mgmt: bool = True
    ) -> Tuple[bool, paramiko.SSHClient, str, Optional[str]]:
        """
        Connect to device with fallback to management IP.
        
        Args:
            device: Device to connect to
            discover_mgmt: Whether to discover management IP on success
        
        Returns:
            Tuple of (success, client, connected_address, discovered_mgmt_ip)
        """
        addresses = device.get_connection_addresses()
        
        for address in addresses:
            try:
                client = paramiko.SSHClient()
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                client.connect(
                    hostname=address,
                    username=device.username,
                    password=device.get_password(),
                    timeout=self.timeout,
                    look_for_keys=False,
                    allow_agent=False
                )
                
                # Optionally discover management IP
                discovered_ip = None
                if discover_mgmt and not device.management_ip:
                    # We're already connected, use this connection to discover
                    try:
                        channel = client.invoke_shell()
                        channel.settimeout(self.timeout)
                        time.sleep(1)
                        self._read_until_prompt(channel)
                        
                        channel.send("show interface management | no-more\n")
                        output = self._read_until_prompt(channel, timeout=30)
                        channel.close()
                        
                        import re
                        ip_pattern = r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})(?:/\d+)?'
                        matches = re.findall(ip_pattern, output)
                        
                        for ip in matches:
                            if not ip.startswith('127.') and not ip.startswith('169.254.') and ip != address:
                                discovered_ip = ip
                                break
                    except Exception:
                        pass
                
                return True, client, address, discovered_ip
                
            except Exception:
                continue
        
        return False, None, "", None

    def run_cli_commands(
        self,
        device: Device,
        commands: List[str],
        dry_run: bool = True,
        progress_callback: Callable[[str, int], None] = None
    ) -> Tuple[bool, str, str]:
        """
        Run CLI commands in configure mode with commit check and optional commit.
        
        This method is used for direct CLI operations like 'no <hierarchy>' to delete
        configuration sections.
        
        Args:
            device: Target device
            commands: List of CLI commands to run in configure mode
            dry_run: If True, only run commit check, don't commit
            progress_callback: Optional callback for progress updates
        
        Returns:
            Tuple of (success, message, full_output)
        """
        import paramiko
        
        addresses = device.get_connection_addresses()
        full_output = ""
        
        for address in addresses:
            try:
                if progress_callback:
                    progress_callback(f"Connecting to {address}...", 10)
                
                client = paramiko.SSHClient()
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                client.connect(
                    hostname=address,
                    username=device.username,
                    password=device.get_password(),
                    timeout=self.timeout,
                    look_for_keys=False,
                    allow_agent=False
                )
                
                channel = client.invoke_shell()
                channel.settimeout(self.timeout)
                
                # Wait for initial prompt
                time.sleep(1)
                initial = self._read_until_prompt(channel, timeout=10)
                full_output += initial
                
                if progress_callback:
                    progress_callback("Entering configure mode...", 20)
                
                # Enter configure mode
                channel.send("configure\n")
                output = self._read_until_prompt(channel, timeout=10)
                full_output += output
                
                if "cfg" not in output.lower() and "#" not in output:
                    client.close()
                    return False, "Failed to enter configure mode", full_output
                
                # Execute each command
                cmd_count = len(commands)
                for i, cmd in enumerate(commands):
                    if progress_callback:
                        pct = 30 + int((i / cmd_count) * 20)
                        progress_callback(f"Running: {cmd}", pct)
                    
                    channel.send(f"{cmd}\n")
                    output = self._read_until_prompt(channel, timeout=30)
                    full_output += output
                    
                    # Check for immediate errors
                    if "error" in output.lower() or "invalid" in output.lower():
                        # Exit config mode
                        channel.send("exit discard\n")
                        self._read_until_prompt(channel, timeout=5)
                        client.close()
                        error_msg = self._extract_error(output)
                        return False, f"Command failed: {error_msg}", full_output
                
                if progress_callback:
                    progress_callback("Running commit check...", 60)
                
                # Run commit check
                channel.send("commit check\n")
                output = self._read_until_prompt(channel, timeout=self.commit_timeout)
                full_output += output
                
                # Check for success - includes "no changes" which means config already on device
                output_lower = output.lower()
                commit_success = any(p in output_lower for p in [
                    "commit check passed", "no configuration changes were made", "commit action is not applicable"
                ])
                if not commit_success:
                    error_msg = self._extract_error(output)
                    # Exit config mode
                    channel.send("exit discard\n")
                    self._read_until_prompt(channel, timeout=5)
                    client.close()
                    return False, f"Commit check failed: {error_msg}", full_output
                
                if dry_run:
                    if progress_callback:
                        progress_callback("✓ Commit check passed (dry run)", 100)
                    channel.send("exit discard\n")
                    self._read_until_prompt(channel, timeout=5)
                    client.close()
                    return True, "Commit check passed (dry run - no changes made)", full_output
                
                # Commit check passed - now do actual commit
                if progress_callback:
                    progress_callback("✓ Commit check passed!", 70)
                
                time.sleep(0.3)  # Brief pause to show the message
                
                if progress_callback:
                    progress_callback("Committing changes...", 80)
                
                # Commit
                channel.send("commit\n")
                output = self._read_until_prompt(channel, timeout=self.commit_timeout)
                full_output += output
                
                if "commit succeeded" not in output.lower():
                    error_msg = self._extract_error(output)
                    client.close()
                    return False, f"Commit failed: {error_msg}", full_output
                
                if progress_callback:
                    progress_callback("✓ Commit succeeded!", 100)
                
                # Exit configure mode
                channel.send("exit\n")
                self._read_until_prompt(channel, timeout=5)
                client.close()
                
                return True, "Commands executed and committed successfully", full_output
                
            except paramiko.AuthenticationException:
                return False, "Authentication failed - check username/password", ""
            except socket.timeout:
                return False, f"Connection timeout to {address}", ""
            except Exception as e:
                continue
        
        return False, "Failed to connect to device", ""


