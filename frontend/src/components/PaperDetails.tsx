import { Author } from '@/utils/api'
import { colors } from '@/constants/colors'

interface PaperDetailsProps {
  title: string
  authors: Author[]
  year?: string
  abstract?: string
}

export default function PaperDetails({ title, authors, year, abstract }: PaperDetailsProps) {
  const formatAuthors = (authors: Author[]) => {
    return authors.map(author => {
      const name = `${author.firstname} ${author.lastname}`
      const affiliation = author.affiliation ? ` (${author.affiliation})` : ''
      return (
        <div key={name} className="mb-2">
          <span className="font-medium">{name}</span>
          {affiliation}
          {author.orcid && (
            <a
              href={`https://orcid.org/${author.orcid}`}
              target="_blank"
              rel="noopener noreferrer"
              className="ml-2 text-blue-500 hover:underline"
            >
              ORCID
            </a>
          )}
          {author.email && (
            <a
              href={`mailto:${author.email}`}
              className="ml-2 text-blue-500 hover:underline"
            >
              ✉️
            </a>
          )}
        </div>
      )
    })
  }

  return (
    <div style={{ background: colors.surface }} className="p-6 rounded-lg shadow-sm">
      <h2 style={{ color: colors.text }} className="text-2xl font-bold mb-4">
        {title}
      </h2>
      <div className="space-y-4">
        <div>
          <h3 style={{ color: colors.text }} className="text-lg font-semibold mb-2">
            Authors
          </h3>
          <div style={{ color: colors.textSecondary }} className="text-base">
            {formatAuthors(authors)}
          </div>
        </div>
        
        {year && (
          <div>
            <h3 style={{ color: colors.text }} className="text-lg font-semibold mb-2">
              Year
            </h3>
            <p style={{ color: colors.textSecondary }} className="text-base">
              {year}
            </p>
          </div>
        )}
        
        {abstract && (
          <div>
            <h3 style={{ color: colors.text }} className="text-lg font-semibold mb-2">
              Abstract
            </h3>
            <p style={{ color: colors.textSecondary }} className="text-base leading-relaxed">
              {abstract}
            </p>
          </div>
        )}
      </div>
    </div>
  )
} 