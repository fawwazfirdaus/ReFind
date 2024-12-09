import { SourceInfo } from '@/utils/api'
import { colors } from '@/constants/colors'

export interface SourceViewProps {
  sources: SourceInfo[]
}

export default function SourceView({ sources }: SourceViewProps) {
  return (
    <div className="space-y-4">
      {sources.map((source, index) => (
        <div
          key={index}
          style={{ background: colors.surface, borderColor: colors.border }}
          className="p-4 rounded-lg border"
        >
          <div className="flex justify-between items-start mb-2">
            <div>
              <h4 style={{ color: colors.text }} className="font-semibold">
                {source.section}
              </h4>
              <p style={{ color: colors.textSecondary }} className="text-sm">
                Lines {source.start_line}-{source.end_line}
              </p>
            </div>
            <span style={{ color: colors.primary }} className="text-sm font-medium">
              {(source.similarity * 100).toFixed(1)}% match
            </span>
          </div>
          <div
            style={{ color: colors.textSecondary, borderColor: colors.border }}
            className="mt-2 pt-2 border-t text-sm"
          >
            <pre className="whitespace-pre-wrap font-sans">{source.text}</pre>
          </div>
        </div>
      ))}
    </div>
  )
} 