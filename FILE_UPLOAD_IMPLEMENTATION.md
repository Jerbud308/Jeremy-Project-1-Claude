# File Upload Feature - Implementation Guide

This document provides step-by-step instructions to get the file upload feature running.

## ✅ What's Been Implemented

### Backend/Database
- ✅ `uploaded_files` table schema
- ✅ Storage bucket configuration
- ✅ Row Level Security policies
- ✅ Database indexes and triggers

### Frontend
- ✅ Upload modal component with drag-and-drop
- ✅ File upload service with Supabase integration
- ✅ n8n webhook triggering
- ✅ Status polling
- ✅ Progress tracking
- ✅ Error handling

### Integration
- ✅ Upload button in dashboard header
- ✅ Auto-refresh dashboard after upload
- ✅ Real-time status updates (polling)

---

## 🚀 Installation Steps

### Step 1: Install Dependencies

```bash
cd dashboard/frontend
npm install react-dropzone
```

### Step 2: Set Up Supabase Database

1. Log in to Supabase Dashboard: https://zdbakftwcpfnpmwrrydy.supabase.co
2. Go to **SQL Editor**
3. Run the schema file: `database/uploaded_files_schema.sql`
4. Verify tables created:
   ```sql
   SELECT * FROM uploaded_files LIMIT 1;
   SELECT column_name FROM information_schema.columns WHERE table_name = 'transactions' AND column_name = 'source_file_id';
   ```

### Step 3: Create Storage Bucket

1. Go to **Storage** in Supabase Dashboard
2. Click **Create a new bucket**
3. Configure:
   - Name: `contract-uploads`
   - Public: **Unchecked** (private bucket)
   - File size limit: 10 MB
   - Allowed MIME types: `application/pdf`, `image/jpeg`, `image/png`, `text/plain`
4. Click **Create bucket**

See `database/SUPABASE_SETUP.md` for detailed instructions.

### Step 4: Configure Environment Variables

1. Copy `.env.example` to `.env`:
   ```bash
   cp dashboard/frontend/.env.example dashboard/frontend/.env
   ```

2. Update `.env` with your values:
   ```bash
   VITE_SUPABASE_URL=https://zdbakftwcpfnpmwrrydy.supabase.co
   VITE_SUPABASE_ANON_KEY=<your-actual-anon-key>
   VITE_N8N_WEBHOOK_URL=https://jerbud.app.n8n.cloud/webhook/contract-upload
   ```

### Step 5: Start the Dashboard

```bash
cd dashboard/frontend
npm run dev
```

The dashboard will be available at http://localhost:3000

---

## 🧪 Testing the Upload Feature

### Manual Test (Without n8n Workflow)

1. Open dashboard at http://localhost:3000
2. Click **Upload Contracts** button in header
3. Drag and drop a PDF file or click to browse
4. Click **Upload 1 File**
5. Watch the progress:
   - File uploads to Supabase Storage
   - Record created in `uploaded_files` table
   - n8n webhook triggered
   - Status shows "Processing..."

6. Check Supabase:
   ```sql
   SELECT * FROM uploaded_files ORDER BY created_at DESC LIMIT 1;
   ```

### Expected Behavior

