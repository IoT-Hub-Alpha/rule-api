from __future__ import annotations

from uuid import uuid4


def _rule_payload(device_id: str) -> dict:
    return {
        "name": "High Temperature",
        "description": "Trigger when temperature is high",
        "device_id": device_id,
        "condition": {"type": "leaf", "operator": "gt", "threshold": 75.0},
        "action_config": [{"type": "notification", "template_id": 101}],
        "is_enabled": True,
    }


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_rule_crud_flow(client):
    device_id = str(uuid4())
    payload = _rule_payload(device_id)

    create_response = client.post("/v1/rules/", json=payload)
    assert create_response.status_code == 201
    created = create_response.json()["data"]
    rule_id = created["id"]
    assert created["device_id"] == device_id
    assert created["name"] == payload["name"]
    assert created["is_enabled"] is True

    list_response = client.get("/v1/rules/")
    assert list_response.status_code == 200
    list_data = list_response.json()["data"]
    assert any(item["id"] == rule_id for item in list_data)

    get_response = client.get(f"/v1/rules/{rule_id}/")
    assert get_response.status_code == 200
    assert get_response.json()["data"]["id"] == rule_id

    update_response = client.patch(
        f"/v1/rules/{rule_id}/",
        json={"name": "Updated Rule", "is_enabled": False},
    )
    assert update_response.status_code == 200
    updated = update_response.json()["data"]
    assert updated["name"] == "Updated Rule"
    assert updated["is_enabled"] is False

    enable_response = client.post(f"/v1/rules/{rule_id}/enable")
    assert enable_response.status_code == 200
    assert enable_response.json()["data"]["is_enabled"] is True

    disable_response = client.post(f"/v1/rules/{rule_id}/disable")
    assert disable_response.status_code == 200
    assert disable_response.json()["data"]["is_enabled"] is False

    delete_response = client.delete(f"/v1/rules/{rule_id}/")
    assert delete_response.status_code == 204

    get_after_delete = client.get(f"/v1/rules/{rule_id}/")
    assert get_after_delete.status_code == 404


def test_list_rules_all(client):
    device_id = str(uuid4())
    payload = _rule_payload(device_id)

    create_response = client.post("/v1/rules/", json=payload)
    assert create_response.status_code == 201

    list_response = client.get("/v1/rules/all")
    assert list_response.status_code == 200
    list_data = list_response.json()["data"]
    assert any(item["device_id"] == device_id for item in list_data)
