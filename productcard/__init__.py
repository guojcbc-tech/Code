"""商品介绍图生成器 (Product Introduction Image Generator).

一个把商品照片合成为精美电商风格介绍图的小工具，可选地借助
视觉大模型自动生成中文文案。
"""

from .model import ProductInfo
from .theme import THEMES, Theme, get_theme
from .compose import compose_card

__all__ = [
    "ProductInfo",
    "THEMES",
    "Theme",
    "get_theme",
    "compose_card",
    "generate_card",
]


def generate_card(*args, **kwargs):
    """惰性导入的 AI 出图入口（见 ``productcard.generate.generate_card``）。"""
    from .generate import generate_card as _gen

    return _gen(*args, **kwargs)

__version__ = "0.1.0"
