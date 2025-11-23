import React, { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, X, File, AlertCircle, CheckCircle2, Loader2 } from 'lucide-react'
import { Card } from './ui/card'
import { Badge } from './ui/badge'

interface UploadedFile {
  file: File
  id: string
  status: 'pending' | 'uploading' | 'processing' | 'completed' | 'failed'
  progress: number
  error?: string
  transaction_id?: string
}

interface UploadModalProps {
  isOpen: boolean
  onClose: () => void
  onUploadComplete?: () => void
}

const MAX_FILE_SIZE = 10 * 1024 * 1024 // 10 MB
const ALLOWED_TYPES = ['application/pdf', 'image/jpeg', 'image/png', 'text/plain']

export function UploadModal({ isOpen, onClose, onUploadComplete }: UploadModalProps) {
  const [files, setFiles] = useState<UploadedFile[]>([])
  const [isUploading, setIsUploading] = useState(false)

  const onDrop = useCallback((acceptedFiles: File[], rejectedFiles: any[]) => {
    // Handle rejected files
    if (rejectedFiles.length > 0) {
      rejectedFiles.forEach(({ file, errors }) => {
        errors.forEach((error: any) => {
          if (error.code === 'file-too-large') {
            alert(`${file.name} exceeds 10 MB limit`)
          } else if (error.code === 'file-invalid-type') {
            alert(`${file.name} is not a supported file type`)
          }
        })
      })
    }

    // Add accepted files
    const newFiles: UploadedFile[] = acceptedFiles.map((file) => ({
      file,
      id: crypto.randomUUID(),
      status: 'pending',
      progress: 0,
    }))

    setFiles((prev) => [...prev, ...newFiles])
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'image/jpeg': ['.jpg', '.jpeg'],
      'image/png': ['.png'],
      'text/plain': ['.txt'],
    },
    maxSize: MAX_FILE_SIZE,
    maxFiles: 5,
  })

  const removeFile = (id: string) => {
    setFiles((prev) => prev.filter((f) => f.id !== id))
  }

  const handleUpload = async () => {
    if (files.length === 0) return

    setIsUploading(true)

    for (const uploadedFile of files) {
      if (uploadedFile.status !== 'pending') continue

      try {
        // Update status to uploading
        setFiles((prev) =>
          prev.map((f) =>
            f.id === uploadedFile.id ? { ...f, status: 'uploading', progress: 0 } : f
          )
        )

        // Import upload function
        const { uploadFile } = await import('../services/fileUploadService')

        // Upload file
        await uploadFile(
          uploadedFile.file,
          (progress) => {
            setFiles((prev) =>
              prev.map((f) =>
                f.id === uploadedFile.id ? { ...f, progress } : f
              )
            )
          },
          (status) => {
            setFiles((prev) =>
              prev.map((f) =>
                f.id === uploadedFile.id ? { ...f, status } : f
              )
            )
          }
        )

      } catch (error: any) {
        console.error('Upload error:', error)
        setFiles((prev) =>
          prev.map((f) =>
            f.id === uploadedFile.id
              ? { ...f, status: 'failed', error: error.message }
              : f
          )
        )
      }
    }

    setIsUploading(false)

    // Check if all uploads completed successfully
    const allCompleted = files.every((f) => f.status === 'completed')
    if (allCompleted && onUploadComplete) {
      onUploadComplete()
    }
  }

  const getStatusIcon = (status: UploadedFile['status']) => {
    switch (status) {
      case 'uploading':
      case 'processing':
        return <Loader2 className="w-4 h-4 animate-spin" />
      case 'completed':
        return <CheckCircle2 className="w-4 h-4 text-green-600" />
      case 'failed':
        return <AlertCircle className="w-4 h-4 text-red-600" />
      default:
        return <File className="w-4 h-4" />
    }
  }

  const getStatusBadge = (status: UploadedFile['status']) => {
    switch (status) {
      case 'uploading':
        return <Badge variant="default">Uploading...</Badge>
      case 'processing':
        return <Badge variant="default">Processing...</Badge>
      case 'completed':
        return <Badge variant="success">Completed</Badge>
      case 'failed':
        return <Badge variant="error">Failed</Badge>
      default:
        return <Badge variant="default">Pending</Badge>
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <Card className="w-full max-w-2xl max-h-[90vh] overflow-hidden shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b bg-gradient-to-r from-blue-600 to-purple-600 text-white">
          <div className="flex items-center gap-3">
            <Upload className="w-6 h-6" />
            <h2 className="text-xl font-bold">Upload Contract Documents</h2>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-white/20 transition-colors"
            disabled={isUploading}
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-180px)]">
          {/* Dropzone */}
          <div
            {...getRootProps()}
            className={`
              border-2 border-dashed rounded-xl p-12 text-center cursor-pointer
              transition-all duration-200
              ${
                isDragActive
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-300 hover:border-blue-400 hover:bg-gray-50'
              }
            `}
          >
            <input {...getInputProps()} />
            <Upload className={`w-16 h-16 mx-auto mb-4 ${isDragActive ? 'text-blue-500' : 'text-gray-400'}`} />
            {isDragActive ? (
              <p className="text-lg font-medium text-blue-600">Drop files here...</p>
            ) : (
              <>
                <p className="text-lg font-medium text-gray-700 mb-2">
                  Drag & drop files here, or click to browse
                </p>
                <p className="text-sm text-gray-500">
                  Supported: PDF, JPG, PNG, TXT • Max size: 10 MB • Up to 5 files
                </p>
              </>
            )}
          </div>

          {/* Selected Files List */}
          {files.length > 0 && (
            <div className="mt-6 space-y-3">
              <h3 className="font-semibold text-gray-700">Selected Files ({files.length})</h3>
              {files.map((uploadedFile) => (
                <Card key={uploadedFile.id} className="p-4">
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-3 flex-1">
                      {getStatusIcon(uploadedFile.status)}
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-sm truncate">{uploadedFile.file.name}</p>
                        <p className="text-xs text-gray-500">{formatFileSize(uploadedFile.file.size)}</p>
                        {uploadedFile.error && (
                          <p className="text-xs text-red-600 mt-1">{uploadedFile.error}</p>
                        )}
                        {uploadedFile.status === 'uploading' && (
                          <div className="mt-2 w-full bg-gray-200 rounded-full h-2">
                            <div
                              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                              style={{ width: `${uploadedFile.progress}%` }}
                            />
                          </div>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-2 ml-4">
                      {getStatusBadge(uploadedFile.status)}
                      {uploadedFile.status === 'pending' && (
                        <button
                          onClick={() => removeFile(uploadedFile.id)}
                          className="p-1 rounded hover:bg-gray-100"
                          disabled={isUploading}
                        >
                          <X className="w-4 h-4" />
                        </button>
                      )}
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 p-6 border-t bg-gray-50">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-lg border border-gray-300 hover:bg-gray-100 transition-colors"
            disabled={isUploading}
          >
            Cancel
          </button>
          <button
            onClick={handleUpload}
            disabled={files.length === 0 || isUploading}
            className="px-6 py-2 rounded-lg bg-gradient-to-r from-blue-600 to-purple-600 text-white font-medium hover:shadow-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {isUploading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Uploading...
              </>
            ) : (
              <>
                <Upload className="w-4 h-4" />
                Upload {files.length} {files.length === 1 ? 'File' : 'Files'}
              </>
            )}
          </button>
        </div>
      </Card>
    </div>
  )
}
