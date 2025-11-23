-- ============================================================================
-- File Upload Feature - Database Schema
-- ============================================================================
-- This schema supports the file upload feature where users can upload
-- contract documents that are processed through the n8n workflow.
--
-- Created: 2025-11-23
-- ============================================================================

-- Create uploaded_files table
CREATE TABLE IF NOT EXISTS uploaded_files (
    file_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    upload_id UUID DEFAULT uuid_generate_v4(),
    filename TEXT NOT NULL,
    original_filename TEXT NOT NULL,
    mime_type TEXT NOT NULL,
    file_size_bytes INTEGER NOT NULL,
    storage_url TEXT NOT NULL,

    -- Status tracking
    status TEXT NOT NULL DEFAULT 'queued',
    -- Status values: 'queued', 'extracting_text', 'processing_compliance',
    --                'saving_results', 'completed', 'failed'

    error_message TEXT,

    -- Link to transaction once processed
    transaction_id UUID REFERENCES transactions(transaction_id),

    -- User tracking
    uploaded_by TEXT,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    processing_started_at TIMESTAMPTZ,
    processing_completed_at TIMESTAMPTZ,

    -- Constraints
    CONSTRAINT valid_status CHECK (status IN (
        'queued',
        'extracting_text',
        'processing_compliance',
        'saving_results',
        'completed',
        'failed'
    )),
    CONSTRAINT valid_file_size CHECK (file_size_bytes > 0 AND file_size_bytes <= 10485760), -- 10 MB max
    CONSTRAINT valid_mime_type CHECK (mime_type IN (
        'application/pdf',
        'image/jpeg',
        'image/png',
        'text/plain'
    ))
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_uploaded_files_upload_id ON uploaded_files(upload_id);
CREATE INDEX IF NOT EXISTS idx_uploaded_files_status ON uploaded_files(status);
CREATE INDEX IF NOT EXISTS idx_uploaded_files_transaction_id ON uploaded_files(transaction_id);
CREATE INDEX IF NOT EXISTS idx_uploaded_files_created_at ON uploaded_files(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_uploaded_files_uploaded_by ON uploaded_files(uploaded_by);

-- Add source_file_id column to transactions table to link back to uploaded file
ALTER TABLE transactions
ADD COLUMN IF NOT EXISTS source_file_id UUID REFERENCES uploaded_files(file_id);

CREATE INDEX IF NOT EXISTS idx_transactions_source_file ON transactions(source_file_id);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_uploaded_files_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to auto-update updated_at timestamp
DROP TRIGGER IF EXISTS trigger_update_uploaded_files_updated_at ON uploaded_files;
CREATE TRIGGER trigger_update_uploaded_files_updated_at
    BEFORE UPDATE ON uploaded_files
    FOR EACH ROW
    EXECUTE FUNCTION update_uploaded_files_updated_at();

-- ============================================================================
-- Row Level Security (RLS) Policies
-- ============================================================================
-- Note: Adjust these policies based on your authentication requirements

-- Enable RLS on uploaded_files
ALTER TABLE uploaded_files ENABLE ROW LEVEL SECURITY;

-- Policy: Allow all users to insert (upload files)
-- TODO: Restrict to authenticated users once auth is implemented
CREATE POLICY "Allow public inserts for now" ON uploaded_files
    FOR INSERT
    WITH CHECK (true);

-- Policy: Allow all users to select (view uploads)
-- TODO: Restrict to own uploads once auth is implemented
CREATE POLICY "Allow public selects for now" ON uploaded_files
    FOR SELECT
    USING (true);

-- Policy: Allow n8n workflow to update status
-- TODO: Create service role for n8n and restrict updates to that role
CREATE POLICY "Allow public updates for now" ON uploaded_files
    FOR UPDATE
    USING (true);

-- ============================================================================
-- Storage Bucket Setup
-- ============================================================================
-- The following needs to be run in Supabase Storage (not SQL editor)
--
-- 1. Create bucket 'contract-uploads' via Supabase Dashboard:
--    - Go to Storage → Create bucket
--    - Name: contract-uploads
--    - Public: false (use signed URLs)
--    - File size limit: 10 MB
--    - Allowed MIME types: application/pdf, image/jpeg, image/png, text/plain
--
-- 2. Set bucket policies (run these in SQL editor):

-- Allow authenticated users to upload files
CREATE POLICY "Allow authenticated uploads" ON storage.objects
    FOR INSERT
    TO authenticated
    WITH CHECK (bucket_id = 'contract-uploads');

-- Allow authenticated users to read files
CREATE POLICY "Allow authenticated reads" ON storage.objects
    FOR SELECT
    TO authenticated
    USING (bucket_id = 'contract-uploads');

-- Allow public reads for signed URLs (if needed)
CREATE POLICY "Allow public reads with signed URLs" ON storage.objects
    FOR SELECT
    TO public
    USING (bucket_id = 'contract-uploads');

-- ============================================================================
-- Helpful Queries
-- ============================================================================

-- View all uploads with their status
-- SELECT file_id, filename, status, created_at, processing_completed_at
-- FROM uploaded_files
-- ORDER BY created_at DESC;

-- View uploads with processing time
-- SELECT
--     file_id,
--     filename,
--     status,
--     EXTRACT(EPOCH FROM (processing_completed_at - processing_started_at)) as processing_seconds
-- FROM uploaded_files
-- WHERE status = 'completed'
-- ORDER BY processing_seconds DESC;

-- View failed uploads
-- SELECT file_id, filename, error_message, created_at
-- FROM uploaded_files
-- WHERE status = 'failed'
-- ORDER BY created_at DESC;

-- View uploads linked to transactions
-- SELECT
--     uf.file_id,
--     uf.filename,
--     uf.status,
--     t.transaction_id,
--     t.property_address,
--     t.compliance_status
-- FROM uploaded_files uf
-- LEFT JOIN transactions t ON uf.transaction_id = t.transaction_id
-- ORDER BY uf.created_at DESC;
