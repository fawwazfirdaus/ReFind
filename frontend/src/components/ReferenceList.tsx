import { Reference } from '@/utils/api'
import { colors } from '@/constants/colors'
import { useEffect, useState } from 'react'
import { getReferencesStatus } from '@/utils/api'

interface ReferenceListProps {
  references: Reference[]
}

export default function ReferenceList({ references }: ReferenceListProps) {
  const [refsWithStatus, setRefsWithStatus] = useState<Reference[]>(references)
  const [isLoading, setIsLoading] = useState(false)

  const formatAuthors = (authors: Reference['authors']) => {
    return authors.map(author => `${author.firstname} ${author.lastname}`).join(', ')
  }

  const getStatusColor = (status?: string) => {
    switch (status) {
      case 'processed':
        return colors.success
      case 'pending':
        return colors.warning
      case 'failed':
        return colors.error
      default:
        return colors.textSecondary
    }
  }

  const getStatusText = (status?: string) => {
    switch (status) {
      case 'processed':
        return 'Available'
      case 'pending':
        return 'Processing...'
      case 'failed':
        return 'Failed to fetch'
      default:
        return 'Not processed'
    }
  }

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        setIsLoading(true)
        const status = await getReferencesStatus()
        
        // Update references with status
        const updatedRefs = references.map(ref => ({
          ...ref,
          status: status.references[ref.doi || ref.title]
        }))
        setRefsWithStatus(updatedRefs)
      } catch (error) {
        console.error('Error fetching reference status:', error)
      } finally {
        setIsLoading(false)
      }
    }

    fetchStatus()
    // Poll for status updates every 5 seconds
    const interval = setInterval(fetchStatus, 5000)
    return () => clearInterval(interval)
  }, [references])

  return (
    <div className="space-y-4">
      {isLoading && (
        <div className="text-center py-4">
          <div 
            className="inline-block animate-spin rounded-full h-8 w-8 border-4" 
            style={{ 
              borderColor: `${colors.border} transparent ${colors.border} transparent`
            }} 
          />
        </div>
      )}
      {refsWithStatus.map((ref, index) => (
        <div
          key={index}
          style={{ background: colors.surface }}
          className="p-4 rounded-lg shadow-sm"
        >
          <div className="flex justify-between items-start">
            <h3 style={{ color: colors.text }} className="text-lg font-semibold mb-2">
              {ref.title}
            </h3>
            <span 
              style={{ 
                color: getStatusColor(ref.status),
                backgroundColor: `${getStatusColor(ref.status)}20`
              }}
              className="text-sm font-medium px-2 py-1 rounded-full"
            >
              {getStatusText(ref.status)}
            </span>
          </div>
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
          {ref.status === 'processed' && (
            <button
              className="mt-2 px-3 py-1 rounded-lg text-sm hover:opacity-90"
              style={{ 
                background: colors.primary,
                color: colors.background
              }}
              onClick={() => {
                // TODO: Implement reference exploration
                console.log('Explore reference:', ref)
              }}
            >
              Explore Reference
            </button>
          )}
        </div>
      ))}
    </div>
  )
} 