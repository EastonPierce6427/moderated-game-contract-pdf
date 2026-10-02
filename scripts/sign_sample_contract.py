from __future__ import annotations

import json
import os

from contract_signer.game_contracts import (
    AssetKind,
    ContractGenerationRequest,
    LiveEvent,
    ModerationQueueItem,
    ModerationState,
    PlayerAsset,
)
from contract_signer.infrai_pdf import InfraiPdfClient


def main() -> None:
    request = ContractGenerationRequest(
        contract_id="contract-crystal-cove-7",
        license_terms="The creator licenses this map for the Summer Cup event.",
        asset=PlayerAsset(
            asset_id="asset-crystal-cove",
            player_id="player-1042",
            kind=AssetKind.MAP,
            moderation_state=ModerationState.APPROVED,
        ),
        event=LiveEvent(event_id="summer-cup", title="Summer Cup", is_live=True),
        moderation=ModerationQueueItem(
            queue_id="queue-882",
            reviewer_id="mod-17",
            state=ModerationState.APPROVED,
        ),
    )
    client = InfraiPdfClient(os.environ["INFRAI_API_KEY"])
    try:
        result = client.generate_contract(
            markdown=(
                f"# Player Asset License\n\nAsset: {request.asset.asset_id}\n\n"
                f"Event: {request.event.title}\n\n## Terms\n\n{request.license_terms}"
            ),
            idempotency_key=request.contract_id,
        )
    finally:
        client.close()
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
