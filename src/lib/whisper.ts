const STORAGE_KEY = 'tinglu-whisper-settings'

export type WhisperSettings = {
  apiKey: string
  baseUrl: string
}

const DEFAULTS: WhisperSettings = {
  apiKey: '',
  baseUrl: 'https://api.openai.com/v1',
}

export function loadWhisperSettings(): WhisperSettings {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) {
      return {
        apiKey: import.meta.env.VITE_OPENAI_API_KEY ?? '',
        baseUrl:
          import.meta.env.VITE_OPENAI_BASE_URL ?? DEFAULTS.baseUrl,
      }
    }
    const parsed = JSON.parse(raw) as Partial<WhisperSettings>
    return {
      apiKey: parsed.apiKey ?? import.meta.env.VITE_OPENAI_API_KEY ?? '',
      baseUrl:
        parsed.baseUrl ??
        import.meta.env.VITE_OPENAI_BASE_URL ??
        DEFAULTS.baseUrl,
    }
  } catch {
    return { ...DEFAULTS }
  }
}

export function saveWhisperSettings(settings: WhisperSettings) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(settings))
}

/**
 * Transcribe via OpenAI-compatible `/audio/transcriptions`.
 * Uses a same-origin proxy (`/api/transcribe`) to avoid browser CORS issues.
 */
export async function transcribeAudio(
  file: Blob,
  filename: string,
  settings: WhisperSettings,
  language?: string,
): Promise<string> {
  if (!settings.apiKey.trim()) {
    throw new Error('请先在设置中填写 OpenAI API Key（用于 Whisper 转写）。')
  }

  const form = new FormData()
  form.append('file', file, filename)
  form.append('model', 'whisper-1')
  if (language) {
    // Whisper expects ISO-639-1, e.g. zh / en
    form.append('language', language.split('-')[0] ?? language)
  }

  const res = await fetch('/api/transcribe', {
    method: 'POST',
    headers: {
      'X-API-Key': settings.apiKey.trim(),
      'X-Base-URL': settings.baseUrl.trim() || DEFAULTS.baseUrl,
    },
    body: form,
  })

  const data = (await res.json().catch(() => ({}))) as {
    text?: string
    error?: string
  }

  if (!res.ok) {
    throw new Error(data.error || `转写失败（HTTP ${res.status}）`)
  }

  return (data.text ?? '').trim()
}
