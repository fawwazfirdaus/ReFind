'use client'

import { useState } from 'react'
import FileUpload from '@/components/FileUpload'
import QueryBox from '@/components/QueryBox'
import ReferenceList from '@/components/ReferenceList'
import PaperDetails from '@/components/PaperDetails'
import SectionList from '@/components/SectionList'
import { uploadPDF, getReferences, submitQuery, Paper } from '@/utils/api'
import { colors } from '@/constants/colors'

export default function Home() {
  const [paper, setPaper] = useState<Paper | null>(null)
  const [answer, setAnswer] = useState<string>('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string>('')

  const handleFileUpload = async (file: File) => {
    try {
      setIsLoading(true)
      setError('')
      const paperData = await uploadPDF(file)
      setPaper(paperData)
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
    <div style={{ background: colors.background, minHeight: '100vh' }}>
      <div className="space-y-8 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8" style={{ background: colors.background }}>
        <section style={{ background: colors.background }}>
          <h2 style={{ color: colors.text }} className="text-2xl font-bold mb-4">Upload Paper</h2>
          <FileUpload onFileUpload={handleFileUpload} />
        </section>

        {paper && (
          <>
            <section style={{ background: colors.background }}>
              <h2 style={{ color: colors.text }} className="text-2xl font-bold mb-4">Paper Details</h2>
              <PaperDetails
                title={paper.title}
                authors={paper.authors}
                year={paper.year}
                abstract={paper.abstract}
              />
            </section>

            <section style={{ background: colors.background }}>
              <h2 style={{ color: colors.text }} className="text-2xl font-bold mb-4">Sections</h2>
              <SectionList sections={paper.sections} />
            </section>

            <section style={{ background: colors.background }}>
              <h2 style={{ color: colors.text }} className="text-2xl font-bold mb-4">References</h2>
              <ReferenceList references={paper.references} />
            </section>
          </>
        )}

        <section style={{ background: colors.background }}>
          <h2 style={{ color: colors.text }} className="text-2xl font-bold mb-4">Ask Questions</h2>
          <QueryBox onSubmit={handleQuery} isLoading={isLoading} />
          {answer && (
            <div style={{ background: colors.surface }} className="mt-4 p-4 rounded-lg">
              <p style={{ color: colors.text }}>{answer}</p>
            </div>
          )}
        </section>

        {error && (
          <div style={{ background: `${colors.error}10`, color: colors.error }} className="p-4 rounded-lg">
            {error}
          </div>
        )}

        {isLoading && (
          <div className="text-center py-4">
            <div 
              className="inline-block animate-spin rounded-full h-8 w-8 border-4" 
              style={{ 
                borderColor: colors.border,
                borderTopColor: colors.primary 
              }}
            />
          </div>
        )}
      </div>
    </div>
  )
}
