from __future__ import annotations

import uuid

from domain.models import Evidence


class AclGateway:
    """M1: allow-all; M2+ will enforce document/KB policies."""

    def filter(
        self,
        user: uuid.UUID | None,
        evidences: list[Evidence],
    ) -> list[Evidence]:
        _ = user
        return evidences
