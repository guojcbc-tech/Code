"""Gradio 网页界面：上传商品图片，一键生成商品介绍图。

运行：
    python -m productcard.webapp
然后在浏览器打开终端里提示的地址即可。
"""

from __future__ import annotations

from typing import Optional

from PIL import Image

from .compose import compose_card
from .model import ProductInfo
from .theme import THEMES


def _generate(
    image: Optional[Image.Image],
    engine: str,
    orientation: str,
    style: str,
    use_ai: bool,
    hint: str,
    theme: str,
    title: str,
    tagline: str,
    points_text: str,
    description: str,
    price: str,
    original_price: str,
    brand: str,
    badge: str,
):
    if image is None:
        raise ValueError("请先上传一张商品图片。")

    status = ""
    info = ProductInfo(
        title=title or "商品名称",
        tagline=tagline,
        selling_points=[
            line.strip(" •-·\t")
            for line in points_text.splitlines()
            if line.strip()
        ],
        description=description,
        price=price,
        original_price=original_price,
        brand=brand,
        badge=badge,
    )

    if use_ai:
        from . import analyze

        if not analyze.ai_available():
            status = "⚠️ 未检测到 AI 配置（OPENAI_API_KEY），已改用手动填写的文案。"
        else:
            try:
                ai_info = analyze.analyze_product(image, extra_hint=hint)
                # AI 结果作为基础，手动填写的非空字段优先覆盖。
                if title:
                    ai_info.title = title
                if tagline:
                    ai_info.tagline = tagline
                if points_text.strip():
                    ai_info.selling_points = info.selling_points
                if description:
                    ai_info.description = description
                if price:
                    ai_info.price = price
                if original_price:
                    ai_info.original_price = original_price
                if brand:
                    ai_info.brand = brand
                if badge:
                    ai_info.badge = badge
                info = ai_info
                status = f"🤖 AI 已生成文案：{info.title}"
            except Exception as exc:  # noqa: BLE001
                status = f"⚠️ AI 文案生成失败，已改用手动文案：{exc}"

    use_nanobanana = engine.startswith("AI") or "nano" in engine.lower()
    if use_nanobanana:
        from . import generate

        if not generate.image_gen_available():
            status += (
                "\n⚠️ 未检测到图像生成配置（ZENMUX_API_KEY），已改用本地排版引擎。"
            )
        else:
            try:
                card = generate.generate_card(
                    image, info, orientation=orientation, style_hint=style
                )
                return card, (status + "\n🍌 已由 Nano Banana Pro 生成").strip(), info.to_json()
            except Exception as exc:  # noqa: BLE001
                status += f"\n⚠️ AI 出图失败，已改用本地排版：{exc}"

    card = compose_card(image, info, theme=theme)
    return card, (status or "✅ 生成完成").strip(), info.to_json()


def build_demo():
    import gradio as gr

    with gr.Blocks(title="商品介绍图生成器") as demo:
        gr.Markdown(
            "# 🛍️ 商品介绍图生成器\n"
            "上传商品图片，生成电商风格的商品介绍图。两种引擎：\n"
            "- **本地排版 (compose)**：纯本地 Pillow 排版，免费、可控、不需要联网。\n"
            "- **AI 出图 (Nano Banana Pro)**：交给图像生成模型直接重绘成实拍级成品图（需配置 `ZENMUX_API_KEY`）。\n\n"
            "文案可手动填写，或勾选 **AI 自动文案**（需配置 `OPENAI_API_KEY`）让模型看图生成。"
        )
        with gr.Row():
            with gr.Column(scale=1):
                image_in = gr.Image(label="商品图片", type="pil", height=320)
                engine = gr.Radio(
                    ["本地排版 (compose)", "AI 出图 (Nano Banana Pro)"],
                    value="本地排版 (compose)",
                    label="生成引擎",
                    info="AI 出图需配置 ZENMUX_API_KEY",
                )
                with gr.Row():
                    orientation = gr.Dropdown(
                        ["portrait", "square", "landscape"],
                        value="portrait",
                        label="构图方向 (AI 出图)",
                    )
                    theme = gr.Dropdown(
                        list(THEMES), value="fresh", label="主题配色 (本地排版)"
                    )
                style = gr.Textbox(label="AI 出图风格提示（可选）", placeholder="例如：ins 风、莫兰迪色、纯白背景")
                with gr.Row():
                    use_ai = gr.Checkbox(label="AI 自动文案", value=False)
                hint = gr.Textbox(label="给 AI 文案的补充提示（可选）", placeholder="例如：主打学生群体")
                title = gr.Textbox(label="标题", placeholder="便携保温水杯 500ml")
                tagline = gr.Textbox(label="副标题 / slogan")
                points = gr.Textbox(
                    label="卖点（每行一个）",
                    lines=4,
                    placeholder="长效保温\n防漏设计\n食品级材质",
                )
                description = gr.Textbox(label="商品描述", lines=2)
                with gr.Row():
                    price = gr.Textbox(label="价格", placeholder="¥129")
                    original_price = gr.Textbox(label="原价（划线）", placeholder="¥199")
                with gr.Row():
                    brand = gr.Textbox(label="品牌 / 店铺")
                    badge = gr.Textbox(label="角标", placeholder="新品")
                btn = gr.Button("生成商品介绍图", variant="primary")
            with gr.Column(scale=1):
                out_image = gr.Image(label="生成结果", height=520)
                status = gr.Markdown()
                with gr.Accordion("查看 / 复制文案 JSON", open=False):
                    out_json = gr.Code(label="文案 JSON", language="json")

        btn.click(
            _generate,
            inputs=[
                image_in, engine, orientation, style, use_ai, hint, theme,
                title, tagline, points, description, price, original_price,
                brand, badge,
            ],
            outputs=[out_image, status, out_json],
        )
    return demo


def main():
    import gradio as gr

    demo = build_demo()
    # Gradio 6 把 theme 参数移到了 launch()，旧版本则不接受，做一下兼容。
    try:
        demo.launch(server_name="0.0.0.0", theme=gr.themes.Soft())
    except TypeError:
        demo.launch(server_name="0.0.0.0")


if __name__ == "__main__":
    main()
