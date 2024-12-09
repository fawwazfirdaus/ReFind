import { useState, FormEvent } from 'react'
import { PaperAirplaneIcon } from '@heroicons/react/24/solid'
import { colors } from '@/constants/colors'

interface QueryBoxProps {
  onSubmit: (query: string) => void
  isLoading?: boolean
}

export default function QueryBox({ onSubmit, isLoading = false }: QueryBoxProps) {
  const [query, setQuery] = useState('')

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    if (query.trim() && !isLoading) {
      onSubmit(query.trim())
      setQuery('')
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex space-x-2">
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Ask a question about the paper..."
        style={{
          background: colors.background,
          borderColor: colors.border,
          color: colors.text,
        }}
        className="flex-1 p-2 border rounded-lg focus:outline-none focus:ring-2"
        disabled={isLoading}
      />
      <button
        type="submit"
        disabled={!query.trim() || isLoading}
        style={{
          backgroundColor: !query.trim() || isLoading ? colors.border : colors.primary,
          color: !query.trim() || isLoading ? colors.textSecondary : colors.background,
        }}
        className="p-2 rounded-lg"
      >
        <PaperAirplaneIcon className="h-5 w-5" />
      </button>
    </form>
  )
} 