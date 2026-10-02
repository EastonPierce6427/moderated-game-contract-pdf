from fastapi.testclient import TestClient

from contract_signer.game_contracts import create_service


class RecordingGenerator:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def generate_contract(self, **payload: object) -> dict[str, str]:
        self.calls.append(payload)
        return {"document_id": "signed-contract-7", "status": "signed"}


def contract_payload() -> dict[str, object]:
    return {
        "contract_id": "contract-7",
        "license_terms": "The creator licenses this map for the named event.",
        "asset": {
            "asset_id": "asset-44",
            "player_id": "player-12",
            "kind": "map",
            "moderation_state": "approved",
        },
        "event": {"event_id": "event-3", "title": "Creator Cup", "is_live": True},
        "moderation": {
            "queue_id": "queue-9",
            "reviewer_id": "moderator-5",
            "state": "pending",
        },
    }


def test_pending_moderation_blocks_generation() -> None:
    generator = RecordingGenerator()
    response = TestClient(create_service(generator)).post("/contracts/generate", json=contract_payload())

    assert response.status_code == 409
    assert response.json()["detail"] == "The moderation queue item must be approved before contract generation"
    assert generator.calls == []


def test_approved_live_asset_gets_contract_pdf() -> None:
    generator = RecordingGenerator()
    payload = contract_payload()
    payload["moderation"]["state"] = "approved"  # type: ignore[index]

    response = TestClient(create_service(generator)).post("/contracts/generate", json=payload)

    assert response.status_code == 200
    assert response.json()["state"] == "generated"
    assert "asset-44" in generator.calls[0]["markdown"]
