'use client'

import { useState } from 'react'
import FileUpload from '@/components/FileUpload'
import QueryBox from '@/components/QueryBox'
import ReferenceList from '@/components/ReferenceList'
import { uploadPDF, getReferences, submitQuery, Reference } from '@/utils/api'

export default function Home() {
  const [references, setReferences] = useState<Reference[]>([])
  const [answer, setAnswer] = useState<string>('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string>('')

  const handleFileUpload = async (file: File) => {
    try {
      setIsLoading(true)
      setError('')
      await uploadPDF(file)
      const refs = await getReferences()
      setReferences(refs)
    } catch (err) {
      setError('Error processing PDF. Please try again.')
      console.error(err)
    } finally {
      setIsLoading(false)
    }
  }

  const handleQuery = async (query: string) => {
    try {
      setIsLoading(true)
      setError('')
      const response = await submitQuery(query)
      setAnswer(response.answer)
    } catch (err) {
      setError('Error processing query. Please try again.')
      console.error(err)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="space-y-8">
      <section>
        <h2 className="text-2xl font-bold mb-4">Upload Paper</h2>
        <FileUpload onFileUpload={handleFileUpload} />
      </section>

      {references.length > 0 && (
        <section>
          <h2 className="text-2xl font-bold mb-4">References</h2>
          <ReferenceList references={references} />
        </section>
      )}

      <section>
        <h2 className="text-2xl font-bold mb-4">Ask Questions</h2>
        <QueryBox onSubmit={handleQuery} isLoading={isLoading} />
        {answer && (
          <div className="mt-4 p-4 bg-gray-50 rounded-lg">
            <p className="text-gray-700">{answer}</p>
          </div>
        )}
      </section>

      {error && (
        <div className="p-4 bg-red-50 text-red-700 rounded-lg">
          {error}
        </div>
      )}

      {isLoading && (
        <div className="text-center py-4">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-4 border-gray-300 border-t-blue-600"></div>
        </div>
      )}
    </div>
  )
}
