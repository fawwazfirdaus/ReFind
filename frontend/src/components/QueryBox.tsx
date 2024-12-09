import { useState, FormEvent } from 'react'
import { PaperAirplaneIcon } from '@heroicons/react/24/solid'

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
        className="flex-1 p-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        disabled={isLoading}
      />
      <button
        type="submit"
        disabled={!query.trim() || isLoading}
        className={`p-2 rounded-lg ${
          !query.trim() || isLoading
            ? 'bg-gray-300 cursor-not-allowed'
            : 'bg-blue-500 hover:bg-blue-600'
        }`}
      >
        <PaperAirplaneIcon className="h-5 w-5 text-white" />
      </button>
    </form>
  )
} 