"""主题配色。

每个主题定义了一组颜色，用于背景、卡片、文字、强调色等。
颜色统一使用 (R, G, B) 元组。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

RGB = Tuple[int, int, int]


@dataclass(frozen=True)
class Theme:
    name: str
    background: RGB        # 整体背景
    background_2: RGB      # 渐变背景的第二个颜色
    card: RGB              # 商品图卡片底色
    accent: RGB            # 强调色（价格、标签、装饰条）
    title: RGB             # 主标题文字颜色
    text: RGB              # 正文文字颜色
    muted: RGB             # 次要文字颜色
    badge_text: RGB        # 角标文字颜色


THEMES: Dict[str, Theme] = {
    "fresh": Theme(
        name="fresh",
        background=(245, 250, 248),
        background_2=(228, 244, 238),
        card=(255, 255, 255),
        accent=(31, 176, 130),
        title=(28, 42, 38),
        text=(70, 84, 80),
        muted=(150, 162, 158),
        badge_text=(255, 255, 255),
    ),
    "dark": Theme(
        name="dark",
        background=(22, 24, 30),
        background_2=(34, 38, 48),
        card=(40, 44, 54),
        accent=(255, 196, 0),
        title=(245, 246, 250),
        text=(206, 210, 220),
        muted=(140, 146, 158),
        badge_text=(30, 30, 30),
    ),
    "elegant": Theme(
        name="elegant",
        background=(250, 247, 242),
        background_2=(240, 234, 224),
        card=(255, 255, 255),
        accent=(176, 122, 72),
        title=(46, 38, 30),
        text=(96, 84, 72),
        muted=(168, 156, 142),
        badge_text=(255, 255, 255),
    ),
    "vivid": Theme(
        name="vivid",
        background=(255, 248, 246),
        background_2=(255, 232, 226),
        card=(255, 255, 255),
        accent=(240, 78, 86),
        title=(40, 28, 30),
        text=(92, 76, 78),
        muted=(176, 158, 160),
        badge_text=(255, 255, 255),
    ),
    "ocean": Theme(
        name="ocean",
        background=(243, 248, 253),
        background_2=(222, 236, 250),
        card=(255, 255, 255),
        accent=(38, 122, 232),
        title=(22, 34, 52),
        text=(64, 80, 102),
        muted=(146, 160, 180),
        badge_text=(255, 255, 255),
    ),
}

DEFAULT_THEME = "fresh"


def get_theme(name: str | None) -> Theme:
    """根据名字取主题，未知名字回退到默认主题。"""
    if not name:
        return THEMES[DEFAULT_THEME]
    return THEMES.get(name.lower(), THEMES[DEFAULT_THEME])
