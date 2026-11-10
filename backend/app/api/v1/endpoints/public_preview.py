"""Privacy-safe analytics ingestion for the public promotional page."""

import logging

from fastapi import APIRouter, Request, Response, status

from app.schemas.public_preview import PublicPreviewEventCreate, PublicPreviewEventName


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/public-preview", tags=["public-preview"])


@router.post(
    "/events",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
def capture_public_preview_event(
    payload: PublicPreviewEventCreate,
    request: Request,
) -> Response:
    """Emit enum-only funnel telemetry without visitor content or identifiers."""

    event_name = payload.event_name
    logger.info(
        "Public preview analytics event",
        extra={
            "request_id": getattr(request.state, "request_id", None),
            "event_name": event_name.value,
            "form_location": (
                payload.form_location.value
                if event_name is not PublicPreviewEventName.SCROLL_DEPTH and payload.form_location
                else None
            ),
            "validation_category": (
                payload.validation_category.value
                if event_name is PublicPreviewEventName.FORM_VALIDATION_FAILURE and payload.validation_category
                else None
            ),
            "scroll_depth": payload.scroll_depth if event_name is PublicPreviewEventName.SCROLL_DEPTH else None,
        },
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
