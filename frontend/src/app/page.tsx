'use client'

import { useState } from 'react'
import FileUpload from '@/components/FileUpload'
import QueryBox from '@/components/QueryBox'
import ReferenceList from '@/components/ReferenceList'
import PaperDetails from '@/components/PaperDetails'
import SectionList from '@/components/SectionList'
import Modal from '@/components/Modal'
import SourceView from '@/components/SourceView'
import { uploadPDF, submitQuery, Paper, TokenUsage, SourceInfo } from '@/utils/api'
import { colors } from '@/constants/colors'

interface QueryMetadata {
  chunks_used: number
  token_usage: TokenUsage
  sources: SourceInfo[]
}

export default function Home() {
  const [paper, setPaper] = useState<Paper | null>(null)
  const [answer, setAnswer] = useState<string>('')
  const [queryMetadata, setQueryMetadata] = useState<QueryMetadata | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string>('')
  
  // Modal states
  const [showSections, setShowSections] = useState(false)
  const [showReferences, setShowReferences] = useState(false)
  const [showQueryDetails, setShowQueryDetails] = useState(false)

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
      setQueryMetadata(response.metadata)
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
                sections={paper.sections || []}
                sourceContent={paper.sourceContent}
              />
              
              <div className="mt-4 space-x-4">
                <button
                  onClick={() => setShowSections(true)}
                  style={{ background: colors.primary, color: colors.text }}
                  className="px-4 py-2 rounded-lg hover:opacity-90"
                >
                  View Sections
                </button>
                <button
                  onClick={() => setShowReferences(true)}
                  style={{ background: colors.primary, color: colors.text }}
                  className="px-4 py-2 rounded-lg hover:opacity-90"
                >
                  View References
                </button>
              </div>
            </section>

            {/* Sections Modal */}
            <Modal
              isOpen={showSections}
              onClose={() => setShowSections(false)}
              title="Paper Sections"
            >
              <SectionList sections={paper.sections} />
            </Modal>

            {/* References Modal */}
            <Modal
              isOpen={showReferences}
              onClose={() => setShowReferences(false)}
              title="References"
            >
              <ReferenceList references={paper.references} />
            </Modal>
          </>
        )}

        <section style={{ background: colors.background }}>
          <h2 style={{ color: colors.text }} className="text-2xl font-bold mb-4">Ask Questions</h2>
          <QueryBox onSubmit={handleQuery} isLoading={isLoading} />
          {answer && (
            <div className="space-y-4">
              <div style={{ background: colors.surface }} className="p-4 rounded-lg">
                <p style={{ color: colors.text }}>{answer}</p>
                {queryMetadata && (
                  <button
                    onClick={() => setShowQueryDetails(true)}
                    style={{ color: colors.primary }}
                    className="mt-2 text-sm hover:underline"
                  >
                    View Query Details
                  </button>
                )}
              </div>

              {/* Query Details Modal */}
              <Modal
                isOpen={showQueryDetails}
                onClose={() => setShowQueryDetails(false)}
                title="Query Details"
              >
                <div className="space-y-6">
                  <div style={{ color: colors.textSecondary }} className="space-y-2">
                    <h4 style={{ color: colors.text }} className="text-lg font-semibold">Statistics</h4>
                    <p>Chunks used: {queryMetadata?.chunks_used}</p>
                    <p className="font-medium mt-4">Token Usage:</p>
                    <ul className="list-disc list-inside pl-4">
                      <li>Prompt: {queryMetadata?.token_usage.prompt_tokens}</li>
                      <li>Completion: {queryMetadata?.token_usage.completion_tokens}</li>
                      <li>Total: {queryMetadata?.token_usage.total_tokens}</li>
                    </ul>
                  </div>

                  <div>
                    <h4 style={{ color: colors.text }} className="text-lg font-semibold mb-4">Source Chunks</h4>
                    {queryMetadata?.sources && <SourceView sources={queryMetadata.sources} />}
                  </div>
                </div>
              </Modal>
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
