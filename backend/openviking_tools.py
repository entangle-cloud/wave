from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class WriteMode(str, Enum):
    REPLACE = "replace"
    APPEND = "append"
    CREATE = "create"


class FindRequest(BaseModel):
    query: str = Field(min_length=1)
    target_uri: str | None = None
    limit: int | None = Field(None, gt=0)
    min_score: float | None = None
    level: str | None = None
    context_type: str | None = None


class SearchRequest(BaseModel):
    query: str = Field(min_length=1)
    mode: Literal["list", "context"] = "list"
    target_uri: str | None = None
    session_id: str | None = None
    limit: int | None = Field(None, gt=0)
    min_score: float | None = None
    level: str | None = None
    context_type: str | None = None
    quotas: dict[str, Any] | None = None
    purpose: str | None = None
    max_tokens: int | None = Field(None, gt=0)
    detail: str | None = None
    detail_by_category: dict[str, Any] | None = None
    dedup_turns: bool | None = None
    exclude_uris: list[str] | None = None
    peer_scope: str | None = None
    other_peer_penalty: float | None = None
    other_peer_penalties: dict[str, Any] | None = None
    rewrite: Literal["off", "auto"] | None = None


class ReadRequest(BaseModel):
    uris: str | list[str]


class ListRequest(BaseModel):
    uri: str
    recursive: bool | None = None


class TreeRequest(BaseModel):
    uri: str | None = None
    level_limit: int = 3
    node_limit: int = 1000
    include_abstract: bool | None = None


class RememberMessage(BaseModel):
    role: str
    content: str


class RememberRequest(BaseModel):
    messages: list[RememberMessage] = Field(min_length=1)


class WriteRequest(BaseModel):
    uri: str
    content: str
    mode: WriteMode = WriteMode.REPLACE
    wait: bool | None = None
    timeout: float | None = Field(None, gt=0)


class EditRequest(BaseModel):
    uri: str
    old_string: str = Field(min_length=1)
    new_string: str
    replace_all: bool | None = None
    wait: bool | None = None
    timeout: float | None = Field(None, gt=0)


class AddResourceRequest(BaseModel):
    path: str = Field(min_length=1)
    temp_file_id: str | None = None
    description: str | None = None
    watch_interval: float | None = Field(None, gt=0)
    processing_mode: Literal["semantic_and_vectors", "vectors_only"] | None = None
    to: str | None = None
    args: dict[str, Any] | None = None


class ListWatchesRequest(BaseModel):
    pass


class CancelWatchRequest(BaseModel):
    to_uri: str


class GrepRequest(BaseModel):
    uri: str
    pattern: str | list[str]
    case_insensitive: bool | None = None
    node_limit: int | None = Field(None, gt=0)


class GlobRequest(BaseModel):
    pattern: str = Field(min_length=1)
    uri: str | None = None
    node_limit: int | None = Field(None, gt=0)


class ForgetRequest(BaseModel):
    uri: str
    recursive: bool | None = None


class HealthRequest(BaseModel):
    pass


TOOL_REGISTRY: dict[str, type[BaseModel]] = {
    "find": FindRequest,
    "search": SearchRequest,
    "read": ReadRequest,
    "list": ListRequest,
    "tree": TreeRequest,
    "remember": RememberRequest,
    "write": WriteRequest,
    "edit": EditRequest,
    "add_resource": AddResourceRequest,
    "list_watches": ListWatchesRequest,
    "cancel_watch": CancelWatchRequest,
    "grep": GrepRequest,
    "glob": GlobRequest,
    "forget": ForgetRequest,
    "health": HealthRequest,
}


def call_tool(session, tool_name: str, params: BaseModel):
    if tool_name not in TOOL_REGISTRY:
        raise ValueError(f"Unknown OpenViking tool: {tool_name}")
    args = params.model_dump(exclude_none=True)
    return session.call_tool(tool_name, args or {})
