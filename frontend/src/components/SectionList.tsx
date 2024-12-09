import { Section } from '@/utils/api'
import { colors } from '@/constants/colors'
import { useState } from 'react'

interface SectionListProps {
  sections?: Section[]
}

export default function SectionList({ sections = [] }: SectionListProps) {
  const [expandedSection, setExpandedSection] = useState<number | null>(null)

  const toggleSection = (index: number) => {
    setExpandedSection(expandedSection === index ? null : index)
  }

  if (!sections || sections.length === 0) {
    return (
      <div 
        style={{ background: colors.surface }} 
        className="p-4 rounded-lg text-center"
      >
        <p style={{ color: colors.textSecondary }}>No sections found in the paper.</p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {sections.map((section, index) => (
        <div
          key={index}
          style={{ background: colors.surface }}
          className="rounded-lg shadow-sm overflow-hidden"
        >
          <button
            onClick={() => toggleSection(index)}
            className="w-full p-4 text-left flex justify-between items-center"
            style={{ color: colors.text }}
          >
            <h3 className="text-lg font-semibold">
              {section.title || 'Untitled Section'}
            </h3>
            <span className="text-2xl transition-transform duration-200" style={{
              transform: expandedSection === index ? 'rotate(180deg)' : 'rotate(0deg)'
            }}>
              ▼
            </span>
          </button>
          {expandedSection === index && (
            <div 
              className="p-4 border-t"
              style={{ borderColor: colors.border }}
            >
              <div 
                style={{ color: colors.textSecondary }}
                className="prose max-w-none"
              >
                {(section.content || '').split('\n').map((paragraph, i) => (
                  <p key={i} className="mb-4 last:mb-0">
                    {paragraph}
                  </p>
                ))}
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  )
} 