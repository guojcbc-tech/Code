import { useCallback, useEffect, useRef, useState } from 'react'

export type RecorderStatus = 'idle' | 'recording' | 'stopped'

function pickMimeType(): string {
  const candidates = [
    'audio/webm;codecs=opus',
    'audio/webm',
    'audio/mp4',
    'audio/ogg',
  ]
  for (const type of candidates) {
    if (MediaRecorder.isTypeSupported(type)) return type
  }
  return ''
}

export function useAudioRecorder() {
  const [status, setStatus] = useState<RecorderStatus>('idle')
  const [blob, setBlob] = useState<Blob | null>(null)
  const [url, setUrl] = useState<string | null>(null)
  const [levels, setLevels] = useState<number[]>(() => Array(24).fill(0.08))
  const [error, setError] = useState<string | null>(null)
  const [elapsedMs, setElapsedMs] = useState(0)

  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const chunksRef = useRef<Blob[]>([])
  const streamRef = useRef<MediaStream | null>(null)
  const audioCtxRef = useRef<AudioContext | null>(null)
  const analyserRef = useRef<AnalyserNode | null>(null)
  const rafRef = useRef<number | null>(null)
  const timerRef = useRef<number | null>(null)
  const startedAtRef = useRef(0)

  const stopVisuals = useCallback(() => {
    if (rafRef.current != null) {
      cancelAnimationFrame(rafRef.current)
      rafRef.current = null
    }
    if (timerRef.current != null) {
      window.clearInterval(timerRef.current)
      timerRef.current = null
    }
    setLevels(Array(24).fill(0.08))
  }, [])

  const releaseStream = useCallback(() => {
    streamRef.current?.getTracks().forEach((t) => t.stop())
    streamRef.current = null
    void audioCtxRef.current?.close()
    audioCtxRef.current = null
    analyserRef.current = null
  }, [])

  const start = useCallback(async () => {
    setError(null)
    setBlob(null)
    if (url) {
      URL.revokeObjectURL(url)
      setUrl(null)
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
        },
      })
      streamRef.current = stream

      const audioCtx = new AudioContext()
      audioCtxRef.current = audioCtx
      const source = audioCtx.createMediaStreamSource(stream)
      const analyser = audioCtx.createAnalyser()
      analyser.fftSize = 64
      source.connect(analyser)
      analyserRef.current = analyser

      const data = new Uint8Array(analyser.frequencyBinCount)
      const tick = () => {
        analyser.getByteFrequencyData(data)
        const bars = Array.from({ length: 24 }, (_, i) => {
          const idx = Math.floor((i / 24) * data.length)
          return Math.max(0.08, data[idx]! / 255)
        })
        setLevels(bars)
        rafRef.current = requestAnimationFrame(tick)
      }
      rafRef.current = requestAnimationFrame(tick)

      const mimeType = pickMimeType()
      const recorder = new MediaRecorder(
        stream,
        mimeType ? { mimeType } : undefined,
      )
      chunksRef.current = []
      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data)
      }
      recorder.onstop = () => {
        const type = recorder.mimeType || 'audio/webm'
        const next = new Blob(chunksRef.current, { type })
        setBlob(next)
        setUrl(URL.createObjectURL(next))
        setStatus('stopped')
        stopVisuals()
        releaseStream()
      }

      mediaRecorderRef.current = recorder
      recorder.start(250)
      startedAtRef.current = Date.now()
      setElapsedMs(0)
      timerRef.current = window.setInterval(() => {
        setElapsedMs(Date.now() - startedAtRef.current)
      }, 200)
      setStatus('recording')
    } catch {
      setError('无法访问麦克风，请检查权限设置。')
      stopVisuals()
      releaseStream()
      setStatus('idle')
    }
  }, [releaseStream, stopVisuals, url])

  const stop = useCallback(() => {
    const recorder = mediaRecorderRef.current
    if (recorder && recorder.state !== 'inactive') {
      recorder.stop()
    } else {
      setStatus('idle')
      stopVisuals()
      releaseStream()
    }
  }, [releaseStream, stopVisuals])

  const reset = useCallback(() => {
    if (url) URL.revokeObjectURL(url)
    setUrl(null)
    setBlob(null)
    setElapsedMs(0)
    setStatus('idle')
  }, [url])

  useEffect(() => {
    return () => {
      stopVisuals()
      releaseStream()
      if (url) URL.revokeObjectURL(url)
    }
  }, [releaseStream, stopVisuals, url])

  return {
    status,
    blob,
    url,
    levels,
    error,
    elapsedMs,
    start,
    stop,
    reset,
  }
}
