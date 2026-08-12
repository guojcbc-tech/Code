export type RecognitionSupport = {
  supported: boolean
  SpeechRecognition: SpeechRecognitionStatic | null
}

export function getSpeechRecognition(): RecognitionSupport {
  const SpeechRecognitionCtor =
    window.SpeechRecognition ?? window.webkitSpeechRecognition ?? null
  return {
    supported: Boolean(SpeechRecognitionCtor),
    SpeechRecognition: SpeechRecognitionCtor,
  }
}

export const LANGUAGES = [
  { code: 'zh-CN', label: '中文（普通话）' },
  { code: 'zh-TW', label: '中文（台湾）' },
  { code: 'zh-HK', label: '中文（粤语）' },
  { code: 'en-US', label: 'English (US)' },
  { code: 'en-GB', label: 'English (UK)' },
  { code: 'ja-JP', label: '日本語' },
  { code: 'ko-KR', label: '한국어' },
  { code: 'fr-FR', label: 'Français' },
  { code: 'de-DE', label: 'Deutsch' },
  { code: 'es-ES', label: 'Español' },
] as const

export type LanguageCode = (typeof LANGUAGES)[number]['code']
