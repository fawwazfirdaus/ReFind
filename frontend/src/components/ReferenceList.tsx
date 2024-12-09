interface Reference {
  title: string
  authors: string[]
  doi?: string
  abstract?: string
}

interface ReferenceListProps {
  references: Reference[]
}

export default function ReferenceList({ references }: ReferenceListProps) {
  if (references.length === 0) {
    return (
      <div className="text-center py-10 text-gray-500">
        No references found
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {references.map((ref, index) => (
        <div
          key={index}
          className="p-4 border rounded-lg hover:shadow-md transition-shadow"
        >
          <h3 className="font-medium text-lg">{ref.title}</h3>
          <p className="text-sm text-gray-600 mt-1">
            {ref.authors.join(', ')}
          </p>
          {ref.doi && (
            <a
              href={`https://doi.org/${ref.doi}`}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm text-blue-500 hover:underline mt-1 block"
            >
              DOI: {ref.doi}
            </a>
          )}
          {ref.abstract && (
            <p className="text-sm text-gray-700 mt-2">
              {ref.abstract}
            </p>
          )}
        </div>
      ))}
    </div>
  )
} 