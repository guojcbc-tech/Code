"""商品信息的数据模型。"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from typing import List, Optional


@dataclass
class ProductInfo:
    """描述一件商品的文案信息。

    所有字段都是可选的，缺失的字段在排版时会自动省略，
    因此既可以由用户手填，也可以由 AI 自动生成后再人工微调。
    """

    title: str = "商品名称"
    tagline: str = ""  # 一句话副标题 / slogan
    selling_points: List[str] = field(default_factory=list)  # 卖点列表
    description: str = ""  # 较长的介绍段落
    price: str = ""  # 价格文本，例如 "¥199"
    original_price: str = ""  # 划线原价，例如 "¥299"
    brand: str = ""  # 品牌 / 店铺名
    badge: str = ""  # 角标文字，例如 "新品" / "热卖"

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self, **kwargs) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2, **kwargs)

    @classmethod
    def from_dict(cls, data: dict) -> "ProductInfo":
        known = {f for f in cls.__dataclass_fields__}  # type: ignore[attr-defined]
        filtered = {k: v for k, v in data.items() if k in known}
        # 容错：selling_points 可能是用换行分隔的字符串。
        sp = filtered.get("selling_points")
        if isinstance(sp, str):
            filtered["selling_points"] = [
                line.strip(" •-·\t")
                for line in sp.splitlines()
                if line.strip()
            ]
        return cls(**filtered)

    @classmethod
    def from_json(cls, text: str) -> "ProductInfo":
        return cls.from_dict(json.loads(text))
