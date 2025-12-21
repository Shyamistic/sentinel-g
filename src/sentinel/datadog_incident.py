"""
SENTINEL-G Datadog Incidents API Client
Sends enriched incidents to Datadog.
"""

import requests
import json
from typing import Dict, Any, Optional
from src.core.config import settings


class DatadogIncidentClient:
    """
    Client for Datadog Incidents API v2.
    """

    def __init__(self):
        self.api_key = settings.datadog_api_key
        self.app_key = settings.datadog_app_key
        self.site = settings.datadog_site
        self.base_url = f"https://api.{self.site}/api/v2"

    def create_incident(self, incident: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Create a Datadog incident from enriched incident payload.
        """
        url = f"{self.base_url}/incidents"

        headers = {
            "DD-API-KEY": self.api_key,
            "DD-APPLICATION-KEY": self.app_key,
            "Content-Type": "application/json",
        }

        # Build payload for Datadog Incidents API v2
        payload = {
            "data": {
                "type": "incidents",
                "attributes": {
                    "title": incident.get("title", "Sentinel-G Incident"),
                    "severity": self._map_severity(incident.get("severity", "MEDIUM")),
                    "customer_impacts": [],
                    "fields": {
                        "state": {
                            "type": "incident_field_attributes",
                            "value": "open",
                        },
                        "detector": {
                            "type": "incident_field_attributes",
                            "value": "sentinel-g-automated",
                        },
                    },
                },
            }
        }

        # Add description as timeline event
        if incident.get("description"):
            payload["data"]["attributes"]["timeline_cells"] = [
                {
                    "type": "incident_timeline_cell",
                    "cell_type": "note",
                    "content": {
                        "type": "incident_note_content",
                        "content": incident.get("description"),
                    },
                    "important": True,
                }
            ]

        try:
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=10,
            )

            if response.status_code in [200, 201]:
                result = response.json()
                print(
                    f"[SENTINEL-G] Incident created: {result.get('data', {}).get('id', 'unknown')}"
                )
                return result

            else:
                print(
                    f"[SENTINEL-G] Failed to create incident. "
                    f"Status: {response.status_code}. Response: {response.text}"
                )
                return None

        except Exception as e:
            print(f"[SENTINEL-G] Error creating incident: {str(e)}")
            return None

    def create_metric(self, metric_name: str, value: float, tags: list = None) -> bool:
        """
        Submit custom metric to Datadog.
        """
        if tags is None:
            tags = []

        tags.append(f"service:{settings.datadog_service_name}")

        url = f"{self.base_url}/series"

        headers = {
            "DD-API-KEY": self.api_key,
            "Content-Type": "application/json",
        }

        payload = {
            "series": [
                {
                    "metric": metric_name,
                    "points": [
                        {
                            "timestamp": int(__import__("time").time()),
                            "value": value,
                        }
                    ],
                    "tags": tags,
                    "type": "gauge",
                }
            ]
        }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=5)
            return response.status_code in [200, 202]
        except Exception as e:
            print(f"[SENTINEL-G] Error submitting metric: {str(e)}")
            return False

    def _map_severity(self, severity_str: str) -> str:
        """Map internal severity to Datadog incident severity."""
        mapping = {
            "HIGH": "SEV-1",
            "MEDIUM": "SEV-2",
            "LOW": "SEV-3",
        }
        return mapping.get(severity_str, "SEV-3")


# Singleton instance for convenience
datadog_client = DatadogIncidentClient()


def create_datadog_incident(incident: Dict[str, Any]) -> bool:
    """
    Convenience function to create Datadog incident.
    """
    result = datadog_client.create_incident(incident)
    return result is not None


def emit_sentinel_metric(metric_name: str, value: float, tags: list = None) -> bool:
    """
    Convenience function to emit Sentinel-G metric to Datadog.
    """
    return datadog_client.create_metric(metric_name, value, tags)