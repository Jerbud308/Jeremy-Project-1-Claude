# Supabase Setup for File Upload Feature

This guide walks you through setting up the Supabase database and storage for the file upload feature.

## Prerequisites

- Access to your Supabase project: https://zdbakftwcpfnpmwrrydy.supabase.co
- SQL Editor access
- Storage permissions

---

## Step 1: Run Database Schema

1. Open Supabase Dashboard
2. Go to **SQL Editor**
3. Create a new query
4. Copy and paste the contents of `uploaded_files_schema.sql`
5. Click **Run** to execute

This will create:
- `uploaded_files` table with indexes
- `source_file_id` column in `transactions` table
- Auto-update triggers
- Row Level Security policies

---

## Step 2: Create Storage Bucket

### Option A: Via Dashboard (Recommended)

1. Go to **Storage** in Supabase Dashboard
2. Click **Create a new bucket**
3. Configure bucket:
   - **Name:** `contract-uploads`
   - **Public:** ❌ Unchecked (use signed URLs for security)
   - **File size limit:** 10 MB
   - **Allowed MIME types:**
     - `application/pdf`
     - `image/jpeg`
     - `image/png`
     - `text/plain`
4. Click **Create bucket**

### Option B: Via SQL (If storage policies already exist)

```sql
-- This is handled by the SQL schema file
-- Storage policies are created automatically
```

---

## Step 3: Verify Setup

Run these verification queries in SQL Editor:

### Check uploaded_files table
```sql
SELECT table_name, column_name, data_type
FROM information_schema.columns
WHERE table_name = 'uploaded_files'
ORDER BY ordinal_position;
```

Expected: 15 columns including file_id, filename, status, etc.

### Check transactions table update
```sql
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'transactions'
  AND column_name = 'source_file_id';
```

Expected: 1 row showing source_file_id column

### Check storage bucket
```sql
SELECT id, name, public
FROM storage.buckets
WHERE name = 'contract-uploads';
```

Expected: 1 row with public = false

---

## Step 4: Test Upload (Manual)

### Test via Supabase Dashboard

1. Go to **Storage** → `contract-uploads` bucket
2. Click **Upload file**
3. Upload a small PDF (< 10 MB)
4. Verify file appears in bucket

### Test via SQL

Insert a test record:

```sql
INSERT INTO uploaded_files (
    filename,
    original_filename,
    mime_type,
    file_size_bytes,
    storage_url,
    status,
    uploaded_by
) VALUES (
    'test-contract.pdf',
    'test-contract.pdf',
    'application/pdf',
    500000,
    'https://zdbakftwcpfnpmwrrydy.supabase.co/storage/v1/object/public/contract-uploads/test.pdf',
    'queued',
    'test@example.com'
);

-- Verify
SELECT * FROM uploaded_files WHERE filename = 'test-contract.pdf';

-- Clean up
DELETE FROM uploaded_files WHERE filename = 'test-contract.pdf';
```

---

## Step 5: Enable Realtime (Optional - Phase 2)

For real-time status updates instead of polling:

1. Go to **Database** → **Replication**
2. Find `uploaded_files` table
3. Toggle **Enable Realtime** to ON
4. Click **Save**

This allows the frontend to subscribe to status changes via Supabase Realtime.

---

## Security Considerations

### Current Setup (Development)

The current RLS policies allow public access for development:
- Anyone can insert (upload)
- Anyone can select (view)
- Anyone can update (status changes from n8n)

### Production Setup (TODO)

Before going to production, update the policies:

```sql
-- Remove public policies
DROP POLICY "Allow public inserts for now" ON uploaded_files;
DROP POLICY "Allow public selects for now" ON uploaded_files;
DROP POLICY "Allow public updates for now" ON uploaded_files;

-- Add authenticated-only policies
CREATE POLICY "Allow authenticated uploads" ON uploaded_files
    FOR INSERT
    TO authenticated
    WITH CHECK (uploaded_by = auth.uid()::text);

CREATE POLICY "Users can view own uploads" ON uploaded_files
    FOR SELECT
    TO authenticated
    USING (uploaded_by = auth.uid()::text);

-- Allow service role (n8n) to update
CREATE POLICY "Service role can update" ON uploaded_files
    FOR UPDATE
    TO service_role
    USING (true);
```

---

## Troubleshooting

### Error: "relation 'uploaded_files' does not exist"
- Run the SQL schema file again
- Check for errors in SQL execution

### Error: "bucket 'contract-uploads' does not exist"
- Create the bucket manually via Dashboard
- Verify bucket name is exactly `contract-uploads`

### Error: "new row violates row-level security policy"
- Check RLS policies are created
- Temporarily disable RLS for testing:
  ```sql
  ALTER TABLE uploaded_files DISABLE ROW LEVEL SECURITY;
  ```

### Files not appearing after upload
- Check storage bucket permissions
- Verify storage URL is correct
- Check browser console for CORS errors

---

## Next Steps

Once setup is complete:

1. ✅ Database schema created
2. ✅ Storage bucket configured
3. ✅ Test upload successful
4. ➡️ Implement frontend upload component
5. ➡️ Create n8n workflow
6. ➡️ Test end-to-end flow

---

## Monitoring Queries

### View recent uploads
```sql
SELECT
    file_id,
    filename,
    status,
    file_size_bytes / 1024 / 1024 as size_mb,
    created_at,
    processing_completed_at - processing_started_at as processing_time
FROM uploaded_files
ORDER BY created_at DESC
LIMIT 10;
```

### View upload statistics
```sql
SELECT
    status,
    COUNT(*) as count,
    AVG(file_size_bytes) / 1024 / 1024 as avg_size_mb
FROM uploaded_files
GROUP BY status
ORDER BY count DESC;
```

### View failed uploads with errors
```sql
SELECT
    file_id,
    filename,
    error_message,
    created_at
FROM uploaded_files
WHERE status = 'failed'
ORDER BY created_at DESC;
```
