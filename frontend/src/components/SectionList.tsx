import { Section } from '@/utils/api'

export interface SectionListProps {
  sections: Section[]
  onSectionClick?: (section: Section) => void
}

export default function SectionList({ sections, onSectionClick }: SectionListProps) {
  return (
    <div className="space-y-4">
      {sections.map((section, index) => (
        <div
          key={index}
          onClick={() => onSectionClick?.(section)}
          className="cursor-pointer hover:bg-gray-100 p-4 rounded"
        >
          <h3 className="font-semibold mb-2">{section.title}</h3>
          <p className="text-gray-600">{section.content}</p>
        </div>
      ))}
    </div>
  )
} 