#Resource monitoring utility for cloud deployments

import psutil
import threading
import time
import logging
from typing import Dict, Any

log = logging.getLogger(__name__)

class CloudResourceMonitor:
    """Monitor and manage resources in cloud environment"""
    
    def __init__(self):
        self.monitoring = False
        self.stats = {}
    
    def start_monitoring(self):
        if not self.monitoring:
            self.monitoring = True
            threading.Thread(target=self._monitor_loop, daemon=True).start()
    
    def _monitor_loop(self):
        while self.monitoring:
            try:
                process = psutil.Process()
                memory_mb = process.memory_info().rss / 1024 / 1024
                thread_count = threading.active_count()
                
                # Log warnings for high resource usage
                if memory_mb > 1000:  # 1GB
                    log.warning(f"High memory usage: {memory_mb:.2f}MB")
                if thread_count > 15:
                    log.warning(f"High thread count: {thread_count}")
                
                self.stats = {
                    'memory_mb': memory_mb,
                    'thread_count': thread_count,
                    'timestamp': time.time()
                }
                
                time.sleep(30)  # Check every 30 seconds
            except Exception as e:
                log.error(f"Resource monitoring error: {e}")
                time.sleep(60)
    
    def stop_monitoring(self):
        self.monitoring = False

# Global monitor instance
resource_monitor = CloudResourceMonitor()