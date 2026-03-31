from __future__ import annotations

from datetime import datetime, timezone
from math import ceil
from uuid import UUID

from sqlalchemy.orm import Session

from ..models import models
from ..core.schemas import RuleCreate, RuleUpdate


class RuleNotFound(Exception):
    pass


def list_rules(
    db: Session,
    *,
    device_id: UUID | None,
    is_enabled: bool | None,
    page: int,
    page_size: int,
):
    query = db.query(models.Rule)

    if device_id is not None:
        query = query.filter(models.Rule.device_id == str(device_id))

    if is_enabled is not None:
        query = query.filter(models.Rule.is_enabled == is_enabled)

    total = query.count()
    total_pages = max(1, ceil(total / page_size)) if page_size else 1

    items = (
        query.order_by(models.Rule.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    next_page = page + 1 if page * page_size < total else None
    prev_page = page - 1 if page > 1 else None

    return items, {
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": total_pages,
        "next_page": next_page,
        "prev_page": prev_page,
    }


def get_rule(db: Session, rule_id: UUID) -> models.Rule:
    rule = db.query(models.Rule).filter(models.Rule.id == str(rule_id)).first()
    if rule is None:
        raise RuleNotFound()
    return rule


def create_rule(db: Session, payload: RuleCreate) -> models.Rule:
    now = datetime.now(timezone.utc)
    rule = models.Rule(
        name=payload.name,
        description=payload.description,
        device_id=str(payload.device_id),
        condition=payload.condition.model_dump(),
        action_config=[
            item.model_dump(exclude_none=True) for item in payload.action_config
        ],
        is_enabled=payload.is_enabled,
        created_at=now,
        updated_at=now,
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


def update_rule(db: Session, rule: models.Rule, payload: RuleUpdate) -> models.Rule:
    if payload.name is not None:
        rule.name = payload.name
    if payload.description is not None:
        rule.description = payload.description
    if payload.device_id is not None:
        rule.device_id = str(payload.device_id)
    if payload.condition is not None:
        rule.condition = payload.condition.model_dump()
    if payload.action_config is not None:
        rule.action_config = [
            item.model_dump(exclude_none=True) for item in payload.action_config
        ]
    if payload.is_enabled is not None:
        rule.is_enabled = payload.is_enabled

    rule.updated_at = datetime.now(timezone.utc)
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


def delete_rule(db: Session, rule: models.Rule) -> None:
    db.delete(rule)
    db.commit()


def set_rule_enabled(db: Session, rule: models.Rule, enabled: bool) -> models.Rule:
    rule.is_enabled = enabled
    rule.updated_at = datetime.now(timezone.utc)
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule
