import { supabase } from '../supabaseClient'

const N8N_WEBHOOK_URL = import.meta.env.VITE_N8N_WEBHOOK_URL || 'https://jerbud.app.n8n.cloud/webhook/contract-upload'
const STORAGE_BUCKET = import.meta.env.VITE_SUPABASE_STORAGE_BUCKET || 'contract-uploads'
const POLL_INTERVAL = parseInt(import.meta.env.VITE_STATUS_POLL_INTERVAL_MS || '2000')
const MAX_POLL_ATTEMPTS = parseInt(import.meta.env.VITE_MAX_POLL_ATTEMPTS || '150')

export interface UploadProgress {
  file_id: string
  filename: string
  status: 'queued' | 'uploading' | 'processing' | 'completed' | 'failed'
  progress: number
  error?: string
  transaction_id?: string
}

/**
 * Upload a file to Supabase Storage and trigger n8n processing workflow
 */
export async function uploadFile(
  file: File,
  onProgress?: (progress: number) => void,
  onStatusChange?: (status: UploadProgress['status']) => void
): Promise<{ file_id: string; transaction_id?: string }> {
  try {
    // Step 1: Validate file
    validateFile(file)

    // Step 2: Generate unique file ID
    const fileId = crypto.randomUUID()
    const filePath = `${fileId}_${file.name}`

    if (onProgress) onProgress(10)
    if (onStatusChange) onStatusChange('uploading')

    // Step 3: Upload to Supabase Storage
    const { data: uploadData, error: uploadError } = await supabase.storage
      .from(STORAGE_BUCKET)
      .upload(filePath, file, {
        cacheControl: '3600',
        upsert: false,
      })

    if (uploadError) {
      throw new Error(`Storage upload failed: ${uploadError.message}`)
    }

    if (onProgress) onProgress(30)

    // Step 4: Get public URL
    const { data: urlData } = supabase.storage
      .from(STORAGE_BUCKET)
      .getPublicUrl(filePath)

    const storageUrl = urlData.publicUrl

    if (onProgress) onProgress(40)

    // Step 5: Create database record
    const { data: dbData, error: dbError } = await supabase
      .from('uploaded_files')
      .insert({
        file_id: fileId,
        filename: file.name,
        original_filename: file.name,
        mime_type: file.type,
        file_size_bytes: file.size,
        storage_url: storageUrl,
        status: 'queued',
        uploaded_by: 'demo-user', // TODO: Get from auth context
      })
      .select()
      .single()

    if (dbError) {
      // Clean up storage if DB insert fails
      await supabase.storage.from(STORAGE_BUCKET).remove([filePath])
      throw new Error(`Database insert failed: ${dbError.message}`)
    }

    if (onProgress) onProgress(50)
    if (onStatusChange) onStatusChange('processing')

    // Step 6: Trigger n8n webhook
    await triggerN8nWorkflow({
      file_id: fileId,
      filename: file.name,
      mime_type: file.type,
      file_size_bytes: file.size,
      storage_url: storageUrl,
      uploaded_by: 'demo-user',
      timestamp: new Date().toISOString(),
    })

    if (onProgress) onProgress(60)

    // Step 7: Poll for processing completion
    const result = await pollUploadStatus(fileId, onProgress, onStatusChange)

    if (result.status === 'failed') {
      throw new Error(result.error || 'Processing failed')
    }

    if (onProgress) onProgress(100)
    if (onStatusChange) onStatusChange('completed')

    return {
      file_id: fileId,
      transaction_id: result.transaction_id,
    }
  } catch (error: any) {
    console.error('Upload error:', error)
    if (onStatusChange) onStatusChange('failed')
    throw error
  }
}

/**
 * Validate file before upload
 */
function validateFile(file: File): void {
  const maxSize = 10 * 1024 * 1024 // 10 MB
  const allowedTypes = ['application/pdf', 'image/jpeg', 'image/png', 'text/plain']

  if (file.size > maxSize) {
    throw new Error(`File size ${(file.size / 1024 / 1024).toFixed(2)} MB exceeds 10 MB limit`)
  }

  if (!allowedTypes.includes(file.type)) {
    throw new Error(`File type ${file.type} is not supported`)
  }
}

/**
 * Trigger n8n workflow via webhook
 */
async function triggerN8nWorkflow(payload: {
  file_id: string
  filename: string
  mime_type: string
  file_size_bytes: number
  storage_url: string
  uploaded_by: string
  timestamp: string
}): Promise<void> {
  try {
    const response = await fetch(N8N_WEBHOOK_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    })

    if (!response.ok) {
      throw new Error(`n8n webhook returned status ${response.status}`)
    }

    console.log('n8n workflow triggered successfully')
  } catch (error: any) {
    console.error('Failed to trigger n8n workflow:', error)
    // Don't throw - file is uploaded, n8n can process it later
    // Or implement retry logic here
  }
}

/**
 * Poll for upload processing status
 */
async function pollUploadStatus(
  fileId: string,
  onProgress?: (progress: number) => void,
  onStatusChange?: (status: UploadProgress['status']) => void
): Promise<{
  status: 'completed' | 'failed'
  transaction_id?: string
  error?: string
}> {
  let attempts = 0

  while (attempts < MAX_POLL_ATTEMPTS) {
    attempts++

    // Wait before polling
    await new Promise((resolve) => setTimeout(resolve, POLL_INTERVAL))

    // Query status
    const { data, error } = await supabase
      .from('uploaded_files')
      .select('status, transaction_id, error_message')
      .eq('file_id', fileId)
      .single()

    if (error) {
      console.error('Poll error:', error)
      continue
    }

    // Update progress based on attempts (60% to 95%)
    if (onProgress) {
      const progressPercent = Math.min(60 + (attempts / MAX_POLL_ATTEMPTS) * 35, 95)
      onProgress(Math.round(progressPercent))
    }

    // Update status
    if (onStatusChange && data.status !== 'queued') {
      onStatusChange(data.status as UploadProgress['status'])
    }

    // Check if processing complete
    if (data.status === 'completed') {
      return {
        status: 'completed',
        transaction_id: data.transaction_id,
      }
    }

    if (data.status === 'failed') {
      return {
        status: 'failed',
        error: data.error_message || 'Processing failed',
      }
    }
  }

  // Timeout
  return {
    status: 'failed',
    error: 'Processing timeout - exceeded 5 minutes',
  }
}

/**
 * Get upload status (single query, no polling)
 */
export async function getUploadStatus(fileId: string): Promise<UploadProgress | null> {
  const { data, error } = await supabase
    .from('uploaded_files')
    .select('*')
    .eq('file_id', fileId)
    .single()

  if (error || !data) {
    return null
  }

  return {
    file_id: data.file_id,
    filename: data.filename,
    status: data.status,
    progress: data.status === 'completed' ? 100 : 0,
    error: data.error_message,
    transaction_id: data.transaction_id,
  }
}

/**
 * Subscribe to real-time status updates (alternative to polling)
 */
export function subscribeToUploadStatus(
  fileId: string,
  onUpdate: (status: UploadProgress) => void
) {
  const channel = supabase
    .channel(`upload-${fileId}`)
    .on(
      'postgres_changes',
      {
        event: 'UPDATE',
        schema: 'public',
        table: 'uploaded_files',
        filter: `file_id=eq.${fileId}`,
      },
      (payload) => {
        const newData = payload.new as any
        onUpdate({
          file_id: newData.file_id,
          filename: newData.filename,
          status: newData.status,
          progress: newData.status === 'completed' ? 100 : 0,
          error: newData.error_message,
          transaction_id: newData.transaction_id,
        })
      }
    )
    .subscribe()

  return () => {
    supabase.removeChannel(channel)
  }
}
