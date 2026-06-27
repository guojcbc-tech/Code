"""字体发现工具。

优先寻找系统中支持中文（CJK）的字体，找不到时回退到 Pillow 自带字体，
以保证中文不会显示成方块/乱码。
"""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Optional

from PIL import ImageFont

# 常见的中文字体候选路径（覆盖 Linux / macOS / Windows）。
_CJK_FONT_CANDIDATES = [
    # 环境变量优先
    os.environ.get("PRODUCTCARD_FONT", ""),
    # Linux
    "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/arphic/uming.ttc",
    # macOS
    "/System/Library/Fonts/PingFang.ttc",
    "/System/Library/Fonts/STHeiti Medium.ttc",
    "/Library/Fonts/Songti.ttc",
    # Windows
    "C:\\Windows\\Fonts\\msyh.ttc",
    "C:\\Windows\\Fonts\\simhei.ttf",
    "C:\\Windows\\Fonts\\simsun.ttc",
]


@lru_cache(maxsize=1)
def find_cjk_font_path() -> Optional[str]:
    """返回第一个存在的中文字体文件路径，找不到返回 None。"""
    for path in _CJK_FONT_CANDIDATES:
        if path and os.path.isfile(path):
            return path
    return None


@lru_cache(maxsize=64)
def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """按字号加载字体。

    ``bold`` 参数在多数 CJK 字体不区分粗细时通过同一文件加载，
    真正的"加粗"效果由绘制时的描边（stroke）来近似实现。
    """
    path = find_cjk_font_path()
    if path:
        try:
            # .ttc 文件可能含多个字形，索引 0 通常即可。
            return ImageFont.truetype(path, size=size)
        except OSError:
            pass
    # 回退：Pillow 自带默认字体（不支持中文，但至少不报错）。
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        # 老版本 Pillow 的 load_default 不接受 size 参数。
        return ImageFont.load_default()
