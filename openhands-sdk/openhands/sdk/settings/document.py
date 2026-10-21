"""Canonical transparent settings document shared across OpenHands products."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from openhands.sdk.llm.meta_profile_store import MetaProfile
from openhands.sdk.marketplace import MarketplaceRegistration
from openhands.sdk.profiles import AgentProfile

from .metadata import (
    SETTINGS_METADATA_KEY,
    SettingProminence,
    SettingsFieldMetadata,
)
from .model import (
    AgentSettingsConfig,
    ConversationSettings,
    SettingsFieldSchema,
    SettingsSchema,
    SettingsSectionSchema,
    export_agent_settings_schema,
    export_settings_schema,
)


SETTINGS_DOCUMENT_SCHEMA_VERSION = 1

type JsonValue = (
    str | int | float | bool | None | list[JsonValue] | dict[str, JsonValue]
)


def _field_metadata(
    prominence: SettingProminence = SettingProminence.MINOR,
) -> dict[str, Any]:
    return {
        SETTINGS_METADATA_KEY: SettingsFieldMetadata(prominence=prominence).model_dump()
    }


class ProductSettings(BaseModel):
    """Frontend/product preferences that do not alter agent execution."""

    model_config = ConfigDict(extra="allow")

    __pydantic_extra__: dict[str, JsonValue] = Field(init=False)

    language: str = Field(
        default="en",
        description="Language used by the product interface.",
        json_schema_extra=_field_metadata(SettingProminence.CRITICAL),
    )
    enable_sound_notifications: bool = Field(
        default=False,
        description="Play a sound when an agent needs attention.",
        json_schema_extra=_field_metadata(SettingProminence.MAJOR),
    )
    user_consents_to_analytics: bool | None = Field(
        default=None,
        description="User choice for anonymous product analytics.",
        json_schema_extra=_field_metadata(),
    )
    git_user_name: str = Field(
        default="openhands",
        description="Git author name used for product-initiated commits.",
        json_schema_extra=_field_metadata(SettingProminence.MAJOR),
    )
    git_user_email: str = Field(
        default="openhands@all-hands.dev",
        description="Git author email used for product-initiated commits.",
        json_schema_extra=_field_metadata(SettingProminence.MAJOR),
    )
    title_llm_profile: str | None = Field(
        default=None,
        description="LLM profile used to generate conversation titles.",
        json_schema_extra=_field_metadata(),
    )
    disabled_skills: list[str] = Field(
        default_factory=list,
        description="User and project skills disabled by the user.",
        json_schema_extra=_field_metadata(),
    )
    enabled_skills: list[str] | None = Field(
        default=None,
        description="Bundled catalog skills explicitly enabled by the user.",
        json_schema_extra=_field_metadata(),
    )
    run_router_at_conversation_start: bool = Field(
        default=False,
        description="Route the initial task through the active model router.",
        json_schema_extra=_field_metadata(SettingProminence.MAJOR),
    )
    workspace_file_discovery: dict[str, JsonValue] = Field(
        default_factory=dict,
        description="Per-workspace file discovery preferences.",
        json_schema_extra=_field_metadata(),
    )
    default_profile_migrated: bool = Field(
        default=False,
        description="Whether legacy behavior was copied into the default profile.",
        json_schema_extra=_field_metadata(),
    )


class SettingsSecretReference(BaseModel):
    """Opaque reference to a secret held by the active persistence backend."""

    model_config = ConfigDict(extra="forbid")

    ref: str = Field(min_length=1)
    is_set: bool = False


class LLMProfileDocument(BaseModel):
    """Named LLM profile with secret values replaced by references."""

    model_config = ConfigDict(extra="forbid")

    settings: dict[str, JsonValue] = Field(default_factory=dict)
    secret_references: dict[str, SettingsSecretReference] = Field(default_factory=dict)


class ProviderConnectionDocument(BaseModel):
    """Shared provider connection without inline credential material."""

    model_config = ConfigDict(extra="forbid")

    id: str
    display_name: str
    provider: str = "custom"
    base_url: str | None = None
    created_at: int | None = None
    updated_at: int | None = None
    api_key: SettingsSecretReference | None = None


class SettingsProfilePointers(BaseModel):
    """Active selectors for named settings resources."""

    active_llm_profile: str | None = None
    active_agent_profile_id: str | None = None
    active_model_router: str | None = None


class SettingsResources(BaseModel):
    """Named resources referenced by settings and profiles."""

    llm_profiles: dict[str, LLMProfileDocument] = Field(default_factory=dict)
    agent_profiles: dict[str, AgentProfile] = Field(default_factory=dict)
    provider_connections: dict[str, ProviderConnectionDocument] = Field(
        default_factory=dict
    )
    model_routers: dict[str, MetaProfile] = Field(default_factory=dict)
    marketplaces: list[MarketplaceRegistration] = Field(default_factory=list)
    credentials: dict[str, SettingsSecretReference] = Field(default_factory=dict)
    pointers: SettingsProfilePointers = Field(default_factory=SettingsProfilePointers)


class SettingsProfilePointersPatch(BaseModel):
    """Sparse update to active resource selectors."""

    model_config = ConfigDict(extra="forbid")

    active_llm_profile: str | None = None
    active_agent_profile_id: str | None = None
    active_model_router: str | None = None


class SettingsResourcesPatch(BaseModel):
    """Sparse update to resource metadata managed through settings persistence."""

    model_config = ConfigDict(extra="forbid")

    pointers: SettingsProfilePointersPatch | None = None


class ProductSettingsPatch(BaseModel):
    """Sparse product-preference patch."""

    model_config = ConfigDict(extra="forbid")

    language: str | None = None
    user_consents_to_analytics: bool | None = None
    enable_sound_notifications: bool | None = None
    git_user_name: str | None = None
    git_user_email: str | None = None
    title_llm_profile: str | None = None
    disabled_skills: list[str] | None = None
    enabled_skills: list[str] | None = None
    run_router_at_conversation_start: bool | None = None
    workspace_file_discovery: dict[str, JsonValue] | None = None
    default_profile_migrated: bool | None = None


class SettingsDocumentPatch(BaseModel):
    """Sparse patch for values stored directly by the settings backend.

    Named resources continue to use their existing production resource clients;
    this patch owns the cross-resource pointers that participate in settings.
    """

    model_config = ConfigDict(extra="forbid")

    agent: dict[str, JsonValue] | None = None
    conversation: dict[str, JsonValue] | None = None
    product: ProductSettingsPatch | None = None
    resources: SettingsResourcesPatch | None = None


class SettingsDocument(BaseModel):
    """Portable settings value document.

    Enterprise hierarchy, locks, provenance, and patch resolution are deliberately
    excluded. Deployments may compose this value document before returning it.
    """

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1] = SETTINGS_DOCUMENT_SCHEMA_VERSION
    agent: AgentSettingsConfig
    conversation: ConversationSettings = Field(default_factory=ConversationSettings)
    product: ProductSettings = Field(default_factory=ProductSettings)
    resources: SettingsResources = Field(default_factory=SettingsResources)


def _prefix_schema(schema: SettingsSchema, prefix: str) -> list[SettingsSectionSchema]:
    sections: list[SettingsSectionSchema] = []
    for section in schema.sections:
        section_key = f"{prefix}.{section.key}"
        fields = [
            field.model_copy(
                update={
                    "key": f"{prefix}.{field.key}",
                    "section": section_key,
                    "section_label": section.label,
                }
            )
            for field in section.fields
        ]
        sections.append(
            section.model_copy(update={"key": section_key, "fields": fields})
        )
    return sections


def _resource_field(key: str, label: str, value_type: Literal["array", "object"]):
    return SettingsFieldSchema(
        key=f"resources.{key}",
        label=label,
        description="Managed named resource in the canonical settings document.",
        section="resources",
        section_label="Resources",
        value_type=value_type,
        default=[] if value_type == "array" else {},
        prominence=SettingProminence.MINOR,
    )


def export_settings_document_schema() -> SettingsSchema:
    """Export one renderer schema for all transparent document values."""

    sections = _prefix_schema(export_agent_settings_schema(), "agent")
    sections.extend(
        _prefix_schema(ConversationSettings.export_schema(), "conversation")
    )
    sections.extend(_prefix_schema(export_settings_schema(ProductSettings), "product"))
    sections.append(
        SettingsSectionSchema(
            key="resources",
            label="Resources",
            fields=[
                _resource_field("llm_profiles", "LLM Profiles", "object"),
                _resource_field("agent_profiles", "Agent Profiles", "object"),
                _resource_field(
                    "provider_connections", "Provider Connections", "object"
                ),
                _resource_field("model_routers", "Model Routers", "object"),
                _resource_field("marketplaces", "Marketplaces", "array"),
                _resource_field("credentials", "Credential References", "object"),
                _resource_field("pointers", "Active Profiles", "object"),
            ],
        )
    )
    return SettingsSchema(model_name="SettingsDocument", sections=sections)
