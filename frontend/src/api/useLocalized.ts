import { useEffect, useState } from 'react'
import { api } from './client'
import { useTranslation } from 'react-i18next'

/**
 * On-demand AI translation of content (place descriptions etc.).
 * Returns [text, wasTranslated]. English → passthrough, no call.
 * Failures silently fall back to the original text (demo-safe).
 */
export function useLocalized(text: string | undefined): [string, boolean] {
  const { i18n } = useTranslation()
  const lang = i18n.language === 'or' ? 'or' : i18n.language === 'hi' ? 'hi' : 'en'
  const [state, setState] = useState<[string, boolean]>([text ?? '', false])

  useEffect(() => {
    if (!text) { setState(['', false]); return }
    if (lang === 'en') { setState([text, false]); return }
    let alive = true                       // avoid setState-after-unmount
    api.translate(text, lang)
      .then(r => { if (alive) setState([r.text, r.was_translated]) })
      .catch(() => { if (alive) setState([text, false]) })
    return () => { alive = false }
  }, [text, lang])

  return state
}