from datadog import initialize, api
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class DatadogTelemetry:
    """Datadog telemetry and metrics client."""
    
    def __init__(self, api_key: str, app_key: str, site: str = "datadoghq.com"):
        """Initialize Datadog client."""
        self.api_key = api_key
        self.app_key = app_key
        self.site = site
        self.enabled = bool(api_key and app_key)
        
        if self.enabled:
            initialize(
                api_key=api_key,
                app_key=app_key,
                api_host=f"https://api.{site}"
            )
    
    def send_metric(self, metric_name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Send metric to Datadog."""
        if not self.enabled:
            return
        
        try:
            tag_list = [f"{k}:{v}" for k, v in (tags or {}).items()]
            api.Metric.send(
                metric=metric_name,
                points=value,
                tags=tag_list
            )
        except Exception as e:
            logger.warning(f"Failed to send metric {metric_name}: {str(e)}")
    
    def send_event(self, title: str, text: str, alert_type: str = "info", tags: Optional[Dict[str, str]] = None):
        """Send event to Datadog."""
        if not self.enabled:
            return
        
        try:
            tag_list = [f"{k}:{v}" for k, v in (tags or {}).items()]
            api.Event.create(
                title=title,
                text=text,
                alert_type=alert_type,
                tags=tag_list
            )
        except Exception as e:
            logger.warning(f"Failed to send event: {str(e)}")