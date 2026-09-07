import logging


def test_public_preview_event_emits_only_approved_dimensions(client, caplog):
    private_value = "candidate@example.com"

    with caplog.at_level(logging.INFO):
        response = client.post(
            "/api/v1/public-preview/events",
            json={
                "event_name": "form_validation_failure",
                "form_location": "hero",
                "validation_category": "consent",
            },
        )

    assert response.status_code == 204
    assert private_value not in caplog.text
    record = next(
        item for item in caplog.records if item.message == "Public preview analytics event"
    )
    assert record.event_name == "form_validation_failure"
    assert record.form_location == "hero"
    assert record.validation_category == "consent"


def test_public_preview_event_rejects_unknown_or_pii_fields(client):
    response = client.post(
        "/api/v1/public-preview/events",
        json={
            "event_name": "form_success",
            "form_location": "final_cta",
            "email": "candidate@example.com",
        },
    )

    assert response.status_code == 422


def test_scroll_depth_requires_an_approved_threshold(client):
    response = client.post(
        "/api/v1/public-preview/events",
        json={"event_name": "scroll_depth", "scroll_depth": 33},
    )

    assert response.status_code == 422
