"""使用图像生成模型（默认 Nano Banana Pro / Gemini 3 Pro Image）直接生成商品介绍图。

与 ``compose.py`` 的纯本地排版不同，本模块把商品图片连同一段中文营销提示词
一起交给图像生成模型，由模型"重绘"出一张带场景、文案排版的成品商品介绍图。

通过 ZenMux 网关调用（兼容 Vertex AI 协议）：
    export ZENMUX_API_KEY="你的密钥"
可选：
    export PRODUCTCARD_IMAGE_MODEL="google/gemini-3-pro-image-preview"
    export PRODUCTCARD_IMAGE_BASE_URL="https://zenmux.ai/api/vertex-ai"
"""

from __future__ import annotations

import base64
import os
from io import BytesIO
from typing import Optional

from PIL import Image

from .model import ProductInfo

DEFAULT_BASE_URL = "https://zenmux.ai/api/vertex-ai"
DEFAULT_MODEL = "google/gemini-3-pro-image-preview"

# 画面比例 -> 中文描述，提示模型构图方向。
_ORIENTATIONS = {
    "portrait": "竖版海报构图（约 3:4，适合电商详情页和手机浏览）",
    "square": "正方形构图（1:1，适合商品主图）",
    "landscape": "横版构图（约 16:9，适合 banner 和封面）",
}


class ImageGenNotConfigured(RuntimeError):
    """未配置图像生成所需的密钥 / 依赖时抛出。"""


def _api_key() -> Optional[str]:
    return (
        os.environ.get("ZENMUX_API_KEY")
        or os.environ.get("GEMINI_API_KEY")
        or os.environ.get("GOOGLE_API_KEY")
    )


def image_gen_available() -> bool:
    """是否具备调用图像生成模型的条件。"""
    if not _api_key():
        return False
    try:
        import google.genai  # noqa: F401
    except ImportError:
        return False
    return True


def build_prompt(
    info: ProductInfo,
    orientation: str = "portrait",
    style_hint: str = "",
) -> str:
    """根据商品信息构造给图像生成模型的中文提示词。"""
    layout = _ORIENTATIONS.get(orientation, _ORIENTATIONS["portrait"])
    lines = [
        "你是资深电商视觉设计师。请基于我提供的这张商品图片，生成一张精美、专业的中文电商『商品介绍图』。",
        f"构图：{layout}。",
        "要求：",
        "1. 保留并真实还原图片中的商品主体（形状、颜色、材质要与原图一致），不要替换成别的商品。",
        "2. 为商品搭配干净、现代、有质感的场景或纯色背景，灯光柔和、有高级感。",
        "3. 在画面中合理排版以下中文文案，字体清晰美观、主次分明、不要出现错别字或乱码：",
    ]
    if info.brand:
        lines.append(f"   - 品牌/店铺：{info.brand}")
    if info.title and info.title != "商品名称":
        lines.append(f"   - 标题：{info.title}")
    if info.tagline:
        lines.append(f"   - 副标题/slogan：{info.tagline}")
    if info.selling_points:
        pts = " ".join(f"·{p}" for p in info.selling_points)
        lines.append(f"   - 卖点：{pts}")
    if info.description:
        lines.append(f"   - 简介：{info.description}")
    if info.price:
        price_line = f"   - 价格：{info.price}"
        if info.original_price:
            price_line += f"（原价 {info.original_price}，可做划线对比）"
        lines.append(price_line)
    if info.badge:
        lines.append(f"   - 角标/标签：{info.badge}")
    lines.append("4. 整体风格统一、克制、留白得当，达到可直接用于上架的成品质量。")
    if style_hint:
        lines.append(f"5. 额外风格要求：{style_hint}")
    return "\n".join(lines)


def _extract_image(resp) -> Optional[Image.Image]:
    """从 generate_content 响应中提取第一张图片为 PIL.Image。"""
    parts = getattr(resp, "parts", None) or []
    for part in parts:
        inline = getattr(part, "inline_data", None)
        if inline is None:
            continue
        data = inline.data
        if isinstance(data, str):
            data = base64.b64decode(data)
        return Image.open(BytesIO(data)).convert("RGB")
    return None


def generate_card(
    image: Image.Image,
    info: ProductInfo,
    orientation: str = "portrait",
    style_hint: str = "",
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
) -> Image.Image:
    """调用图像生成模型，基于商品图片生成商品介绍图。

    未配置密钥 / 依赖时抛出 ``ImageGenNotConfigured``。
    """
    key = api_key or _api_key()
    if not key:
        raise ImageGenNotConfigured(
            "未检测到图像生成密钥。请设置环境变量 ZENMUX_API_KEY 后重试。"
        )
    try:
        from google import genai
        from google.genai import types
    except ImportError as exc:  # noqa: BLE001
        raise ImageGenNotConfigured(
            "未安装 google-genai，请先执行：pip install google-genai"
        ) from exc

    model = model or os.environ.get("PRODUCTCARD_IMAGE_MODEL", DEFAULT_MODEL)
    base_url = base_url or os.environ.get("PRODUCTCARD_IMAGE_BASE_URL", DEFAULT_BASE_URL)

    client = genai.Client(
        api_key=key,
        vertexai=True,
        http_options=types.HttpOptions(api_version="v1", base_url=base_url),
    )

    prompt = build_prompt(info, orientation=orientation, style_hint=style_hint)
    resp = client.models.generate_content(
        model=model,
        contents=[prompt, image.convert("RGB")],
        config=types.GenerateContentConfig(response_modalities=["TEXT", "IMAGE"]),
    )

    out = _extract_image(resp)
    if out is None:
        raise RuntimeError("图像生成模型未返回图片，请稍后重试或更换模型。")
    return out
