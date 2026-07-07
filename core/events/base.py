from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Dict, Optional
import uuid


@dataclass(frozen=True)
class Event:
    """Immutable domain event object.

    Fields follow architecture doc: UUID, type, origin, tenant, user, timestamp and payload.
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    origin: Optional[str] = None
    tenant_id: Optional[str] = None
    user_id: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Event":
        return Event(
            id=data.get("id") or str(uuid.uuid4()),
            type=data.get("type", ""),
            payload=data.get("payload", {}),
            origin=data.get("origin"),
            tenant_id=data.get("tenant_id"),
            user_id=data.get("user_id"),
            created_at=data.get("created_at") or (datetime.utcnow().isoformat() + "Z"),
        )
