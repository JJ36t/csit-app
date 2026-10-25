# -*- coding: utf-8 -*-
"""كتابة سجل التدقيق: من فعل ماذا، على أي كيان، وما تغيّر (قبل/بعد).

يُستدعى من العمليات الحساسة: إعادة ضبط الجهاز/كلمة المرور، الاستيراد، تغيير كلمة المرور.
"""
from typing import Any

from sqlalchemy.orm import Session

from app.models import AuditLog, User


def log_action(
    db: Session,
    *,
    actor: User | None,
    action: str,
    entity: str,
    entity_id: str,
    before: Any = None,
    after: Any = None,
    ip: str | None = None,
    commit: bool = False,
) -> AuditLog:
    row = AuditLog(
        actor_id=actor.id if actor is not None else None,
        action=action,
        entity=entity,
        entity_id=str(entity_id),
        before=before,
        after=after,
        ip=ip,
    )
    db.add(row)
    if commit:
        db.commit()
    return row
