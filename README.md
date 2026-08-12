# 听录 · 录音转文字

对着麦克风说话，文字实时落下；也可上传音频文件，用 Whisper 转写。

## 功能

- **实时听写**：基于浏览器 [Web Speech API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Speech_API)，无需 API Key（推荐 Chrome / Edge）
- **同步录音**：听写同时录制音频，可回放与下载
- **多语言**：中文（普通话 / 粤语）、英语、日语、韩语等
- **文件转写**：上传 mp3 / wav / m4a / webm 等，经本地代理调用 OpenAI 兼容的 Whisper 接口（可选）
- **文稿管理**：复制、下载 TXT、手动编辑

## 快速开始

```bash
npm install
npm run dev
```

浏览器打开终端提示的地址（默认 `http://localhost:5173`），允许麦克风权限后点击「开始听写」。

## 文件转写（可选）

1. 点击右上角 **设置**
2. 填写 OpenAI API Key（或兼容服务的 Key）
3. 如使用第三方兼容接口，可修改 Base URL
4. 切换到「文件转写」，选择音频文件

也可通过环境变量提供默认值（写入 `.env.local`）：

```bash
VITE_OPENAI_API_KEY=sk-...
VITE_OPENAI_BASE_URL=https://api.openai.com/v1
```

> Key 保存在本机 `localStorage`，请求经 Vite 开发/预览服务器的 `/api/transcribe` 代理转发，避免浏览器 CORS 限制。

## 脚本

| 命令 | 说明 |
| --- | --- |
| `npm run dev` | 开发服务器 |
| `npm run build` | 生产构建 |
| `npm run preview` | 预览构建产物（含 Whisper 代理） |
| `npm run lint` | Lint |

## 说明

- 实时听写依赖浏览器语音识别引擎，准确率因环境与口音而异；需 HTTPS 或 localhost。
- Safari / Firefox 对 Web Speech API 支持有限，实时听写请优先使用 Chromium 系浏览器。
- 文件转写需要可用的 Whisper API；未配置 Key 时不影响实时听写。
