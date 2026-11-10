export const HERO_IMAGE = "/hero.jpg"; // put hero.jpg in frontend/public/ — or paste an https:// URL
import { useTranslation } from 'react-i18next'
export default function Placeholder({ page }: { page: string }) {
  const { t } = useTranslation()
  return (
    <div className="text-center py-20">
      <h1 className="text-3xl font-bold mb-2">{t(`nav_${page}`)}</h1>
      <p className="text-gray-500">🚧 Phase B part 2 — coming next.</p>
    </div>
  )
}