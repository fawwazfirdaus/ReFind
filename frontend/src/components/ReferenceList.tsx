import { Reference } from '@/utils/api'
import { colors } from '@/constants/colors'

interface ReferenceListProps {
  references: Reference[]
}

export default function ReferenceList({ references }: ReferenceListProps) {
  const formatAuthors = (authors: Reference['authors']) => {
    return authors.map(author => `${author.firstname} ${author.lastname}`).join(', ')
  }

  return (
    <div className="space-y-4">
      {references.map((ref, index) => (
        <div
          key={index}
          style={{ background: colors.surface }}
          className="p-4 rounded-lg shadow-sm"
        >
          <h3 style={{ color: colors.text }} className="text-lg font-semibold mb-2">
            {ref.title}
          </h3>
          <p style={{ color: colors.textSecondary }} className="text-sm mb-2">
            {formatAuthors(ref.authors)}
          </p>
          {ref.year && (
            <p style={{ color: colors.textSecondary }} className="text-sm mb-2">
              Year: {ref.year}
            </p>
          )}
          {ref.doi && (
            <p style={{ color: colors.textSecondary }} className="text-sm mb-2">
              DOI: <a href={`https://doi.org/${ref.doi}`} target="_blank" rel="noopener noreferrer" className="text-blue-500 hover:underline">{ref.doi}</a>
            </p>
          )}
          {ref.abstract && (
            <p style={{ color: colors.textSecondary }} className="text-sm mt-2">
              {ref.abstract}
            </p>
          )}
        </div>
      ))}
    </div>
  )
} 