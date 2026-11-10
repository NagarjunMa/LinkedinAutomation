import json
import logging

from app.core.enhanced_logging import RailwayOptimizedFormatter


def test_public_preview_event_emits_only_approved_dimensions(client, caplog, monkeypatch):
    with caplog.at_level(logging.INFO):
        response = client.post(
            "/api/v1/public-preview/events",
            json={
                "event_name": "form_validation_failure",
                "form_location": "hero",
                "validation_category": "consent",
                "scroll_depth": 25,
            },
        )

    assert response.status_code == 204
    record = next(
        item for item in caplog.records if item.message == "Public preview analytics event"
    )
    record_with_private_extras = logging.makeLogRecord({
        **vars(record),
        "email": "candidate@example.com",
        "target_role": "Private role",
        "communication_challenge": "Private free text",
        "consent_granted": False,
    })
    monkeypatch.setenv("RAILWAY_DEPLOYMENT_ID", "test-deployment")
    formatted = json.loads(RailwayOptimizedFormatter().format(record_with_private_extras))
    assert set(formatted) == {
        "timestamp", "level", "logger", "message", "module", "function", "line",
        "railway_deployment", "railway_environment", "service_name", "environment",
        "request_id", "event_name", "form_location", "validation_category",
    }
    assert formatted["event_name"] == "form_validation_failure"
    assert formatted["form_location"] == "hero"
    assert formatted["validation_category"] == "consent"


def test_public_preview_scroll_event_keeps_numeric_depth(client, caplog):
    with caplog.at_level(logging.INFO):
        response = client.post(
            "/api/v1/public-preview/events",
            json={
                "event_name": "scroll_depth",
                "scroll_depth": 75,
                "form_location": "hero",
                "validation_category": "consent",
            },
        )
    assert response.status_code == 204
    record = next(item for item in caplog.records if item.message == "Public preview analytics event")
    formatted = json.loads(RailwayOptimizedFormatter().format(record))
    assert formatted["event_name"] == "scroll_depth"
    assert formatted["scroll_depth"] == 75
    assert "form_location" not in formatted
    assert "validation_category" not in formatted


def test_public_preview_success_event_ignores_inapplicable_dimensions(client, caplog):
    with caplog.at_level(logging.INFO):
        response = client.post(
            "/api/v1/public-preview/events",
            json={
                "event_name": "form_success",
                "form_location": "final_cta",
                "validation_category": "consent",
                "scroll_depth": 25,
            },
        )
    assert response.status_code == 204
    record = next(item for item in caplog.records if item.message == "Public preview analytics event")
    formatted = json.loads(RailwayOptimizedFormatter().format(record))
    assert formatted["event_name"] == "form_success"
    assert formatted["form_location"] == "final_cta"
    assert "validation_category" not in formatted
    assert "scroll_depth" not in formatted


def test_public_preview_event_rejects_unknown_or_pii_fields(client, caplog):
    with caplog.at_level(logging.INFO):
        response = client.post(
            "/api/v1/public-preview/events",
            json={
                "event_name": "form_success",
                "form_location": "final_cta",
                "email": "candidate@example.com",
            },
        )

    assert response.status_code == 422
    assert all(record.message != "Public preview analytics event" for record in caplog.records)
    formatter = RailwayOptimizedFormatter()
    assert all("candidate@example.com" not in formatter.format(record) for record in caplog.records)


def test_unrelated_railway_logs_do_not_include_analytics_extras():
    record = logging.makeLogRecord({
        "name": "app.other",
        "msg": "Public preview analytics event",
        "event_name": "candidate@example.com",
        "form_location": "hero",
    })
    formatted = json.loads(RailwayOptimizedFormatter().format(record))
    assert "event_name" not in formatted
    assert "form_location" not in formatted


def test_scroll_depth_requires_an_approved_threshold(client):
    response = client.post(
        "/api/v1/public-preview/events",
        json={"event_name": "scroll_depth", "scroll_depth": 33},
    )

    assert response.status_code == 422