**Without n8n workflow:**
- Upload completes successfully
- File stored in Supabase Storage
- Database record created with status = "queued"
- n8n webhook called (may fail if workflow doesn't exist yet)
- Frontend polls status (will timeout after 5 minutes)

**With n8n workflow:**
- All of the above, plus:
- n8n downloads and processes file
- Status updates to "processing" → "completed"
- Transaction record created
- Dashboard automatically refreshes
- New contract appears in table

---

## 📋 n8n Workflow Setup (Required for Full Functionality)

The upload feature triggers your n8n webhook. You need to create the workflow:

### Workflow Overview

**Webhook URL:** `https://jerbud.app.n8n.cloud/webhook/contract-upload`

**Expected Payload:**
```json
{
  "file_id": "uuid",
  "filename": "contract.pdf",
  "mime_type": "application/pdf",
  "file_size_bytes": 1234567,
  "storage_url": "https://...",
  "uploaded_by": "user@example.com",
  "timestamp": "2025-11-23T10:30:00Z"
}
```

### Workflow Steps

1. **Webhook Trigger** - Receive upload notification
2. **HTTP Request** - Download file from `storage_url`
3. **Switch** - Branch based on `mime_type`
   - PDF → PDF text extraction
   - Image → OCR
   - Text → Direct read
4. **Python/Claude Agent** - Process with compliance agent
5. **Supabase Update** - Update `uploaded_files` status
6. **Supabase Insert** - Create `transactions` record
7. **Error Handler** - Update status to "failed" on errors

See `FEATURE_SPEC_FILE_UPLOAD.md` Section 7 for detailed workflow implementation.

---

## 🔍 Troubleshooting

### Issue: "Failed to upload file"

**Check:**
- Supabase credentials in `.env` are correct
- Storage bucket `contract-uploads` exists
- File size is under 10 MB
- File type is PDF, JPG, PNG, or TXT

**Debug:**
```javascript
// In browser console
console.log(import.meta.env.VITE_SUPABASE_URL)
console.log(import.meta.env.VITE_SUPABASE_STORAGE_BUCKET)
```

### Issue: "Processing timeout"

**This is expected** if n8n workflow isn't set up yet.

**Check:**
```sql
SELECT file_id, filename, status, error_message
FROM uploaded_files
WHERE status = 'queued'
ORDER BY created_at DESC;
```

**Solution:**
- Set up n8n workflow (see above)
- Or manually update status for testing:
  ```sql
  UPDATE uploaded_files
  SET status = 'completed', transaction_id = gen_random_uuid()
  WHERE file_id = '<your-file-id>';
  ```

### Issue: "n8n webhook failed"

**Check:**
- n8n webhook URL is correct in `.env`
- Webhook endpoint exists in n8n
- n8n workflow is active

**Test webhook manually:**
```bash
curl -X POST https://jerbud.app.n8n.cloud/webhook/contract-upload \
  -H "Content-Type: application/json" \
  -d '{
    "file_id": "test-123",
    "filename": "test.pdf",
    "storage_url": "https://example.com/test.pdf"
  }'
```

### Issue: "CORS error" in browser

**Check:**
- Supabase Storage policies allow public reads
- Storage bucket is configured correctly

**Fix:**
Run in Supabase SQL Editor:
```sql
CREATE POLICY "Allow public reads with signed URLs" ON storage.objects
FOR SELECT TO public
USING (bucket_id = 'contract-uploads');
```

---

## 📊 Monitoring Uploads

### View Recent Uploads
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

### View Upload Statistics
```sql
SELECT
  status,
  COUNT(*) as count,
  AVG(file_size_bytes) / 1024 / 1024 as avg_size_mb
FROM uploaded_files
GROUP BY status
ORDER BY count DESC;
```

### View Failed Uploads
```sql
SELECT file_id, filename, error_message, created_at
FROM uploaded_files
WHERE status = 'failed'
ORDER BY created_at DESC;
```

---

## 🎯 Next Steps

### Phase 2 Enhancements

1. **Realtime Updates** - Replace polling with Supabase Realtime
   ```typescript
   // Enable in Supabase Dashboard → Database → Replication
   // Toggle "uploaded_files" table
   ```

2. **Batch Upload** - Upload multiple files at once
   - Already supported in modal (up to 5 files)
   - Each file processed independently

3. **Upload History** - View all past uploads
   - Create new page: `/uploads`
   - List all uploads with status, date, etc.

4. **File Download** - Download original files
   - Add download button to contract details
   - Use Supabase signed URLs

5. **Retry Failed Uploads** - Re-trigger processing
   - Add retry button for failed uploads
   - Call n8n webhook again

---

## 📁 Files Created/Modified

### New Files
- `database/uploaded_files_schema.sql` - Database schema
- `database/SUPABASE_SETUP.md` - Setup instructions
- `dashboard/frontend/src/components/UploadModal.tsx` - Upload UI
- `dashboard/frontend/src/services/fileUploadService.ts` - Upload logic
- `dashboard/frontend/.env.example` - Environment template

### Modified Files
- `dashboard/frontend/src/App.tsx` - Added upload button and modal

---

## 🔗 Related Documentation

- [Feature Specification](./FEATURE_SPEC_FILE_UPLOAD.md) - Complete feature design
- [Supabase Setup Guide](./database/SUPABASE_SETUP.md) - Database setup details
- [n8n Webhook Integration](./FEATURE_SPEC_FILE_UPLOAD.md#7-file-processing-flow-n8n-workflow) - Workflow details

---

## ✨ Feature Complete!

The file upload feature is fully implemented and ready to use. Once you set up the n8n workflow, you'll have end-to-end automated contract processing from upload to compliance results.

**Questions?** Check the troubleshooting section above or review the feature spec.
