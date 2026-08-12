import { useCallback, useEffect, useRef, useState } from 'react'
import { getSpeechRecognition, type LanguageCode } from '../lib/speech'

export type DictationStatus = 'idle' | 'listening' | 'paused'

type UseDictationOptions = {
  lang: LanguageCode
  onFinal?: (text: string) => void
}

export function useDictation({ lang, onFinal }: UseDictationOptions) {
  const [status, setStatus] = useState<DictationStatus>('idle')
  const [interim, setInterim] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [supported] = useState(() => getSpeechRecognition().supported)

  const recognitionRef = useRef<SpeechRecognition | null>(null)
  const shouldRunRef = useRef(false)
  const onFinalRef = useRef(onFinal)
  onFinalRef.current = onFinal

  const cleanup = useCallback(() => {
    const rec = recognitionRef.current
    recognitionRef.current = null
    if (rec) {
      rec.onresult = null
      rec.onerror = null
      rec.onend = null
      try {
        rec.abort()
      } catch {
        /* ignore */
      }
    }
  }, [])

  const start = useCallback(() => {
    setError(null)
    const { SpeechRecognition: Ctor } = getSpeechRecognition()
    if (!Ctor) {
      setError('当前浏览器不支持语音识别，请使用 Chrome / Edge。')
      return
    }

    cleanup()
    const recognition = new Ctor()
    recognition.continuous = true
    recognition.interimResults = true
    recognition.lang = lang
    recognition.maxAlternatives = 1

    recognition.onresult = (event: SpeechRecognitionEvent) => {
      let interimText = ''
      let finalChunk = ''
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const result = event.results[i]
        const transcript = result[0]?.transcript ?? ''
        if (result.isFinal) {
          finalChunk += transcript
        } else {
          interimText += transcript
        }
      }
      setInterim(interimText)
      if (finalChunk) {
        onFinalRef.current?.(finalChunk)
      }
    }

    recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
      if (event.error === 'aborted' || event.error === 'no-speech') return
      if (event.error === 'not-allowed') {
        setError('麦克风权限被拒绝，请在浏览器设置中允许访问。')
        shouldRunRef.current = false
        setStatus('idle')
        return
      }
      setError(`识别出错：${event.error}`)
    }

    recognition.onend = () => {
      if (shouldRunRef.current) {
        try {
          recognition.start()
        } catch {
          setStatus('idle')
          shouldRunRef.current = false
        }
      } else {
        setStatus('idle')
        setInterim('')
      }
    }

    recognitionRef.current = recognition
    shouldRunRef.current = true
    setStatus('listening')
    try {
      recognition.start()
    } catch {
      setError('无法启动语音识别，请刷新页面重试。')
      shouldRunRef.current = false
      setStatus('idle')
    }
  }, [cleanup, lang])

  const stop = useCallback(() => {
    shouldRunRef.current = false
    setStatus('idle')
    setInterim('')
    const rec = recognitionRef.current
    if (rec) {
      try {
        rec.stop()
      } catch {
        cleanup()
      }
    }
  }, [cleanup])

  const pause = useCallback(() => {
    shouldRunRef.current = false
    setStatus('paused')
    setInterim('')
    const rec = recognitionRef.current
    if (rec) {
      try {
        rec.stop()
      } catch {
        /* ignore */
      }
    }
  }, [])

  const resume = useCallback(() => {
    if (status === 'paused') start()
  }, [start, status])

  useEffect(() => {
    return () => {
      shouldRunRef.current = false
      cleanup()
    }
  }, [cleanup])

  return {
    supported,
    status,
    interim,
    error,
    start,
    stop,
    pause,
    resume,
    setError,
  }
}
