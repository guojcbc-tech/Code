"""命令行接口。

示例：
  # 手动指定文案
  python -m productcard.cli photo.jpg -o out --title "保温杯" --price "¥129" \
      --points "长效保温" "防漏设计" "食品级材质"

  # 用 JSON 文件提供文案
  python -m productcard.cli photo.jpg -o out --info info.json

  # 让 AI 自动看图生成文案（需配置 OPENAI_API_KEY）
  python -m productcard.cli photo.jpg -o out --ai

  # 批量处理整个文件夹
  python -m productcard.cli ./photos -o out --ai
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List

from PIL import Image

from .compose import compose_card
from .model import ProductInfo
from .theme import THEMES

_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif", ".tiff"}


def _gather_images(paths: List[str]) -> List[Path]:
    result: List[Path] = []
    for p in paths:
        path = Path(p)
        if path.is_dir():
            for child in sorted(path.iterdir()):
                if child.suffix.lower() in _IMAGE_EXTS:
                    result.append(child)
        elif path.is_file():
            result.append(path)
        else:
            print(f"⚠️  跳过不存在的路径：{p}", file=sys.stderr)
    return result


def _build_info(args: argparse.Namespace) -> ProductInfo:
    if args.info:
        info = ProductInfo.from_json(Path(args.info).read_text(encoding="utf-8"))
    else:
        info = ProductInfo()
    # 命令行参数覆盖
    if args.title:
        info.title = args.title
    if args.tagline:
        info.tagline = args.tagline
    if args.points:
        info.selling_points = list(args.points)
    if args.description:
        info.description = args.description
    if args.price:
        info.price = args.price
    if args.original_price:
        info.original_price = args.original_price
    if args.brand:
        info.brand = args.brand
    if args.badge:
        info.badge = args.badge
    return info


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="productcard",
        description="把商品图片合成为电商风格的商品介绍图。",
    )
    parser.add_argument("images", nargs="+", help="商品图片文件或文件夹（可多个）")
    parser.add_argument("-o", "--output", default="output", help="输出目录（默认 output）")
    parser.add_argument(
        "-t", "--theme", default="fresh", choices=list(THEMES), help="主题配色"
    )
    parser.add_argument("--ai", action="store_true", help="用视觉模型自动生成文案")
    parser.add_argument("--hint", default="", help="给 AI 的补充提示")
    parser.add_argument("--info", help="包含商品文案的 JSON 文件")
    parser.add_argument("--title", help="商品标题")
    parser.add_argument("--tagline", help="副标题/slogan")
    parser.add_argument("--points", nargs="*", help="卖点列表（空格分隔多个）")
    parser.add_argument("--description", help="商品描述")
    parser.add_argument("--price", help="价格，例如 ¥129")
    parser.add_argument("--original-price", dest="original_price", help="划线原价")
    parser.add_argument("--brand", help="品牌/店铺名")
    parser.add_argument("--badge", help="角标文字，例如 新品")
    args = parser.parse_args(argv)

    images = _gather_images(args.images)
    if not images:
        print("没有找到可处理的图片。", file=sys.stderr)
        return 1

    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)

    base_info = _build_info(args)

    analyzer = None
    if args.ai:
        from . import analyze

        if not analyze.ai_available():
            print(
                "⚠️  未检测到 AI 配置（OPENAI_API_KEY），将改用手动/默认文案。",
                file=sys.stderr,
            )
        else:
            analyzer = analyze

    ok = 0
    for img_path in images:
        try:
            image = Image.open(img_path)
            image.load()
        except Exception as exc:  # noqa: BLE001
            print(f"❌ 无法打开 {img_path}: {exc}", file=sys.stderr)
            continue

        info = base_info
        if analyzer is not None:
            try:
                info = analyzer.analyze_product(image, extra_hint=args.hint)
                print(f"🤖 已为 {img_path.name} 生成文案：{info.title}")
            except Exception as exc:  # noqa: BLE001
                print(f"⚠️  {img_path.name} AI 文案生成失败，改用默认文案：{exc}",
                      file=sys.stderr)

        card = compose_card(image, info, theme=args.theme)
        out_path = out_dir / f"{img_path.stem}_card.png"
        card.save(out_path)
        print(f"✅ {out_path}")
        ok += 1

    print(f"\n完成：成功生成 {ok}/{len(images)} 张商品介绍图，输出目录：{out_dir}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
