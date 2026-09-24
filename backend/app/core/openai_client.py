from functools import lru_cache
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from decimal import Decimal
from types import MappingProxyType
from typing import Literal

from openai import AsyncOpenAI
from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.core.config import settings


class OpenAIConfigurationError(RuntimeError):
    """Raised when an AI feature is called without usable OpenAI settings."""


@lru_cache(maxsize=1)
def get_openai_client() -> AsyncOpenAI:
    if settings.ENABLE_AI_FEATURES and not settings.OPENAI_API_KEY:
        raise OpenAIConfigurationError("OPENAI_API_KEY is required when AI features are enabled")
    return AsyncOpenAI(api_key=settings.OPENAI_API_KEY)


def clear_openai_client_cache() -> None:
    get_openai_client.cache_clear()


class ModelParameters(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    temperature: float = Field(ge=0, le=2, allow_inf_nan=False)


class ModelPricing(BaseModel):
    """USD per million tokens for one exact provider snapshot and price version."""

    model_config = ConfigDict(frozen=True, extra="forbid")
    model_snapshot: str = Field(min_length=1)
    version: str = Field(min_length=1)
    input_usd_per_million: Decimal = Field(ge=0, allow_inf_nan=False)
    cached_input_usd_per_million: Decimal = Field(ge=0, allow_inf_nan=False)
    output_usd_per_million: Decimal = Field(ge=0, allow_inf_nan=False)


class ModelManifest(BaseModel):
    """Versioned call configuration, never credentials or rendered user content."""

    model_config = ConfigDict(frozen=True, extra="forbid")
    provider: Literal["openai"] = "openai"
    model_snapshot: str = Field(min_length=1)
    prompt_name: str = Field(min_length=1)
    prompt_version: str = "1"
    prompt_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    schema_version: str = Field(min_length=1)
    parameters: ModelParameters
    pricing: ModelPricing | None = None

    @model_validator(mode="after")
    def pricing_matches_snapshot(self) -> "ModelManifest":
        if self.pricing is not None and self.pricing.model_snapshot != self.model_snapshot:
            raise ValueError("Manifest pricing must match its exact model snapshot")
        return self


# OpenAI's published standard Chat Completions rates for this pinned snapshot.
# Cached input has a distinct rate; unknown usage detail means cost unavailable.
_GPT_4O_AUG_2024_PRICING = ModelPricing(
    model_snapshot="gpt-4o-2024-08-06",
    version="openai-prompt-caching-2026-09-23",
    input_usd_per_million=Decimal("2.50"),
    cached_input_usd_per_million=Decimal("1.25"),
    output_usd_per_million=Decimal("10.00"),
)


# Hashes lock the unchanged [system, user-template] pair as compact UTF-8 JSON.
# Prompt text stays with its service; characterization tests detect version drift.
DEFAULT_MANIFESTS: Mapping[str, ModelManifest] = MappingProxyType({
    name: ModelManifest(
        model_snapshot="gpt-4o-2024-08-06",
        prompt_name=name,
        prompt_hash=prompt_hash,
        schema_version=schema_version,
        parameters=ModelParameters(temperature=temperature),
        pricing=_GPT_4O_AUG_2024_PRICING,
    )
    for name, prompt_hash, schema_version, temperature in (
        ("evaluator", "c2778f00e0be9bccec41c3330bb131893d7d1de6a80c632a33aedafa75346943", "EvaluationReport.v1", 0.2),
        ("rewriter", "e6a37a4da9d5d4a201a671ce6c60056d932ebc109c75f6f91412f4fdadaeebed", "RewriteResult.v1", 0.4),
        ("extractor", "3a6d86b1f4fa066a95d0b3003fcdaa926b1a162d9f1c98e01aefbeba88879af8", "JDExtraction.v1", 0.1),
        ("tailor", "59c6811de30c33b0a0340e0900a87c50607063a09fc3d317e3e0a403a3ed0d09", "DiffPlan.v1", 0.3),
        ("tailor_options", "eb423c08e9c2eaaa8e0c936102ecf60cf6a5f3affbffdb2398233dd929bb65ca", "BulletDiff.v1", 0.4),
    )
})


@dataclass(frozen=True)
class ModelRuntime:
    """Request-scoped injection; constructing a service never opens a client."""

    client_factory: Callable[[], AsyncOpenAI] = field(default=get_openai_client, repr=False)
    manifests: Mapping[str, ModelManifest] = field(default_factory=lambda: DEFAULT_MANIFESTS)

    def __post_init__(self) -> None:
        # Snapshot caller-owned mappings so metadata cannot drift during an await.
        object.__setattr__(self, "manifests", MappingProxyType(dict(self.manifests)))

    def single_attempt_client(self) -> AsyncOpenAI:
        # Reuse the transport without changing the shared/legacy client's policy.
        # Application retries are the sole attempt budget for these operations.
        return self.client_factory().with_options(max_retries=0)


def get_model_runtime() -> ModelRuntime:
    return ModelRuntime(client_factory=get_openai_client)
