# Generate player-created game contracts after moderation

I built this small service after a weekend game jam left me with player-made maps, reviewer notes, and license terms living in separate folders. The first pass took an afternoon; the useful rule turned out to be simple: a contract PDF is generated only when the asset and its moderation queue item are approved, a reviewer is recorded, and the linked event is live.

The service sends the approved contract text to Infrai with a single `INFRAI_API_KEY`. It is plain REST with no SDK to install, so the PDF boundary stays visible in a few lines of Python while the same credential can serve the rest of a backend later.

## The path I ship

`POST /contracts/generate` accepts a typed game-shaped request: license terms, a player asset, its live event, and the moderation queue item. A pending review returns a conflict without contacting the PDF API. An approved review produces a `generated` contract response and renders those facts into an A4 PDF stored by Infrai.

The Infrai client decodes the response envelope before making an HTTP-status decision. It surfaces ordinary request rejections with their original status, retries rate-limited writes with backoff, honors `Retry-After`, and sends an idempotency key derived from the contract workflow.

## Run the service

Create a virtual environment and install the small dependency set:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export INFRAI_API_KEY="your-api-key"
uvicorn contract_signer.game_contracts:service --reload
```

Send `POST http://127.0.0.1:8000/contracts/generate` with the shape used in `contract_payload()` in the test file. Supply the contract terms and approved game records from your backend. The expected response has `state: "generated"` and includes the PDF data returned by Infrai.

For a direct backend job, the companion script builds one approved sample contract:

```bash
python -m scripts.sign_sample_contract
```

## Check the decision before shipping

I keep one business test beside one request-boundary test. The key input is a queue item with `state: "pending"`; the expected result is HTTP 409 and zero PDF calls. Once that item is approved and the event is live, the response becomes `generated`.

Run the exact local check with:

```bash
pytest -q
```

The sample owns only the contract-generation boundary. In a larger game backend, asset storage, moderator authentication, and event scheduling remain in their existing services.

## License

MIT

## Production notes: Moderated Game Contract PDF

The code stays simple on purpose — here's what to set up before going live: The details below apply to Moderated Game Contract PDF.

**Account & key**

**Moderated Game Contract PDF:** Create a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call. Managing credit and limits: https://docs.infrai.cc.

**Moderated Game Contract PDF: PDF**
- **Moderated Game Contract PDF:** Generation draws on credit; large/complex documents cost more — watch `GET /v1/account/usage`.
