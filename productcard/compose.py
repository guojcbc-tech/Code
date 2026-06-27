"""核心排版引擎：把商品图片合成为电商风格的介绍图。

使用 Pillow 绘制，纯本地运行，不需要联网。
"""

from __future__ import annotations

from typing import List, Optional, Tuple

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from .fonts import load_font
from .model import ProductInfo
from .theme import Theme, get_theme

RGB = Tuple[int, int, int]

# 画布默认尺寸（竖版，适合电商详情 / 朋友圈分享）。
DEFAULT_WIDTH = 1080
DEFAULT_HEIGHT = 1440
MARGIN = 72


# --------------------------------------------------------------------------- #
# 基础绘制辅助
# --------------------------------------------------------------------------- #
def _vertical_gradient(size: Tuple[int, int], top: RGB, bottom: RGB) -> Image.Image:
    """生成一张竖直渐变图。"""
    w, h = size
    base = Image.new("RGB", (1, h))
    px = base.load()
    for y in range(h):
        t = y / max(h - 1, 1)
        px[0, y] = (
            round(top[0] + (bottom[0] - top[0]) * t),
            round(top[1] + (bottom[1] - top[1]) * t),
            round(top[2] + (bottom[2] - top[2]) * t),
        )
    return base.resize((w, h))


def _rounded_mask(size: Tuple[int, int], radius: int) -> Image.Image:
    """返回一张圆角矩形的 L 模式蒙版。"""
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([(0, 0), (size[0] - 1, size[1] - 1)], radius=radius, fill=255)
    return mask


