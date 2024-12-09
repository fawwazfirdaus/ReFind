import { useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { DocumentArrowUpIcon } from '@heroicons/react/24/outline'
import { colors } from '@/constants/colors'

interface FileUploadProps {
  onFileUpload: (file: File) => void
}

export default function FileUpload({ onFileUpload }: FileUploadProps) {
  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      onFileUpload(acceptedFiles[0])
    }
  }, [onFileUpload])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf']
    },
    maxFiles: 1
  })

  return (
    <div
      {...getRootProps()}
      style={{
        background: colors.surface,
        borderColor: isDragActive ? colors.primary : colors.border,
        backgroundColor: isDragActive ? `${colors.primary}10` : colors.surface
      }}
      className={`p-10 border-2 border-dashed rounded-lg text-center cursor-pointer`}
    >
      <input {...getInputProps()} />
      <DocumentArrowUpIcon style={{ color: colors.textSecondary }} className="mx-auto h-12 w-12" />
      <p style={{ color: colors.textSecondary }} className="mt-2 text-sm">
        {isDragActive
          ? "Drop the PDF here"
          : "Drag and drop a PDF file here, or click to select"}
      </p>
      <p style={{ color: colors.textSecondary }} className="mt-1 text-xs">
        Only PDF files are accepted
      </p>
    </div>
  )
} 