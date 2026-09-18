from __future__ import annotations

from domain.models import Message
from retrieve.packer import PackedContext

SYSTEM_PROMPT = """你是企业知识库问答助手。只能依据提供的证据块回答，不得编造。

规则：
1. 证据块已标记为 [E1]、[E2] …；回答中每个事实性陈述句末必须带上对应 [En] 引用。
2. 禁止出现无任何 [En] 引用的事实句。
3. 若证据不足以回答问题，请明确说明资料不足，且不要捏造内容。
4. 用 Markdown 组织回答（可用标题、有序/无序列表、加粗、代码块）；不要输出 raw HTML。"""


def build_messages(question: str, packed: PackedContext) -> list[Message]:
    user_content = f"""问题：{question}

证据：
{packed.text}

请用中文、Markdown 回答，并在事实句末使用 [En] 引用。""".strip()
    return [
        Message(role="system", content=SYSTEM_PROMPT),
        Message(role="user", content=user_content),
    ]
