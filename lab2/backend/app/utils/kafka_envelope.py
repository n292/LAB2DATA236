from datetime import datetime, timezone
from uuid import uuid4


def build_event(
    event_type: str,
    actor_id: str,
    entity_type: str,
    entity_id: str,
    payload: dict,
    trace_id: str | None = None,
    idempotency_key: str | None = None,
):
    return {
        "event_type": event_type,
        "trace_id": trace_id or str(uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "actor_id": actor_id,
        "entity": {"entity_type": entity_type, "entity_id": entity_id},
        "payload": payload,
        "idempotency_key": idempotency_key or str(uuid4()),
    }
