import { Author, Section } from '@/utils/api'
import { colors } from '@/constants/colors'
import ReferenceExplorer from './ReferenceExplorer'
import { useState } from 'react'
import { Box, Tabs, Tab } from '@mui/material'
import SectionList from './SectionList'
import SourceView from './SourceView'

interface PaperDetailsProps {
  title: string
  authors: Author[]
  year?: string
  abstract?: string
  sections: Section[]
  sourceContent?: string
  onSectionClick?: (section: Section) => void
}

export default function PaperDetails({ 
  title, 
  authors, 
  year, 
  abstract,
  sections = [],
  sourceContent = '',
  onSectionClick
}: PaperDetailsProps) {
  const [activeTab, setActiveTab] = useState('sections')

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
      <Box sx={{ width: '100%', mt: 4 }}>
        <Tabs
          value={activeTab}
          onChange={(_, newValue) => setActiveTab(newValue)}
          aria-label="paper navigation"
        >
          <Tab label="Sections" value="sections" />
          <Tab label="References" value="references" />
          <Tab label="Source" value="source" />
        </Tabs>

        <Box sx={{ mt: 2 }}>
          {activeTab === 'sections' && (
            <SectionList sections={sections} onSectionClick={onSectionClick} />
          )}
          
          {activeTab === 'references' && (
            <ReferenceExplorer />
          )}
          
          {activeTab === 'source' && (
            <SourceView sources={[{
              text: sourceContent || '',
              section: 'Source',
              start_line: 1,
              end_line: sourceContent?.split('\n').length || 1,
              similarity: 1
            }]} />
          )}
        </Box>
      </Box>
    </div>
  )
} 