# 🛍️ 商品介绍图生成器 (Product Intro Image Generator)

给程序一张**商品图片**，它就能帮你生成一张精美的、电商风格的**商品介绍图**
（带标题、卖点、价格、品牌、主题配色等排版）。

提供两种生成引擎：

- 🖼️ **本地排版 (compose)**：用 [Pillow](https://python-pillow.org/) 把商品图拼进现代版式卡片，免费、可控、不需要联网，开箱即用。
- 🍌 **AI 出图 (Nano Banana Pro)**：把商品图交给图像生成模型（Google Gemini 3 Pro Image，经 [ZenMux](https://zenmux.ai) 调用）**直接重绘成实拍级成品图**，自动搭配场景与文案排版。

其它特性：

- 🤖 **可选 AI 文案**：配置兼容 OpenAI 的视觉模型后，可让模型"看图"自动生成中文商品文案。
- 🌈 **5 套主题配色**（本地排版）：`fresh` / `dark` / `elegant` / `vivid` / `ocean`。
- 💻 **两种用法**：友好的网页界面 + 支持批量的命令行工具。
- 🈶 **中文友好**：自动寻找系统中文字体，渲染不乱码。

## 效果预览

**AI 出图 (Nano Banana Pro)** —— 输入一张普通商品图，直接生成实拍级成品：

![nanobanana](examples/nanobanana_module.png)

**本地排版 (compose)** —— 多套主题，纯本地渲染：

| fresh | dark | elegant |
|---|---|---|
| ![fresh](examples/sample_fresh.png) | ![dark](examples/sample_dark.png) | ![elegant](examples/sample_elegant.png) |

## 安装

```bash
# 核心功能只需要 Pillow
pip install Pillow

# 如需网页界面与 AI 文案，安装全部依赖
pip install -r requirements.txt
```

## 用法一：网页界面（最简单）

```bash
python -m productcard.webapp
```

然后在浏览器打开终端提示的地址，上传图片 → 填写或让 AI 生成文案 → 点击生成。

## 用法二：命令行

```bash
# 手动指定文案
python -m productcard.cli photo.jpg -o output \
    --title "便携保温水杯 500ml" \
    --tagline "24小时长效保温" \
    --points "316不锈钢内胆" "六小时锁温" "一键弹盖" \
    --price "¥129" --original-price "¥199" \
    --brand "MUJI LIFE" --badge "新品" --theme fresh

# 用 JSON 文件提供文案
python -m productcard.cli photo.jpg -o output --info info.json

# 批量处理整个文件夹
python -m productcard.cli ./photos -o output --theme ocean
```

`info.json` 示例：

```json
{
  "title": "便携保温水杯 500ml",
  "tagline": "24小时长效保温 · 一杯走天下",
  "selling_points": ["316不锈钢内胆", "六小时锁温", "一键弹盖", "防漏密封圈"],
  "description": "精选食品级材质，简约外观适配各种场景。",
  "price": "¥129",
  "original_price": "¥199",
  "brand": "MUJI LIFE",
  "badge": "新品"
}
```

## 用法三：AI 直接出图（Nano Banana Pro，可选）

把商品图片交给图像生成模型直接重绘成成品介绍图。通过 [ZenMux](https://zenmux.ai) 调用 Google Gemini 3 Pro Image（Nano Banana Pro）：

```bash
pip install google-genai
export ZENMUX_API_KEY="你的 ZenMux 密钥"

# 命令行：用 --engine nanobanana
python -m productcard.cli photo.jpg -o output --engine nanobanana \
    --title "手冲咖啡马克杯" --tagline "每天从一杯好咖啡开始" \
    --points "陶瓷材质细腻顺滑" "大容量350ml" "微波炉可用" \
    --price "¥69" --original-price "¥99" --brand "COFFEE TIME" --badge "热卖" \
    --orientation portrait --style "莫兰迪色系，纯净背景"
```

可选环境变量：

```bash
# 默认即 Nano Banana Pro，可换成其它图像生成模型
export PRODUCTCARD_IMAGE_MODEL="google/gemini-3-pro-image-preview"
# 也可换成免费档（有限速）：google/gemini-3-pro-image-preview-free
export PRODUCTCARD_IMAGE_BASE_URL="https://zenmux.ai/api/vertex-ai"
```

`--orientation` 支持 `portrait`（竖版，默认）/ `square`（方形主图）/ `landscape`（横版 banner）。
出图失败时会自动回退到本地 `compose` 引擎，不会中断批量任务。
在网页界面里，把「生成引擎」切换到 **AI 出图 (Nano Banana Pro)** 即可。

## 用法四：AI 自动看图生成文案（可选）

配置好兼容 OpenAI 的视觉模型后，加上 `--ai` 即可让模型根据图片自动生成中文文案：

```bash
export OPENAI_API_KEY="你的密钥"
# 可选：自定义服务地址与模型
export OPENAI_BASE_URL="https://api.openai.com/v1"
export PRODUCTCARD_MODEL="gpt-4o-mini"

python -m productcard.cli ./photos -o output --ai --theme elegant
```

> 在网页界面里勾选 **"AI 自动文案"** 也能达到同样效果。
> 没有配置密钥时，程序会自动回退到手动/默认文案，不会报错。

## 作为库调用

```python
from PIL import Image
from productcard import compose_card, ProductInfo

img = Image.open("photo.jpg")
info = ProductInfo(
    title="便携保温水杯",
    selling_points=["长效保温", "防漏设计"],
    price="¥129",
)
card = compose_card(img, info, theme="fresh")
card.save("card.png")
```

## 自定义字体

中文渲染默认会在系统常见路径中寻找中文字体（如文泉驿、Noto CJK、PingFang、微软雅黑）。
如需指定字体，设置环境变量：

```bash
export PRODUCTCARD_FONT="/path/to/your/font.ttf"
```

## 项目结构

```
productcard/
├── compose.py   # 引擎一：Pillow 本地排版
├── generate.py  # 引擎二：Nano Banana Pro AI 出图（经 ZenMux）
├── theme.py     # 主题配色
├── fonts.py     # 中文字体发现
├── model.py     # 商品信息数据模型
├── analyze.py   # 可选：AI 视觉文案生成
├── cli.py       # 命令行接口
└── webapp.py    # Gradio 网页界面
```
