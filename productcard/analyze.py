"""可选的 AI 视觉文案生成。

如果配置了兼容 OpenAI 的视觉模型（环境变量 ``OPENAI_API_KEY``，
可选 ``OPENAI_BASE_URL`` 与 ``PRODUCTCARD_MODEL``），就可以让模型"看"图片，
自动生成中文商品文案；没有配置时本模块不可用，程序仍可手动填写文案使用。
"""

from __future__ import annotations

import base64
import io
import json
import os
import re
from typing import Optional

from PIL import Image

from .model import ProductInfo

_PROMPT = """你是一名资深电商文案策划。请根据图片中的商品，生成用于商品介绍图的中文文案。
要求：
- 只描述图片中真实可见的商品，不要编造图片中不存在的信息。
- 文案精炼、有吸引力，符合中文电商风格。
严格只输出一个 JSON 对象，不要包含任何额外文字或解释，字段如下：
{
  "title": "商品标题（不超过15字）",
  "tagline": "一句话卖点副标题（不超过20字）",
  "selling_points": ["卖点1", "卖点2", "卖点3", "卖点4"],
  "description": "一段约40-60字的商品描述",
  "badge": "角标短语，例如 新品/热卖/限时（不超过4字）"
}"""


class AINotConfigured(RuntimeError):
    """当未配置 AI 凭据时抛出。"""


def ai_available() -> bool:
    """是否具备调用 AI 的条件（已安装 openai 且配置了 API Key）。"""
    if not os.environ.get("OPENAI_API_KEY"):
        return False
    try:
        import openai  # noqa: F401
    except ImportError:
        return False
    return True


def _encode_image(img: Image.Image) -> str:
    """把图片编码为 data URL（JPEG），过大则先缩小。"""
    img = img.convert("RGB")
    max_side = 1024
    if max(img.size) > max_side:
        ratio = max_side / max(img.size)
        img = img.resize(
            (round(img.width * ratio), round(img.height * ratio)), Image.LANCZOS
        )
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=88)
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/jpeg;base64,{b64}"


def _extract_json(text: str) -> dict:
    """从模型输出中尽量稳健地解析出 JSON 对象。"""
    text = text.strip()
    # 去掉 ```json ... ``` 代码块围栏
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.MULTILINE).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if match:
            return json.loads(match.group(0))
        raise


def analyze_product(
    image: Image.Image,
    extra_hint: str = "",
    model: Optional[str] = None,
) -> ProductInfo:
    """调用视觉模型分析图片，返回商品文案。

    未配置 AI 时抛出 ``AINotConfigured``。
    """
    if not ai_available():
        raise AINotConfigured(
            "未检测到 AI 配置。请设置环境变量 OPENAI_API_KEY（可选 OPENAI_BASE_URL、"
            "PRODUCTCARD_MODEL）后重试，或改用手动填写文案的方式。"
        )

    from openai import OpenAI

    client = OpenAI(
        api_key=os.environ["OPENAI_API_KEY"],
        base_url=os.environ.get("OPENAI_BASE_URL") or None,
    )
    model = model or os.environ.get("PRODUCTCARD_MODEL", "gpt-4o-mini")

    user_text = _PROMPT
    if extra_hint:
        user_text += f"\n补充信息（供参考）：{extra_hint}"

    resp = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_text},
                    {
                        "type": "image_url",
                        "image_url": {"url": _encode_image(image)},
                    },
                ],
            }
        ],
        temperature=0.7,
        max_tokens=600,
    )
    content = resp.choices[0].message.content or ""
    data = _extract_json(content)
    return ProductInfo.from_dict(data)
