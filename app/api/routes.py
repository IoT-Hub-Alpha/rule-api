from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from . import crud
from ..models import models
from ..db.db import get_db
from ..core.schemas import (
    RuleCreate,
    RuleListResponse,
    RuleListSimpleResponse,
    RuleOut,
    RuleResponse,
    RuleUpdate,
)

router = APIRouter(prefix="/rules", tags=["rules"])


def _to_rule_out(rule: models.Rule) -> RuleOut:
    return RuleOut(
        id=rule.id,
        device_id=rule.device_id,
        name=rule.name,
        description=rule.description,
        condition=rule.condition,
        action_config=rule.action_config,
        is_enabled=rule.is_enabled,
        last_triggered_at=rule.last_triggered_at,
        event_cooldown_until=rule.event_cooldown_until,
        created_at=rule.created_at,
        updated_at=rule.updated_at,
    )


@router.get("/", response_model=RuleListResponse)
def list_rules(
    device_id: UUID | None = Query(default=None),
    is_enabled: bool | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    items, pagination = crud.list_rules(
        db,
        device_id=device_id,
        is_enabled=is_enabled,
        page=page,
        page_size=page_size,
    )
    return {
        "data": [_to_rule_out(item) for item in items],
        "pagination": pagination,
    }


@router.get("/all", response_model=RuleListSimpleResponse)
def list_rules_all(
    device_id: UUID | None = Query(default=None),
    is_enabled: bool | None = Query(default=None),
    db: Session = Depends(get_db),
):
    items = crud.list_rules_all(
        db,
        device_id=device_id,
        is_enabled=is_enabled,
    )
    return {"data": [_to_rule_out(item) for item in items]}


@router.post("/", response_model=RuleResponse, status_code=201)
def create_rule(payload: RuleCreate, db: Session = Depends(get_db)):
    rule = crud.create_rule(db, payload)
    return {"data": _to_rule_out(rule)}


@router.get("/{rule_id}/", response_model=RuleResponse)
def get_rule(rule_id: UUID, db: Session = Depends(get_db)):
    try:
        rule = crud.get_rule(db, rule_id)
    except crud.RuleNotFound:
        raise HTTPException(status_code=404, detail="Rule not found")
    return {"data": _to_rule_out(rule)}


@router.patch("/{rule_id}/", response_model=RuleResponse)
def update_rule(rule_id: UUID, payload: RuleUpdate, db: Session = Depends(get_db)):
    try:
        rule = crud.get_rule(db, rule_id)
    except crud.RuleNotFound:
        raise HTTPException(status_code=404, detail="Rule not found")

    rule = crud.update_rule(db, rule, payload)
    return {"data": _to_rule_out(rule)}


@router.delete("/{rule_id}/", status_code=204)
def delete_rule(rule_id: UUID, db: Session = Depends(get_db)):
    try:
        rule = crud.get_rule(db, rule_id)
    except crud.RuleNotFound:
        raise HTTPException(status_code=404, detail="Rule not found")

    crud.delete_rule(db, rule)
    return None


@router.post("/{rule_id}/enable", response_model=RuleResponse)
def enable_rule(rule_id: UUID, db: Session = Depends(get_db)):
    try:
        rule = crud.get_rule(db, rule_id)
    except crud.RuleNotFound:
        raise HTTPException(status_code=404, detail="Rule not found")

    rule = crud.set_rule_enabled(db, rule, True)
    return {"data": _to_rule_out(rule)}


@router.post("/{rule_id}/disable", response_model=RuleResponse)
def disable_rule(rule_id: UUID, db: Session = Depends(get_db)):
    try:
        rule = crud.get_rule(db, rule_id)
    except crud.RuleNotFound:
        raise HTTPException(status_code=404, detail="Rule not found")

    rule = crud.set_rule_enabled(db, rule, False)
    return {"data": _to_rule_out(rule)}
