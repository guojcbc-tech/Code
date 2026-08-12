import { useCallback, useRef, useState, type ChangeEvent } from 'react'
import { SettingsModal } from './components/SettingsModal'
import { Waveform } from './components/Waveform'
import { useAudioRecorder } from './hooks/useAudioRecorder'
import { useDictation } from './hooks/useDictation'
import { formatDuration } from './lib/format'
import { LANGUAGES, type LanguageCode } from './lib/speech'
import { loadWhisperSettings, transcribeAudio } from './lib/whisper'
import './App.css'

type Mode = 'live' | 'file'

export default function App() {
  const [lang, setLang] = useState<LanguageCode>('zh-CN')
  const [transcript, setTranscript] = useState('')
  const [mode, setMode] = useState<Mode>('live')
  const [settingsOpen, setSettingsOpen] = useState(false)
  const [fileBusy, setFileBusy] = useState(false)
  const [fileError, setFileError] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const appendFinal = useCallback((chunk: string) => {
    setTranscript((prev) => {
      const needsSpace =
        prev.length > 0 &&
        !/\s$/.test(prev) &&
        !/^[,.!?，。！？、；：]/.test(chunk)
      const spacer = needsSpace && /^[A-Za-z0-9]/.test(chunk) ? ' ' : ''
      return prev + spacer + chunk
    })
  }, [])

  const dictation = useDictation({ lang, onFinal: appendFinal })
  const recorder = useAudioRecorder()

  const isListening = dictation.status === 'listening'
  const isPaused = dictation.status === 'paused'

  const toggleListen = async () => {
    if (isListening) {
      dictation.pause()
      if (recorder.status === 'recording') recorder.stop()
      return
    }
    if (isPaused) {
      dictation.resume()
      await recorder.start()
      return
    }
    dictation.start()
    await recorder.start()
  }

  const stopAll = () => {
    dictation.stop()
    if (recorder.status === 'recording') recorder.stop()
  }

  const clearAll = () => {
    stopAll()
    setTranscript('')
    recorder.reset()
    setFileError(null)
  }

  const copyText = async () => {
    const text = transcript.trim()
    if (!text) return
    await navigator.clipboard.writeText(text)
    setCopied(true)
    window.setTimeout(() => setCopied(false), 1600)
  }

  const downloadText = () => {
    const text = transcript.trim()
    if (!text) return
    const blob = new Blob([text], { type: 'text/plain;charset=utf-8' })
    const a = document.createElement('a')
    a.href = URL.createObjectURL(blob)
    a.download = `听录-${new Date().toISOString().slice(0, 19).replace(/[:T]/g, '-')}.txt`
    a.click()
    URL.revokeObjectURL(a.href)
  }

  const downloadAudio = () => {
    if (!recorder.url || !recorder.blob) return
    const ext = recorder.blob.type.includes('mp4')
      ? 'm4a'
      : recorder.blob.type.includes('ogg')
        ? 'ogg'
        : 'webm'
    const a = document.createElement('a')
    a.href = recorder.url
    a.download = `听录-${Date.now()}.${ext}`
    a.click()
  }

  const onFilePick = async (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    e.target.value = ''
    if (!file) return

    setFileError(null)
    setFileBusy(true)
    try {
      const settings = loadWhisperSettings()
      const text = await transcribeAudio(file, file.name, settings, lang)
      if (!text) {
        setFileError('未识别到有效语音内容。')
      } else {
        setTranscript((prev) => (prev ? `${prev}\n${text}` : text))
      }
    } catch (err) {
      setFileError(err instanceof Error ? err.message : '转写失败')
    } finally {
      setFileBusy(false)
    }
  }

  const statusLabel = (() => {
    if (mode === 'file') return fileBusy ? '正在转写…' : '上传音频转写'
    if (isListening) return '正在听写'
    if (isPaused) return '已暂停'
    return '准备就绪'
  })()

  return (
    <div className="app">
      <div className="atmosphere" aria-hidden="true">
        <div className="atmosphere__glow atmosphere__glow--a" />
        <div className="atmosphere__glow atmosphere__glow--b" />
        <div className="atmosphere__grain" />
      </div>

      <header className="topbar">
        <div className="brand" aria-label="听录">
          <span className="brand__mark" aria-hidden="true" />
          <span className="brand__name">听录</span>
        </div>
        <div className="topbar__actions">
          <label className="lang">
            <span className="sr-only">识别语言</span>
            <select
              value={lang}
              onChange={(e) => setLang(e.target.value as LanguageCode)}
              disabled={isListening}
            >
              {LANGUAGES.map((l) => (
                <option key={l.code} value={l.code}>
                  {l.label}
                </option>
              ))}
            </select>
          </label>
          <button
            type="button"
            className="ghost-btn"
            onClick={() => setSettingsOpen(true)}
          >
            设置
          </button>
        </div>
      </header>

      <main className="stage">
        <section className="hero" aria-labelledby="hero-title">
          <p className="hero__eyebrow">录音转文字</p>
          <h1 id="hero-title" className="hero__title">
            听录
          </h1>
          <p className="hero__sub">
            对着麦克风说，文字实时落下。也可上传音频，交给 Whisper 转写。
          </p>
        </section>

        <div className="mode-tabs" role="tablist" aria-label="模式">
          <button
            type="button"
            role="tab"
            aria-selected={mode === 'live'}
            className={mode === 'live' ? 'is-active' : ''}
            onClick={() => {
              stopAll()
              setMode('live')
            }}
          >
            实时听写
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={mode === 'file'}
            className={mode === 'file' ? 'is-active' : ''}
            onClick={() => {
              stopAll()
              setMode('file')
            }}
          >
            文件转写
          </button>
        </div>

        <section className="console" aria-label="听写控制台">
          <div className="console__meter">
            <Waveform
              levels={recorder.levels}
              active={recorder.status === 'recording' || isListening}
            />
            <p className={`console__status ${isListening ? 'is-live' : ''}`}>
              <span className="console__dot" />
              {statusLabel}
              {recorder.status === 'recording' && (
                <span className="console__timer">
                  {formatDuration(recorder.elapsedMs)}
                </span>
              )}
            </p>
          </div>

          {mode === 'live' ? (
            <div className="console__controls">
              {!dictation.supported && (
                <p className="banner banner--warn">
                  当前浏览器不支持 Web Speech API。请使用最新版 Chrome 或
                  Edge，并允许麦克风权限。
                </p>
              )}
              {(dictation.error || recorder.error) && (
                <p className="banner banner--error">
                  {dictation.error || recorder.error}
                </p>
              )}

              <button
                type="button"
                className={`mic-btn ${isListening ? 'mic-btn--hot' : ''}`}
                onClick={() => void toggleListen()}
                disabled={!dictation.supported}
                aria-pressed={isListening}
              >
                <span className="mic-btn__ring" aria-hidden="true" />
                <span className="mic-btn__icon" aria-hidden="true">
                  {isListening ? (
                    <svg viewBox="0 0 24 24" width="36" height="36">
                      <rect x="7" y="7" width="10" height="10" rx="1.5" fill="currentColor" />
                    </svg>
                  ) : (
                    <svg viewBox="0 0 24 24" width="36" height="36">
                      <path
                        fill="currentColor"
                        d="M12 14a3 3 0 0 0 3-3V7a3 3 0 1 0-6 0v4a3 3 0 0 0 3 3zm5-3a5 5 0 0 1-10 0H5a7 7 0 0 0 6 6.92V21h2v-3.08A7 7 0 0 0 19 11h-2z"
                      />
                    </svg>
                  )}
                </span>
                <span className="mic-btn__label">
                  {isListening ? '暂停' : isPaused ? '继续' : '开始听写'}
                </span>
              </button>

              <div className="console__row">
                <button
                  type="button"
                  className="btn"
                  onClick={stopAll}
                  disabled={!isListening && !isPaused}
                >
                  结束
                </button>
                {recorder.url && (
                  <>
                    <audio className="console__audio" controls src={recorder.url} />
                    <button type="button" className="btn" onClick={downloadAudio}>
                      下载录音
                    </button>
                  </>
                )}
              </div>
            </div>
          ) : (
            <div className="console__controls console__controls--file">
              {fileError && <p className="banner banner--error">{fileError}</p>}
              <input
                ref={fileInputRef}
                type="file"
                accept="audio/*,.mp3,.wav,.m4a,.webm,.ogg,.flac,.mp4"
                hidden
                onChange={(e) => void onFilePick(e)}
              />
              <button
                type="button"
                className="mic-btn mic-btn--file"
                disabled={fileBusy}
                onClick={() => fileInputRef.current?.click()}
              >
                <span className="mic-btn__ring" aria-hidden="true" />
                <span className="mic-btn__icon" aria-hidden="true">
                  <svg viewBox="0 0 24 24" width="36" height="36">
                    <path
                      fill="currentColor"
                      d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6zm1 7V3.5L18.5 9H15zM8 13h8v2H8v-2zm0 4h5v2H8v-2z"
                    />
                  </svg>
                </span>
                <span className="mic-btn__label">
                  {fileBusy ? '转写中…' : '选择音频文件'}
                </span>
              </button>
              <p className="console__note">
                支持 mp3 / wav / m4a / webm 等格式。需在设置中配置 Whisper API Key。
              </p>
              <button
                type="button"
                className="ghost-btn"
                onClick={() => setSettingsOpen(true)}
              >
                配置 API Key
              </button>
            </div>
          )}
        </section>

        <section className="sheet" aria-label="转写结果">
          <div className="sheet__toolbar">
            <h2>转写文稿</h2>
            <div className="sheet__actions">
              <button
                type="button"
                className="btn"
                onClick={() => void copyText()}
                disabled={!transcript.trim()}
              >
                {copied ? '已复制' : '复制'}
              </button>
              <button
                type="button"
                className="btn"
                onClick={downloadText}
                disabled={!transcript.trim()}
              >
                下载 TXT
              </button>
              <button
                type="button"
                className="btn btn--ghost"
                onClick={clearAll}
                disabled={!transcript && !dictation.interim && recorder.status === 'idle'}
              >
                清空
              </button>
            </div>
          </div>
          <textarea
            className="sheet__editor"
            value={
              dictation.interim ? `${transcript}${dictation.interim}` : transcript
            }
            onChange={(e) => {
              if (isListening) return
              setTranscript(e.target.value)
            }}
            readOnly={isListening}
            placeholder="按下开始听写，说出的话会出现在这里…"
            spellCheck={false}
          />
          {dictation.interim && (
            <p className="sheet__interim-hint">末尾灰色语气词仍在识别中，停顿后会固化进文稿。</p>
          )}
        </section>
      </main>

      <footer className="footer">
        <p>
          实时听写基于浏览器 Web Speech API · 文件转写可选 OpenAI Whisper
        </p>
      </footer>

      <SettingsModal open={settingsOpen} onClose={() => setSettingsOpen(false)} />
    </div>
  )
}
