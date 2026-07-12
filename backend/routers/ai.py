"""AI 对话与权限路由。"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from backend.services import ai_service as svc
from backend.deps import get_api_permission
from backend.permissions import ApiPermission

router = APIRouter(tags=["ai"])


class ChatRequest(BaseModel):
    messages: list[dict] = Field(
        description="对话历史消息列表，格式 `[{\"role\": \"user\", \"content\": \"...\"}, ...]`",
        min_length=1,
    )
    system_prompt: str | None = Field(
        default=None,
        description="自定义系统提示词，默认使用内置 SYSTEM_PROMPT",
    )
    max_iterations: int = Field(
        default=10,
        ge=1,
        le=50,
        description="最大工具调用轮次",
    )
    llm_kwargs: dict[str, Any] | None = Field(
        default=None,
        description="LLM 额外参数（如 temperature）",
    )
    permission_name: str = Field(
        default="ai",
        description="权限名称，对应 _permissions 表中的记录",
    )
    tool_names: list[str] | None = Field(
        default=None,
        description="工具名称列表，如 [\"query_entries\", \"add_entries\"]，默认全部",
    )


class ChatResponse(BaseModel):
    messages: list[dict] = Field(description="完整的对话历史（含新增消息）")


@router.post("/ai/chat")
def ai_chat(
    body: ChatRequest,
    api_perm: ApiPermission = Depends(get_api_permission),
):
    try:
        new_messages = svc.chat(
            messages=body.messages,
            system_prompt=body.system_prompt,
            max_iterations=body.max_iterations,
            llm_kwargs=body.llm_kwargs,
            permission_name=body.permission_name,
            tool_names=body.tool_names,
        )
        return ChatResponse(messages=new_messages)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get("/ai/permission")
def ai_permission():
    return svc.get_permission_info()