def _paste_rounded(
    canvas: Image.Image,
    box: Tuple[int, int, int, int],
    fill: RGB,
    radius: int,
    shadow: bool = True,
) -> None:
    """在画布上画一个带柔和阴影的圆角矩形。"""
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    if shadow:
        pad = 40
        shadow_layer = Image.new("RGBA", (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
        sd = ImageDraw.Draw(shadow_layer)
        sd.rounded_rectangle(
            [(pad, pad), (pad + w, pad + h)], radius=radius, fill=(0, 0, 0, 70)
        )
        shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(18))
        canvas.paste(
            shadow_layer,
            (x0 - pad, y0 - pad + 10),
            shadow_layer,
        )
    card = Image.new("RGB", (w, h), fill)
    canvas.paste(card, (x0, y0), _rounded_mask((w, h), radius))


def _fit_image(img: Image.Image, box_w: int, box_h: int) -> Image.Image:
    """等比缩放图片以"包含"在给定尺寸内（contain）。"""
    img = img.convert("RGBA")
    ratio = min(box_w / img.width, box_h / img.height)
    new_size = (max(1, round(img.width * ratio)), max(1, round(img.height * ratio)))
    return img.resize(new_size, Image.LANCZOS)


# --------------------------------------------------------------------------- #
# 文本辅助
# --------------------------------------------------------------------------- #
def _wrap_text(
    text: str, font: ImageFont.FreeTypeFont, max_width: int
) -> List[str]:
    """按像素宽度折行，兼容中英文混排。

    中文逐字断行；英文优先在空格处断行。
    """
    lines: List[str] = []
    for paragraph in text.split("\n"):
        if not paragraph:
            lines.append("")
            continue
        current = ""
        for ch in paragraph:
            trial = current + ch
            if font.getlength(trial) <= max_width or not current:
                current = trial
            else:
                # 英文单词尽量不拆开
                if ch != " " and " " in current and not _is_cjk(ch):
                    head, _, tail = current.rpartition(" ")
                    lines.append(head)
                    current = tail + ch
                else:
                    lines.append(current)
                    current = ch
        lines.append(current)
    return lines


def _is_cjk(ch: str) -> bool:
    return "\u4e00" <= ch <= "\u9fff"


def _draw_text_block(
    draw: ImageDraw.ImageDraw,
    xy: Tuple[int, int],
    text: str,
    font: ImageFont.FreeTypeFont,
    fill: RGB,
    max_width: int,
    line_spacing: float = 1.35,
    stroke_width: int = 0,
    stroke_fill: Optional[RGB] = None,
    max_lines: Optional[int] = None,
) -> int:
    """绘制可换行文本块，返回绘制后的底部 y 坐标。"""
    x, y = xy
    lines = _wrap_text(text, font, max_width)
    if max_lines is not None and len(lines) > max_lines:
        lines = lines[:max_lines]
        if lines:
            # 末行加省略号
            last = lines[-1]
            while last and font.getlength(last + "…") > max_width:
                last = last[:-1]
            lines[-1] = last + "…"
    ascent, descent = font.getmetrics()
    line_h = round((ascent + descent) * line_spacing)
    for line in lines:
        draw.text(
            (x, y),
            line,
            font=font,
            fill=fill,
            stroke_width=stroke_width,
            stroke_fill=stroke_fill or fill,
        )
        y += line_h
    return y


# --------------------------------------------------------------------------- #
# 主入口
# --------------------------------------------------------------------------- #
def compose_card(
    product_image: Image.Image,
    info: ProductInfo,
    theme: Theme | str | None = None,
    width: int = DEFAULT_WIDTH,
    height: int = DEFAULT_HEIGHT,
) -> Image.Image:
    """把一张商品图片和文案信息合成为商品介绍图。

    参数
    ----
    product_image: 原始商品图片（PIL.Image）。
    info: 商品文案信息。
    theme: 主题名或 Theme 对象。
    width, height: 输出画布尺寸。
    """
    if not isinstance(theme, Theme):
        theme = get_theme(theme)

    # 1) 渐变背景
    canvas = _vertical_gradient((width, height), theme.background, theme.background_2)
    draw = ImageDraw.Draw(canvas)

    content_w = width - MARGIN * 2
    y = MARGIN

    # 2) 顶部：品牌 + 角标
    if info.brand:
        brand_font = load_font(34)
        draw.text((MARGIN, y), info.brand, font=brand_font, fill=theme.muted)
    if info.badge:
        badge_font = load_font(30)
        pad_x, pad_y = 22, 12
        tw = badge_font.getlength(info.badge)
        ascent, descent = badge_font.getmetrics()
        th = ascent + descent
        bx1 = width - MARGIN
        bx0 = round(bx1 - tw - pad_x * 2)
        by0 = y - 4
        by1 = round(by0 + th + pad_y * 2)
        draw.rounded_rectangle([(bx0, by0), (bx1, by1)], radius=(by1 - by0) // 2, fill=theme.accent)
        draw.text((bx0 + pad_x, by0 + pad_y), info.badge, font=badge_font, fill=theme.badge_text)
    y += 64

    # 3) 商品图卡片
    card_h = round(height * 0.42)
    card_box = (MARGIN, y, width - MARGIN, y + card_h)
    _paste_rounded(canvas, card_box, theme.card, radius=36, shadow=True)

    inner_pad = 36
    fitted = _fit_image(
        product_image,
        content_w - inner_pad * 2,
        card_h - inner_pad * 2,
    )
    px = MARGIN + (content_w - fitted.width) // 2
    py = y + (card_h - fitted.height) // 2
    canvas.paste(fitted, (px, py), fitted)
    y += card_h + 56

    # 4) 强调装饰条 + 标题
    bar_h = 46
    draw.rounded_rectangle(
        [(MARGIN, y + 6), (MARGIN + 12, y + bar_h)], radius=6, fill=theme.accent
    )
    title_font = load_font(58)
    y = _draw_text_block(
        draw,
        (MARGIN + 30, y),
        info.title,
        title_font,
        theme.title,
        content_w - 30,
        line_spacing=1.2,
        stroke_width=1,
        stroke_fill=theme.title,
        max_lines=2,
    )
    y += 8

    # 5) 副标题
    if info.tagline:
        tagline_font = load_font(34)
        y = _draw_text_block(
            draw,
            (MARGIN, y),
            info.tagline,
            tagline_font,
            theme.accent,
            content_w,
            line_spacing=1.3,
            max_lines=2,
        )
    y += 18

    # 6) 卖点列表
    if info.selling_points:
        point_font = load_font(34)
        ascent, descent = point_font.getmetrics()
        line_h = round((ascent + descent) * 1.5)
        for point in info.selling_points[:5]:
            # 圆点
            cy = y + (ascent + descent) // 2
            r = 7
            draw.ellipse(
                [(MARGIN + 2, cy - r), (MARGIN + 2 + 2 * r, cy + r)],
                fill=theme.accent,
            )
            _draw_text_block(
                draw,
                (MARGIN + 34, y),
                point,
                point_font,
                theme.text,
                content_w - 34,
                line_spacing=1.5,
                max_lines=1,
            )
            y += line_h
    y += 10

    # 7) 描述段落
    if info.description:
        desc_font = load_font(30)
        y = _draw_text_block(
            draw,
            (MARGIN, y),
            info.description,
            desc_font,
            theme.muted,
            content_w,
            line_spacing=1.5,
            max_lines=4,
        )

    # 8) 底部价格区（固定贴底）
    if info.price or info.original_price:
        _draw_price(draw, info, theme, width, height)

    return canvas


def _draw_price(
    draw: ImageDraw.ImageDraw,
    info: ProductInfo,
    theme: Theme,
    width: int,
    height: int,
) -> None:
    baseline_y = height - MARGIN - 70
    x = MARGIN
    if info.price:
        price_font = load_font(72)
        draw.text((x, baseline_y), info.price, font=price_font, fill=theme.accent,
                  stroke_width=1, stroke_fill=theme.accent)
        x += round(price_font.getlength(info.price)) + 20
    if info.original_price:
        op_font = load_font(34)
        op_ascent, op_descent = op_font.getmetrics()
        oy = baseline_y + 36
        draw.text((x, oy), info.original_price, font=op_font, fill=theme.muted)
        # 划线
        ow = op_font.getlength(info.original_price)
        line_y = oy + (op_ascent + op_descent) // 2
        draw.line([(x, line_y), (x + ow, line_y)], fill=theme.muted, width=2)
