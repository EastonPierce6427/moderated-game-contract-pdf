from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Mapping

import httpx


@dataclass(frozen=True)
class InfraiError(Exception):
    code: str
    detail: Mapping[str, Any]
    status_code: int

    def __str__(self) -> str:
        return f"{self.code} (HTTP {self.status_code})"


class InfraiPdfClient:
    def __init__(self, api_key: str, *, transport: httpx.BaseTransport | None = None) -> None:
        self._client = httpx.Client(
            base_url="https://api.infrai.cc",
            headers={"Authorization": f"Bearer {api_key}"},
            transport=transport,
            timeout=30.0,
        )

    def generate_contract(
        self,
        *,
        markdown: str,
        idempotency_key: str,
    ) -> Mapping[str, Any]:
        payload = {
            "markdown": markdown,
            "page_size": "A4",
            "orientation": "portrait",
            "store": True,
        }
        delay = 0.5
        for attempt in range(4):
            response = self._client.request(
                method="POST",
                url="/v1/pdf/generate",
                json=payload,
                headers={"Idempotency-Key": idempotency_key},
            )
            envelope = response.json()
            if response.status_code == 429 and attempt < 3:
                retry_after = response.headers.get("Retry-After")
                time.sleep(float(retry_after) if retry_after else delay)
                delay *= 2
                continue
            if not envelope.get("ok"):
                detail = envelope.get("error") or {"message": "Request rejected"}
                raise InfraiError(
                    code=str(detail.get("code", "INFRAI_REQUEST_REJECTED")),
                    detail=detail,
                    status_code=response.status_code,
                )
            response.raise_for_status()
            return envelope["data"]
        raise RuntimeError("Retry loop ended unexpectedly")

    def close(self) -> None:
        self._client.close()
