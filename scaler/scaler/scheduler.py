"""Periodic configuration extraction scheduler."""

import logging
from datetime import datetime, timezone
from typing import Callable, Optional, List
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

import os
from pathlib import Path

from .device_manager import DeviceManager
from .config_extractor import ConfigExtractor
from .config_parser import ConfigParser
from .models import DeviceConfig
from .utils import get_device_config_dir
import re


def get_local_now() -> datetime:
    """Get current time in local timezone (timezone-aware)."""
    return datetime.now().astimezone()


# Configure logging with local timezone
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logging.Formatter.converter = lambda *args: datetime.now().astimezone().timetuple()
logger = logging.getLogger(__name__)


class ConfigSyncScheduler:
    """Schedule periodic configuration extraction from devices."""

    def __init__(
        self,
        device_manager: DeviceManager = None,
        config_extractor: ConfigExtractor = None,
        interval_minutes: int = 60
    ):
        """
        Initialize the scheduler.
        
        Args:
            device_manager: DeviceManager instance
            config_extractor: ConfigExtractor instance
            interval_minutes: Sync interval in minutes
        """
        self.dm = device_manager or DeviceManager()
        self.extractor = config_extractor or ConfigExtractor()
        self.parser = ConfigParser()
        self.interval_minutes = interval_minutes
        
        self.scheduler = BackgroundScheduler()
        self.job = None
        self.running = False
        
        # Callbacks
        self.on_sync_start: Optional[Callable[[str], None]] = None
        self.on_sync_complete: Optional[Callable[[str, bool, str], None]] = None
        self.on_sync_error: Optional[Callable[[str, str], None]] = None

    def start(self):
        """Start the scheduler."""
        if self.running:
            logger.warning("Scheduler is already running")
            return
        
        # Add the sync job
        self.job = self.scheduler.add_job(
            self.sync_all_devices,
            IntervalTrigger(minutes=self.interval_minutes),
            id='config_sync',
            name='Configuration Sync',
            replace_existing=True
        )
        
        self.scheduler.start()
        self.running = True
        logger.info(f"Scheduler started. Sync interval: {self.interval_minutes} minutes")

    def stop(self):
        """Stop the scheduler."""
        if not self.running:
            return
        
        self.scheduler.shutdown(wait=False)
        self.running = False
        logger.info("Scheduler stopped")

    def set_interval(self, minutes: int):
        """
        Update the sync interval.
        
        Args:
            minutes: New interval in minutes
        """
        self.interval_minutes = minutes
        
        if self.running and self.job:
            self.job.reschedule(IntervalTrigger(minutes=minutes))
            logger.info(f"Sync interval updated to {minutes} minutes")

    def sync_all_devices(self):
        """Sync configurations from all devices."""
        devices = self.dm.list_devices()
        
        if not devices:
            logger.info("No devices to sync")
            return
        
        logger.info(f"Starting sync for {len(devices)} devices")
        
        results = []
        for device in devices:
            success, message = self.sync_device(device.id)
            results.append({
                "device_id": device.id,
                "hostname": device.hostname,
                "success": success,
                "message": message
            })
        
        # Log summary
        successful = sum(1 for r in results if r["success"])
        logger.info(f"Sync complete. {successful}/{len(devices)} devices synced successfully")
        
        return results

    def _load_operational_data(self, hostname: str) -> dict:
        """
        Load operational data from bash-generated operational.json file.
        
        Args:
            hostname: Device hostname
        
        Returns:
            Dict with operational data (router_id, local_as, igp, bgp_neighbors, etc.)
        """
        import json
        config_dir = get_device_config_dir(hostname)
        ops_file = config_dir / "operational.json"
        
        if not ops_file.exists():
            return {}
        
        try:
            with open(ops_file) as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load operational data for {hostname}: {e}")
            return {}

    def _load_config_from_file(self, device) -> DeviceConfig:
        """
        Load configuration from existing running.txt file (populated by bash script).
        
        Args:
            device: Device object
        
        Returns:
            DeviceConfig if file exists and is valid, None otherwise
        """
        config_dir = get_device_config_dir(device.hostname)
        config_file = config_dir / "running.txt"
        
        if not config_file.exists():
            return None
        
        try:
            raw_config = config_file.read_text()
            if not raw_config or len(raw_config) < 100:  # Sanity check
                return None
            
            return DeviceConfig(
                device_id=device.id,
                hostname=device.hostname,
                extracted_at=get_local_now(),
                raw_config=raw_config
            )
        except Exception as e:
            logger.warning(f"Failed to load config from file for {device.hostname}: {e}")
            return None

    def sync_device(self, device_id: str, use_cached_config: bool = True) -> tuple:
        """
        Sync configuration from a single device with enhanced summary.
        
        Args:
            device_id: Device identifier
            use_cached_config: If True, use existing running.txt from bash script
        
        Returns:
            Tuple of (success, message)
        """
        device = self.dm.get_device(device_id)
        if not device:
            return False, f"Device {device_id} not found"
        
        logger.info(f"Syncing {device.hostname}...")
        
        if self.on_sync_start:
            self.on_sync_start(device.hostname)
        
        try:
            # Try to load from cached file first (populated by bash script)
            config = None
            if use_cached_config:
                config = self._load_config_from_file(device)
                if config:
                    logger.info(f"{device.hostname}: Using cached config from running.txt")
            
            # Fall back to SSH extraction if no cached config
            if not config:
                config = self.extractor.extract_running_config(device, save_to_db=False)
            
            if not config or not config.raw_config or len(config.raw_config) < 100:
                message = "No configuration received"
                if self.on_sync_error:
                    self.on_sync_error(device.hostname, message)
                return False, message
            
            # Update last sync time (using local timezone)
            self.dm.update_device(device.id, last_sync=get_local_now())
            
            # Parse configuration
            parsed = self.parser.parse(config.raw_config)
            
            # Load operational data from bash-generated file (more reliable than SSH commands)
            operational_data = self._load_operational_data(device.hostname)
            
            # Generate enhanced summaries
            # ISIS summary
            if operational_data and operational_data.get("isis_interfaces"):
                config.isis_summary = self.parser.parse_isis_interfaces(
                    operational_data["isis_interfaces"]
                )
            
            # OSPF summary
            if operational_data and operational_data.get("ospf_interfaces"):
                config.ospf_summary = self.parser.parse_ospf_interfaces(
                    operational_data["ospf_interfaces"],
                    operational_data.get("ospf_interfaces_detail")
                )
            
            # BGP AS number
            if operational_data and operational_data.get("bgp_summary"):
                bgp_info = self.parser.parse_bgp_summary(operational_data["bgp_summary"])
                config.bgp_as = bgp_info.get("local_as")
            elif parsed.get("protocols", {}).get("bgp"):
                config.bgp_as = parsed["protocols"]["bgp"].get("local_as")
            
            # VLAN summary
            vlan_info = self.parser.get_vlan_summary(parsed)
            config.vlan_range = vlan_info.get("range")
            
            # Interface summary (pass operational data for UP counts)
            config.interface_summary = self.parser.get_interface_type_summary(parsed, operational_data)
            
            # Generate detailed sectioned summary for running.txt header
            config.enhanced_summary = self.parser.generate_history_header(
                device.hostname,
                parsed, 
                config.raw_config, 
                operational_data
            )
            
            # Now save the config with all the enhanced data
            self.extractor._save_config(device.hostname, config)
            
            # Use enhanced summary as the message
            message = config.enhanced_summary or self._generate_basic_summary(parsed, config.raw_config)
            
            logger.info(f"{device.hostname}: {message}")
            
            if self.on_sync_complete:
                self.on_sync_complete(device.hostname, True, message)
            
            return True, message
                
        except Exception as e:
            message = str(e)
            logger.error(f"{device.hostname}: Sync failed - {message}")
            
            if self.on_sync_error:
                self.on_sync_error(device.hostname, message)
            
            return False, message

    def _generate_basic_summary(self, parsed: dict, raw_config: str) -> str:
        """Generate a basic summary when enhanced summary is not available."""
        iface_count = self.parser.get_interface_count(parsed)
        svc_count = self.parser.get_service_count(raw_config)
        return f"Synced: {iface_count['total']} interfaces, {svc_count['total']} services"

    def get_next_run_time(self) -> Optional[datetime]:
        """Get the next scheduled run time."""
        if self.job:
            return self.job.next_run_time
        return None

    def get_status(self) -> dict:
        """Get scheduler status."""
        return {
            "running": self.running,
            "interval_minutes": self.interval_minutes,
            "next_run": self.get_next_run_time(),
            "job_count": len(self.scheduler.get_jobs()) if self.running else 0
        }

    def trigger_sync_now(self, device_id: str = None) -> List[dict]:
        """
        Trigger an immediate sync.
        
        Args:
            device_id: Optional specific device to sync, or all if None
        
        Returns:
            List of sync results
        """
        if device_id:
            success, message = self.sync_device(device_id)
            return [{"device_id": device_id, "success": success, "message": message}]
        else:
            return self.sync_all_devices()


