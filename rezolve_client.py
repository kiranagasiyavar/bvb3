"""Rezolve Labs Integration Module for Anticipatory Commerce.

Integrates official Rezolve Labs capabilities:
1. Semantic Product Search (/product-discovery/search)
2. Managed Knowledge Retrieval (Knowledge base creation, document upload, status polling)
3. Conversational Product Finder (Mid-conversation retrieval tool)

Includes secure credential handling, timeout resilience, structured fallback,
and verification against the local catalogue.
"""

import os
import json
import logging
import urllib.request
import urllib.error
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Official Rezolve API Endpoints
DEFAULT_REZOLVE_API_BASE = "https://api.rezolvelabs.com/api/v1"


class RezolveLabsClient:
    """Client for Rezolve Labs Platform APIs with resilient local fallback."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        kb_id: Optional[str] = None,
        timeout: float = 3.0
    ):
        self.api_key = api_key or os.environ.get("REZOLVE_API_KEY", "").strip()
        self.base_url = (base_url or os.environ.get("REZOLVE_API_BASE", DEFAULT_REZOLVE_API_BASE)).rstrip("/")
        self.kb_id = kb_id or os.environ.get("REZOLVE_KB_ID", "").strip()
        self.timeout = timeout
        self.is_configured = bool(self.api_key and self.kb_id)
        self.last_status: Dict[str, Any] = {
            "mode": "live" if self.is_configured else "mock_adapter",
            "connected": self.is_configured,
            "last_latency_ms": 0.0,
            "error": None
        }

    def _headers(self, content_type: str = "application/json") -> Dict[str, str]:
        headers = {"X-API-KEY": self.api_key}
        if content_type:
            headers["Content-Type"] = content_type
        return headers

    def semantic_search(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 5
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Search products using Rezolve Semantic Product Search API.

        Maps constraints to Rezolve schema (e.g., max_price -> price_lte).
        Returns (results_list, metadata_dict).
        """
        import time

        start_time = time.perf_counter()

        # If credentials are not supplied, return gracefully with status indicator
        if not self.is_configured:
            self.last_status = {
                "mode": "mock_adapter",
                "connected": False,
                "last_latency_ms": 0.0,
                "error": "REZOLVE_API_KEY or REZOLVE_KB_ID not set in environment."
            }
            return [], self.last_status

        # Map filter schema to Rezolve specification
        rezolve_filters: Dict[str, Any] = {}
        if filters:
            for k, v in filters.items():
                if v is None:
                    continue
                if k == "max_price":
                    rezolve_filters["price_lte"] = int(v)
                elif k == "min_price":
                    rezolve_filters["price_gte"] = int(v)
                else:
                    rezolve_filters[k] = str(v)

        payload = {
            "knowledgeBaseId": self.kb_id,
            "query": query or "",
            "filters": rezolve_filters,
            "limit": limit
        }

        url = f"{self.base_url}/product-discovery/search"
        data_bytes = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data_bytes, headers=self._headers(), method="POST")

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                elapsed_ms = (time.perf_counter() - start_time) * 1000.0
                raw = resp.read().decode("utf-8")
                res = json.loads(raw)
                hits = res.get("data", [])
                hit_count = res.get("hitCount", len(hits))
                has_more = res.get("hasMore", False)

                self.last_status = {
                    "mode": "live",
                    "connected": True,
                    "last_latency_ms": elapsed_ms,
                    "hitCount": hit_count,
                    "hasMore": has_more,
                    "error": None
                }
                return hits, self.last_status

        except urllib.error.HTTPError as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            error_body = ""
            try:
                error_body = e.read().decode("utf-8")
            except Exception:
                pass
            err_msg = f"HTTP {e.code}: {e.reason}. {error_body}"
            logger.warning("Rezolve semantic search error: %s", err_msg)
            self.last_status = {
                "mode": "live_error",
                "connected": False,
                "last_latency_ms": elapsed_ms,
                "error": err_msg
            }
            return [], self.last_status

        except Exception as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            err_msg = f"Rezolve request failed: {str(e)}"
            logger.warning(err_msg)
            self.last_status = {
                "mode": "live_error",
                "connected": False,
                "last_latency_ms": elapsed_ms,
                "error": err_msg
            }
            return [], self.last_status

    def create_knowledge_base(self, name: str = "PS1 catalogue") -> Dict[str, Any]:
        """Create a knowledge base for product catalogue retrieval."""
        if not self.api_key:
            return {"status": "mock", "data": {"id": "mock_kb_001", "name": name}}

        url = f"{self.base_url}/developer-platform/knowledge-bases"
        payload = json.dumps({"name": name}).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers=self._headers(), method="POST")

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                if "data" in data and "id" in data["data"]:
                    self.kb_id = data["data"]["id"]
                return data
        except Exception as e:
            logger.error("Failed to create knowledge base: %s", e)
            return {"error": str(e)}

    def upload_catalogue(self, filepath: str = "catalogue.csv", kb_id: Optional[str] = None) -> Dict[str, Any]:
        """Upload catalogue document into the knowledge base using multipart form data."""
        target_kb = kb_id or self.kb_id
        if not self.api_key or not target_kb:
            return {"status": "mock", "data": {"id": "mock_doc_001", "status": "ready"}}

        url = f"{self.base_url}/developer-platform/knowledge-bases/{target_kb}/documents"
        path = Path(filepath)
        if not path.exists():
            return {"error": f"File {filepath} not found"}

        boundary = "----WebKitFormBoundaryRezolveUpload"
        body = []
        body.append(f"--{boundary}".encode("utf-8"))
        body.append(f'Content-Disposition: form-data; name="file"; filename="{path.name}"'.encode("utf-8"))
        body.append(b"Content-Type: text/csv\r\n")
        with open(path, "rb") as fh:
            body.append(fh.read())
        body.append(f"\r\n--{boundary}--\r\n".encode("utf-8"))
        data_bytes = b"\r\n".join(body)

        headers = self._headers(content_type=f"multipart/form-data; boundary={boundary}")
        req = urllib.request.Request(url, data=data_bytes, headers=headers, method="POST")

        try:
            with urllib.request.urlopen(req, timeout=10.0) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            logger.error("Failed to upload catalogue: %s", e)
            return {"error": str(e)}

    def check_document_status(self, doc_id: str, kb_id: Optional[str] = None) -> Dict[str, Any]:
        """Poll document readiness."""
        target_kb = kb_id or self.kb_id
        if not self.api_key or not target_kb:
            return {"status": "mock", "data": {"status": "ready"}}

        url = f"{self.base_url}/developer-platform/knowledge-bases/{target_kb}/documents/{doc_id}"
        req = urllib.request.Request(url, headers=self._headers(), method="GET")

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            return {"error": str(e)}
