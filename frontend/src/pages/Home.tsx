import { useTranslation } from 'react-i18next'
export default function Home() {
  const { t } = useTranslation()
  return (<div>
    <h1 className="text-4xl font-bold">🛕 UtkalaYatri</h1>
    <p className="text-xl text-terracotta mb-4">{t('app_tagline')}</p>
    <p>Welcome to <b>UtkalaYatri</b> — your AI travel companion for <b>Odisha</b>.</p>
    <p className="text-xs text-gray-400 mt-8">Data: OpenStreetMap contributors · Wikipedia/Wikimedia Commons (CC BY-SA) · AI content provenance-tagged.</p>
  </div>)
}