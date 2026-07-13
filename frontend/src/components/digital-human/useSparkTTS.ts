import { useCallback, useEffect, useRef, useState } from 'react'
import { ttsApi } from '@/services/api'

type TtsSource = 'checking' | 'iflytek' | 'browser'
export type TtsGender = 'male' | 'female'

const IFLYTEK_VOICE_BY_GENDER: Record<TtsGender, string> = {
  male: 'aisjiuxu',
  female: 'aisjinger',
}

const BROWSER_VOICE_HINTS: Record<TtsGender, string[]> = {
  male: ['yunxi', 'yunyang', 'kangkang', 'zhiwei', 'yunjian', 'male', '男'],
  female: ['xiaoxiao', 'xiaoyi', 'xiaomeng', 'xiaoxuan', 'huihui', 'yaoyao', 'female', '女'],
}

function pickChineseVoice(voices: SpeechSynthesisVoice[], gender: TtsGender) {
  const zhVoices = voices.filter((voice) => voice.lang.toLowerCase().startsWith('zh'))
  const hints = BROWSER_VOICE_HINTS[gender]
  return (
    zhVoices.find((voice) => {
      const name = voice.name.toLowerCase()
      return hints.some((hint) => name.includes(hint))
    }) ||
    zhVoices[0] ||
    voices[0]
  )
}

export function useSparkTTS() {
  const [speaking, setSpeaking] = useState(false)
  const [sparkAvailable, setSparkAvailable] = useState<boolean | null>(null)
  const [source, setSource] = useState<TtsSource>('checking')
  const [lastError, setLastError] = useState('')
  const audioRef = useRef<HTMLAudioElement | null>(null)
  const objectUrlRef = useRef<string>('')

  useEffect(() => {
    ttsApi
      .status()
      .then((response) => {
        const available = Boolean(response.data.tts_available)
        setSparkAvailable(available)
        setSource(available ? 'iflytek' : 'browser')
      })
      .catch(() => {
        setSparkAvailable(false)
        setSource('browser')
      })
  }, [])

  const clearObjectUrl = useCallback(() => {
    if (objectUrlRef.current) {
      URL.revokeObjectURL(objectUrlRef.current)
      objectUrlRef.current = ''
    }
  }, [])

  const stop = useCallback(() => {
    audioRef.current?.pause()
    audioRef.current = null
    clearObjectUrl()
    window.speechSynthesis?.cancel()
    setSpeaking(false)
  }, [clearObjectUrl])

  useEffect(() => stop, [stop])

  const speakWithBrowser = useCallback(
    (text: string, speed: number, gender: TtsGender) => {
      const synth = window.speechSynthesis
      if (!synth) {
        setLastError('当前浏览器不支持语音朗读')
        return
      }

      const utterance = new SpeechSynthesisUtterance(text)
      utterance.lang = 'zh-CN'
      utterance.rate = Math.max(0.5, Math.min(2, speed / 50))
      utterance.pitch = gender === 'male' ? 0.78 : 1.08
      utterance.volume = 1

      const voices = synth.getVoices()
      const zhVoice = pickChineseVoice(voices, gender)
      if (zhVoice) utterance.voice = zhVoice

      utterance.onend = () => setSpeaking(false)
      utterance.onerror = () => {
        setSpeaking(false)
        setLastError('浏览器语音朗读失败')
      }

      synth.speak(utterance)
      setSource('browser')
      setSpeaking(true)
    },
    [],
  )

  const speak = useCallback(
    async (text: string, speed: number = 50, gender: TtsGender = 'female', voiceName?: string) => {
      const cleanText = text.trim()
      if (!cleanText) return

      stop()
      setLastError('')

      if (sparkAvailable) {
        try {
          const response = await ttsApi.synthesize(cleanText, speed, voiceName || IFLYTEK_VOICE_BY_GENDER[gender])
          const blob = response.data as Blob
          if (!blob || blob.size < 128) throw new Error('后端未返回有效音频')

          const url = URL.createObjectURL(blob)
          objectUrlRef.current = url
          const audio = new Audio(url)
          audioRef.current = audio
          audio.onended = () => {
            setSpeaking(false)
            clearObjectUrl()
          }
          audio.onerror = () => {
            setSpeaking(false)
            setLastError('讯飞音频播放失败，已尝试浏览器朗读')
            clearObjectUrl()
            speakWithBrowser(cleanText, speed, gender)
          }

          await audio.play()
          setSource('iflytek')
          setSpeaking(true)
          return
        } catch (error) {
          setLastError(error instanceof Error ? error.message : '讯飞 TTS 调用失败，已回退浏览器语音')
          setSparkAvailable(false)
          setSource('browser')
        }
      }

      speakWithBrowser(cleanText, speed, gender)
    },
    [clearObjectUrl, sparkAvailable, speakWithBrowser, stop],
  )

  return { speaking, sparkAvailable, source, lastError, speak, stop }
}
