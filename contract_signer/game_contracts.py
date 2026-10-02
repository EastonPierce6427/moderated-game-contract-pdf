from __future__ import annotations

import hashlib
import os
from enum import Enum
from typing import Any, Mapping

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .infrai_pdf import InfraiError, InfraiPdfClient


class AssetKind(str, Enum):
    SKIN = "skin"
    MAP = "map"
    AUDIO = "audio"


class ModerationState(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class PlayerAsset(BaseModel):
    asset_id: str
    player_id: str
    kind: AssetKind
    moderation_state: ModerationState


class LiveEvent(BaseModel):
    event_id: str
    title: str
    is_live: bool


class ModerationQueueItem(BaseModel):
    queue_id: str
    reviewer_id: str | None = None
    state: ModerationState


class ContractGenerationRequest(BaseModel):
    contract_id: str
    license_terms: str
    asset: PlayerAsset
    event: LiveEvent
    moderation: ModerationQueueItem


class GeneratedContract(BaseModel):
    contract_id: str
    state: str
    pdf_document: Mapping[str, Any]


def generation_blocker(request: ContractGenerationRequest) -> str | None:
    if request.asset.moderation_state != ModerationState.APPROVED:
        return "The player asset must be approved before contract generation"
    if request.moderation.state != ModerationState.APPROVED:
        return "The moderation queue item must be approved before contract generation"
    if not request.moderation.reviewer_id:
        return "An approved queue item must name its reviewer"
    if not request.event.is_live:
        return "The linked game event must be live before contract generation"
    return None


def create_service(client: InfraiPdfClient | None = None) -> FastAPI:
    app = FastAPI(title="Game Contract PDF Generator")

    @app.post("/contracts/generate", response_model=GeneratedContract)
    def generate_game_contract(request: ContractGenerationRequest) -> GeneratedContract:
        blocker = generation_blocker(request)
        if blocker:
            raise HTTPException(status_code=409, detail=blocker)

        active_client = client or InfraiPdfClient(os.environ["INFRAI_API_KEY"])
        request_key = hashlib.sha256(
            f"{request.contract_id}:{request.asset.asset_id}:{request.moderation.queue_id}".encode()
        ).hexdigest()
        try:
            document = active_client.generate_contract(
                markdown=(
                    f"# Player Asset License\n\n"
                    f"Contract: {request.contract_id}\n\n"
                    f"Asset: {request.asset.asset_id} ({request.asset.kind.value})\n\n"
                    f"Player: {request.asset.player_id}\n\n"
                    f"Event: {request.event.title} ({request.event.event_id})\n\n"
                    f"Reviewer: {request.moderation.reviewer_id}\n\n"
                    f"## Terms\n\n{request.license_terms}"
                ),
                idempotency_key=request_key,
            )
        except InfraiError as error:
            status = error.status_code if 400 <= error.status_code < 500 else 502
            raise HTTPException(status_code=status, detail=dict(error.detail)) from error
        finally:
            if client is None:
                active_client.close()

        return GeneratedContract(
            contract_id=request.contract_id,
            state="generated",
            pdf_document=document,
        )

    return app


service = create_service()
