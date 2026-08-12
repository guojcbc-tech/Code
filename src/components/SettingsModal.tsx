import { useEffect, useId, useState, type FormEvent } from 'react'
import {
  loadWhisperSettings,
  saveWhisperSettings,
  type WhisperSettings,
} from '../lib/whisper'

type Props = {
  open: boolean
  onClose: () => void
}

export function SettingsModal({ open, onClose }: Props) {
  const titleId = useId()
  const [settings, setSettings] = useState<WhisperSettings>(() => loadWhisperSettings())
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    if (open) {
      setSettings(loadWhisperSettings())
      setSaved(false)
    }
  }, [open])

  useEffect(() => {
    if (!open) return
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open, onClose])

  if (!open) return null

  const onSubmit = (e: FormEvent) => {
    e.preventDefault()
    saveWhisperSettings(settings)
    setSaved(true)
  }

  return (
    <div className="modal-backdrop" role="presentation" onClick={onClose}>
      <div
        className="modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        onClick={(e) => e.stopPropagation()}
      >
        <header className="modal__header">
          <h2 id={titleId}>Whisper 转写设置</h2>
          <button type="button" className="icon-btn" onClick={onClose} aria-label="关闭">
            ×
          </button>
        </header>
        <p className="modal__hint">
          实时听写不需要 Key。上传音频文件转写时，会调用兼容 OpenAI 的 Whisper
          接口（经本地代理，Key 仅保存在本机浏览器）。
        </p>
        <form className="modal__form" onSubmit={onSubmit}>
          <label>
            <span>API Key</span>
            <input
              type="password"
              autoComplete="off"
              placeholder="sk-..."
              value={settings.apiKey}
              onChange={(e) =>
                setSettings((s) => ({ ...s, apiKey: e.target.value }))
              }
            />
          </label>
          <label>
            <span>Base URL</span>
            <input
              type="url"
              placeholder="https://api.openai.com/v1"
              value={settings.baseUrl}
              onChange={(e) =>
                setSettings((s) => ({ ...s, baseUrl: e.target.value }))
              }
            />
          </label>
          <div className="modal__actions">
            <button type="submit" className="btn btn--primary">
              保存
            </button>
            {saved && <span className="modal__saved">已保存</span>}
          </div>
        </form>
      </div>
    </div>
  )
}
