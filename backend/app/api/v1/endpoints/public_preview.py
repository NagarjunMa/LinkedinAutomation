"""Privacy-safe analytics ingestion for the public promotional page."""

import logging

from fastapi import APIRouter, Request, Response, status

from app.schemas.public_preview import PublicPreviewEventCreate


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

    logger.info(
        "Public preview analytics event",
        extra={
            "request_id": getattr(request.state, "request_id", None),
            "event_name": payload.event_name.value,
            "form_location": (
                payload.form_location.value if payload.form_location else None
            ),
            "validation_category": (
                payload.validation_category.value
                if payload.validation_category
                else None
            ),
            "scroll_depth": payload.scroll_depth,
        },
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