class SyncDaemon:
    """Run the config sync scheduler as a background service."""

    def __init__(self, interval_minutes: int = 60):
        """
        Initialize the sync daemon.
        
        Args:
            interval_minutes: Sync interval in minutes
        """
        self.scheduler = ConfigSyncScheduler(interval_minutes=interval_minutes)

    def run(self):
        """Run the daemon (blocking)."""
        import signal
        import time
        
        def shutdown(signum, frame):
            logger.info("Received shutdown signal")
            self.scheduler.stop()
        
        # Register signal handlers
        signal.signal(signal.SIGINT, shutdown)
        signal.signal(signal.SIGTERM, shutdown)
        
        # Start scheduler
        self.scheduler.start()
        
        # Run initial sync
        logger.info("Running initial sync...")
        self.scheduler.sync_all_devices()
        
        # Keep running
        try:
            while self.scheduler.running:
                time.sleep(1)
        except (KeyboardInterrupt, SystemExit):
            self.scheduler.stop()

    def start_background(self):
        """Start the scheduler in background (non-blocking)."""
        self.scheduler.start()
        return self.scheduler

    def stop(self):
        """Stop the daemon."""
        self.scheduler.stop()


def run_sync_daemon(interval_minutes: int = 60):
    """
    Run the sync daemon as a standalone process.
    
    Args:
        interval_minutes: Sync interval in minutes
    """
    daemon = SyncDaemon(interval_minutes=interval_minutes)
    daemon.run()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="SCALER Config Sync Daemon")
    parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="Sync interval in minutes (default: 60)"
    )
    
    args = parser.parse_args()
    
    logger.info(f"Starting SCALER Config Sync Daemon (interval: {args.interval} minutes)")
    run_sync_daemon(args.interval)



