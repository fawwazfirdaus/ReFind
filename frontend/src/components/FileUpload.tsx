import { useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { DocumentArrowUpIcon } from '@heroicons/react/24/outline'

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
      className={`p-10 border-2 border-dashed rounded-lg text-center cursor-pointer
        ${isDragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-gray-400'}`}
    >
      <input {...getInputProps()} />
      <DocumentArrowUpIcon className="mx-auto h-12 w-12 text-gray-400" />
      <p className="mt-2 text-sm text-gray-600">
        {isDragActive
          ? "Drop the PDF here"
          : "Drag and drop a PDF file here, or click to select"}
      </p>
      <p className="mt-1 text-xs text-gray-500">
        Only PDF files are accepted
      </p>
    </div>
  )
} 