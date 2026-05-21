"""Compatibility shim — will be deleted in Phase 5.

New code should import from:
  - app.schemas.resume_v2    (Phase 1 structured resume schemas)
  - app.schemas.resume_legacy (pre-Phase-1 multi-agent / evaluation V1 schemas)

Importing from this module continues to work for any code not yet migrated.
"""
from app.schemas.resume_legacy import *  # noqa: F401, F403
from app.schemas.resume_v2 import *  # noqa: F401, F403
