# Feature Specification: File Upload & Processing

**Feature Name:** Contract Document Upload
**Version:** 1.0
**Created:** 2025-11-19
**Status:** Draft
**Branch:** `claude/file-upload-feature-01Uz2dnE3UCyTqEcXrg5rQ9C`

---

## 1. Overview

### Purpose
Enable users to upload contract documents (PDF, images, text files) directly through the dashboard for automated processing through the Claude Compliance Agent.

### Goals
- **Reduce manual workflow steps** - Eliminate need to use external n8n interface for uploads
- **Improve UX** - Provide instant feedback on document processing
- **Increase adoption** - Make the tool more accessible to non-technical TCs
- **Enable batch processing** - Process multiple contracts simultaneously

### Success Metrics
- Time from upload to results < 30 seconds
- Support for 95%+ of real-world contract formats
- Zero data loss during upload/processing
- 100% of uploads logged for audit trail

---

## 2. User Stories

### Executive User
> "As an executive board member, I want to upload a contract during our meeting and immediately see the compliance results so that I can make informed decisions in real-time."

### Transaction Coordinator
> "As a TC, I want to drag-and-drop multiple contracts at once so that I can process my morning workload efficiently."

### Compliance Officer
> "As a compliance officer, I want to see a history of all uploaded documents and their processing status so that I can audit our compliance tracking system."

---

## 3. Technical Requirements

### 3.1 Supported File Formats

#### Phase 1 (MVP)
- **PDF** (.pdf) - Most common format for contracts
- **Images** (.jpg, .jpeg, .png) - Scanned contracts
- **Text** (.txt) - Plain text contracts

#### Phase 2 (Future)
- **DOCX** (.docx) - Word documents
- **Multi-page TIFF** (.tiff, .tif) - Legal document standard

### 3.2 File Constraints
- **Max file size:** 10 MB per file
- **Max batch size:** 5 files per upload
- **Max total batch size:** 25 MB
- **Allowed MIME types:**
  - `application/pdf`
  - `image/jpeg`
  - `image/png`
  - `text/plain`

### 3.3 Processing Requirements
- **OCR Integration:** Use Tesseract.js or Cloud OCR API for image/PDF text extraction
- **Queue Management:** Process files asynchronously with progress tracking
- **Storage:** Store original files in Supabase Storage for audit/reprocessing
- **Metadata:** Track upload timestamp, user, filename, processing status

---

## 4. Architecture Design

### 4.1 System Components

```
┌─────────────────┐
│   Frontend UI   │
│  (React + Vite) │
└────────┬────────┘
         │
         │ 1. Upload file via Supabase SDK
         ▼
┌─────────────────┐
│ Supabase Storage│
│  (File Storage) │
└────────┬────────┘
         │
         │ 2. Get file URL
         ▼
┌─────────────────┐
│   Frontend UI   │
│  (React + Vite) │
└────────┬────────┘
         │
         │ 3. POST to n8n webhook
         ▼
┌─────────────────┐
│  n8n Webhook    │
│  Trigger        │
└─────┬───────────┘
      │
      ▼
┌───────────────────┐
│  n8n Workflow     │
│  (Orchestration)  │
└────────┬──────────┘
         │
         ├──────────────────┐
         ▼                  ▼
┌──────────────┐    ┌──────────────────┐
│ OCR Service  │    │ Claude Compliance│
│ (if needed)  │    │      Agent       │
└──────┬───────┘    └──────┬───────────┘
       │                   │
       └─────────┬─────────┘
                 ▼
         ┌──────────────────┐
         │  Supabase DB     │
         │  (Results)       │
         └──────────────────┘
```

**n8n Webhook URL:** `https://jerbud.app.n8n.cloud/webhook/contract-upload`

**Architecture Notes:**
- No backend API server needed
- Frontend uploads directly to Supabase Storage using Supabase JavaScript SDK
- Frontend triggers n8n webhook with file metadata
- n8n handles all processing and database writes

### 4.2 Data Flow

1. **User selects file(s)** → Frontend validates format/size client-side
2. **Frontend uploads to Supabase** → Uses Supabase JS SDK `.upload()` method
3. **Supabase stores file** → Returns public URL or signed URL
4. **Frontend creates DB record** → Insert into `uploaded_files` table with status "queued"
5. **Frontend triggers n8n webhook** → POST to `https://jerbud.app.n8n.cloud/webhook/contract-upload` with:
   - `file_url`: Supabase storage URL
   - `file_id`: Database record ID (UUID)
   - `filename`: Original filename
   - `mime_type`: File MIME type
   - `uploaded_by`: User email/ID (optional)
6. **n8n processes file** → Workflow handles OCR, Claude API, compliance validation
7. **n8n writes results** → Updates `uploaded_files` status, creates `transactions` record
8. **Frontend polls Supabase** → Query `uploaded_files` table every 2 seconds for status
9. **Update UI** → Show new contract in dashboard when status = "completed"

**Key Benefits of Direct Upload:**
- ✅ No backend server needed
- ✅ Faster uploads (direct to Supabase CDN)
- ✅ Simpler architecture
- ✅ Better scalability

---

## 5. UI/UX Design

### 5.1 Upload Interface Options

#### Option A: Modal Dialog (Recommended for MVP)
```
┌───────────────────────────────────────┐
│  Upload Contract Documents        [×] │
├───────────────────────────────────────┤
│                                       │
│  ┌─────────────────────────────────┐ │
│  │                                 │ │
│  │    📄 Drag & Drop files here    │ │
│  │         or click to browse      │ │
│  │                                 │ │
│  │   Supported: PDF, JPG, PNG, TXT │ │
│  │   Max size: 10 MB per file      │ │
│  └─────────────────────────────────┘ │
│                                       │
│  Selected Files:                      │
│  ☑ contract_123.pdf (2.3 MB)     [×] │
│  ☑ addendum_456.jpg (1.1 MB)     [×] │
│                                       │
│            [Cancel]  [Upload Files]   │
└───────────────────────────────────────┘
```

#### Option B: Inline Upload Widget
- Upload button in dashboard header
- Drag-and-drop anywhere on page
- Files appear in queue sidebar

### 5.2 Processing States

**During Upload:**
```
┌─────────────────────────────────────┐
│ Uploading contract_123.pdf...       │
│ ████████████░░░░░░░░ 60%            │
└─────────────────────────────────────┘
```

**Processing:**
```
┌─────────────────────────────────────┐
│ Processing contract_123.pdf         │
│ ⚙ Extracting text...                │
│ ⚙ Running compliance checks...      │
└─────────────────────────────────────┘
```

**Success:**
```
┌─────────────────────────────────────┐
│ ✓ contract_123.pdf processed        │
│   Status: PASS | 0 issues           │
│   [View Details]                    │
└─────────────────────────────────────┘
```

**Error:**
```
┌─────────────────────────────────────┐
│ ✗ contract_123.pdf failed           │
│   Error: Unable to extract text     │
│   [Retry] [View Error Log]          │
└─────────────────────────────────────┘
```

### 5.3 Dashboard Integration

Add upload button to main dashboard header:

```tsx
<div className="flex justify-between items-center mb-6">
  <h1>Contract Compliance Dashboard</h1>
  <Button onClick={openUploadModal}>
    <Upload className="mr-2" />
    Upload Contracts
  </Button>
</div>
```

---

## 6. Frontend Integration Points

### 6.1 Supabase Storage Upload (Frontend)

**Using Supabase JavaScript SDK:**

```typescript
import { supabase } from './supabaseClient'

async function uploadFile(file: File) {
  // Validate file
  if (file.size > 10 * 1024 * 1024) {
    throw new Error('File exceeds 10 MB limit')
  }

  // Generate unique file ID
  const fileId = crypto.randomUUID()
  const filePath = `${fileId}_${file.name}`

  // Upload to Supabase Storage
  const { data, error } = await supabase.storage
    .from('contract-uploads')
    .upload(filePath, file, {
      cacheControl: '3600',
      upsert: false
    })

  if (error) throw error

  // Get public URL
  const { data: urlData } = supabase.storage
    .from('contract-uploads')
    .getPublicUrl(filePath)

  return {
    fileId,
    filename: file.name,
    storageUrl: urlData.publicUrl,
    mimeType: file.type,
    sizeBytes: file.size
  }
}
```

### 6.2 Database Record Creation (Frontend)

**Insert upload record:**

```typescript
async function createUploadRecord(fileInfo: any) {
  const { data, error } = await supabase
    .from('uploaded_files')
    .insert({
      file_id: fileInfo.fileId,
      filename: fileInfo.filename,
      original_filename: fileInfo.filename,
      mime_type: fileInfo.mimeType,
      file_size_bytes: fileInfo.sizeBytes,
      storage_url: fileInfo.storageUrl,
      status: 'queued',
      uploaded_by: 'user@example.com' // From auth context
    })
    .select()
    .single()

  if (error) throw error
  return data
}
```

### 6.3 n8n Webhook Trigger (Frontend)

**POST** `https://jerbud.app.n8n.cloud/webhook/contract-upload`

**Trigger from Frontend:**

```typescript
async function triggerN8nProcessing(fileInfo: any) {
  const response = await fetch('https://jerbud.app.n8n.cloud/webhook/contract-upload', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      file_id: fileInfo.file_id,
      filename: fileInfo.filename,
      mime_type: fileInfo.mime_type,
      file_size_bytes: fileInfo.file_size_bytes,
      storage_url: fileInfo.storage_url,
      uploaded_by: fileInfo.uploaded_by,
      timestamp: new Date().toISOString()
    })
  })

  if (!response.ok) {
    throw new Error('Failed to trigger n8n workflow')
  }

  return await response.json()
}
```

**Expected n8n Workflow Actions:**

1. Download file from `storage_url`
2. Extract text (OCR for images, pdfplumber for PDFs)
3. Call Claude Compliance Agent with extracted text
4. Parse compliance results (document_type, compliance_status, flags)
5. Update `uploaded_files` table:
   - Set status to "completed" or "failed"
   - Set `processing_completed_at` timestamp
   - Store `transaction_id` if successful
6. Insert into `transactions` table:
   - All extracted transaction data
   - Link to `source_file_id`
7. (Optional) Send notification/email if critical compliance issues found

### 6.4 Poll for Processing Status (Frontend)

**Query Supabase for status updates:**

```typescript
async function pollUploadStatus(fileId: string) {
  const { data, error } = await supabase
    .from('uploaded_files')
    .select('status, transaction_id, error_message')
    .eq('file_id', fileId)
    .single()

  if (error) throw error
  return data
}

// Poll every 2 seconds
const interval = setInterval(async () => {
  const status = await pollUploadStatus(fileId)

  if (status.status === 'completed') {
    clearInterval(interval)
    // Show success, fetch transaction details
    fetchTransactionDetails(status.transaction_id)
  } else if (status.status === 'failed') {
    clearInterval(interval)
    // Show error
    showError(status.error_message)
  }
}, 2000)
```

### 6.5 Real-time Updates with Supabase (Optional Enhancement)

**Instead of polling, use Supabase Realtime:**

```typescript
const channel = supabase
  .channel('upload-status')
  .on(
    'postgres_changes',
    {
      event: 'UPDATE',
      schema: 'public',
      table: 'uploaded_files',
      filter: `file_id=eq.${fileId}`
    },
    (payload) => {
      const status = payload.new.status
      if (status === 'completed') {
        // Show success
        fetchTransactionDetails(payload.new.transaction_id)
      } else if (status === 'failed') {
        // Show error
        showError(payload.new.error_message)
      }
    }
  )
  .subscribe()
```

---

## 7. File Processing Flow (n8n Workflow)

### 7.1 n8n Workflow Overview

**Workflow Name:** `contract-upload-processing`

**Trigger:** Webhook at `https://jerbud.app.n8n.cloud/webhook/contract-upload`

**Workflow Steps:**

1. **Webhook Trigger** - Receives upload notification from FastAPI
2. **Download File** - Fetch file from Supabase Storage using `storage_url`
3. **Extract Text** - Branch based on `mime_type`:
   - PDF → pdfplumber node
   - Images → Tesseract OCR node
   - Text → Direct read
4. **Call Claude Agent** - HTTP Request to compliance agent API or direct Python function call
5. **Parse Results** - Extract `document_type`, `compliance_status`, `transaction_data`, `compliance_flags`
6. **Update File Record** - Supabase node to update `uploaded_files` table
7. **Create Transaction** - Supabase node to insert into `transactions` table
8. **Error Handling** - Catch errors and update status to "failed"
9. **(Optional) Send Notifications** - Email/Slack if CRITICAL compliance issues

### 7.2 Text Extraction Strategy (n8n Implementation)

**For n8n workflow developers:**

```javascript
// n8n Code Node - Text Extraction
const mime_type = $input.item.json.mime_type;
const file_url = $input.item.json.storage_url;

// Download file
const response = await $http.get(file_url, { responseType: 'arraybuffer' });
const buffer = Buffer.from(response.data);

let extracted_text = '';

if (mime_type === 'application/pdf') {
  // Use n8n PDF Extract node or external PDF service
  // OR call Python script with pdfplumber
  extracted_text = await extractPdfText(buffer);

} else if (mime_type.startsWith('image/')) {
  // Use n8n OCR node or Tesseract API
  extracted_text = await performOcr(buffer);

} else if (mime_type === 'text/plain') {
  extracted_text = buffer.toString('utf-8');
}

// Validate text length
if (!extracted_text || extracted_text.length < 50) {
  throw new Error('Insufficient text extracted from document');
}

return { extracted_text };
```

### 7.3 Database Update Pattern (n8n)

**Update uploaded_files status:**

```sql
-- n8n Supabase Node - Update Query
UPDATE uploaded_files
SET
  status = 'completed',
  transaction_id = $json.transaction_id,
  processing_completed_at = NOW(),
  updated_at = NOW()
WHERE file_id = $json.file_id;
```

**Insert transaction record:**

```sql
-- n8n Supabase Node - Insert Query
INSERT INTO transactions (
  transaction_id,
  source_file_id,
  document_type,
  is_purchase_agreement,
  compliance_status,
  property_address,
  buyer_name,
  seller_name,
  purchase_price,
  -- ... other fields from transaction_data
  created_at
) VALUES (
  $json.transaction_id,
  $json.file_id,
  $json.document_type,
  $json.is_purchase_agreement,
  $json.compliance_status,
  $json.transaction_data.property_address,
  $json.transaction_data.buyer_name,
  $json.transaction_data.seller_name,
  $json.transaction_data.purchase_price,
  -- ... other values
  NOW()
);
```

---

## 8. Database Schema Updates

### 8.1 New Table: `uploaded_files`

```sql
CREATE TABLE uploaded_files (
    file_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    upload_id UUID NOT NULL,
    filename TEXT NOT NULL,
    original_filename TEXT NOT NULL,
    mime_type TEXT NOT NULL,
    file_size_bytes INTEGER NOT NULL,
    storage_url TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'queued',
    -- Status: queued, extracting_text, processing_compliance,
    --         saving_results, completed, failed
    error_message TEXT,
    transaction_id UUID REFERENCES transactions(transaction_id),
    uploaded_by TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    processing_started_at TIMESTAMPTZ,
    processing_completed_at TIMESTAMPTZ
);

CREATE INDEX idx_uploaded_files_upload_id ON uploaded_files(upload_id);
CREATE INDEX idx_uploaded_files_status ON uploaded_files(status);
CREATE INDEX idx_uploaded_files_transaction_id ON uploaded_files(transaction_id);
```

### 8.2 Update `transactions` Table

Add column to link back to uploaded file:

```sql
ALTER TABLE transactions
ADD COLUMN source_file_id UUID REFERENCES uploaded_files(file_id);

CREATE INDEX idx_transactions_source_file ON transactions(source_file_id);
```

---

## 9. Security Considerations

### 9.1 File Validation
- **MIME type verification:** Check magic bytes, not just extension
- **File size limits:** Enforce 10 MB limit server-side
- **Filename sanitization:** Remove dangerous characters, path traversal attempts
- **Virus scanning:** (Phase 2) Integrate ClamAV or cloud AV service

### 9.2 Access Control
- **Authentication required:** Only logged-in users can upload
- **File ownership:** Users can only access their own uploads (or admin sees all)
- **Signed URLs:** Use Supabase signed URLs for time-limited file access

### 9.3 Storage Security
- **Private buckets:** Files not publicly accessible
- **Encryption at rest:** Supabase provides encryption
- **Retention policy:** Auto-delete files after 90 days (configurable)

---

## 10. Error Handling

### 10.1 Error Categories

| Error Code | Description | User Action |
|------------|-------------|-------------|
| `FILE_TOO_LARGE` | File exceeds 10 MB | Compress or split file |
| `INVALID_FORMAT` | Unsupported file type | Convert to PDF/JPG/PNG |
| `TEXT_EXTRACTION_FAILED` | OCR/parsing error | Improve scan quality |
| `PROCESSING_TIMEOUT` | Claude API timeout | Retry upload |
| `STORAGE_FULL` | Storage quota exceeded | Contact admin |
| `DUPLICATE_FILE` | File already uploaded | View existing record |

### 10.2 Retry Logic

- **Automatic retries:** 3 attempts for transient errors (network, timeout)
- **Exponential backoff:** 2s, 4s, 8s between retries
- **Manual retry:** User can click "Retry" for failed uploads

---

## 11. Testing Strategy

### 11.1 Unit Tests

```python
# test_file_upload.py

def test_validate_file_size():
    """Test file size validation."""
    assert validate_file_size(5_000_000) == True
    assert validate_file_size(15_000_000) == False

def test_validate_mime_type():
    """Test MIME type validation."""
    assert validate_mime_type("application/pdf") == True
    assert validate_mime_type("application/exe") == False

def test_extract_text_from_pdf():
    """Test PDF text extraction."""
    text = extract_text_from_file("test_contract.pdf", "application/pdf")
    assert len(text) > 100
    assert "Purchase Agreement" in text
```

### 11.2 Integration Tests

```python
def test_upload_and_process_flow():
    """Test complete upload to processing flow."""
    # Upload file
    response = client.post("/api/upload", files={"file": test_pdf})
    assert response.status_code == 200

    upload_id = response.json()["upload_id"]

    # Wait for processing
    wait_for_completion(upload_id, timeout=30)

    # Check results
    status = client.get(f"/api/upload/{upload_id}/status")
    assert status.json()["files"][0]["status"] == "completed"
```

### 11.3 Test Files

Create test suite with:
- ✅ Valid PDF contract (clean)
- ✅ Low-quality scanned image (tests OCR)
- ✅ Multi-page PDF
- ✅ Plain text contract
- ❌ Oversized file (11 MB)
- ❌ Invalid format (.exe)
- ❌ Corrupted PDF
- ❌ Empty file

---

## 12. Implementation Plan

### Phase 1: MVP (Week 1)

**Supabase Setup:**
- [ ] Create `contract-uploads` storage bucket
- [ ] Set up bucket policies (public read or authenticated access)
- [ ] Create `uploaded_files` table in database
- [ ] Add source_file_id column to `transactions` table
- [ ] Enable Realtime on `uploaded_files` table (optional)

**Frontend (React):**
- [ ] Install react-dropzone and configure Supabase client
- [ ] Create upload modal component
- [ ] Implement drag-and-drop UI
- [ ] Add client-side file validation (size, type)
- [ ] Implement Supabase Storage upload function
- [ ] Create database record after successful upload
- [ ] Trigger n8n webhook with file metadata
- [ ] Poll Supabase for status updates (or use Realtime)
- [ ] Display upload progress and processing status
- [ ] Show success/error notifications
- [ ] Auto-refresh dashboard when processing completes

**n8n Workflow:**
- [ ] Create webhook trigger endpoint
- [ ] Implement file download from Supabase Storage URL
- [ ] Add PDF text extraction (pdfplumber or external service)
- [ ] Integrate Claude Compliance Agent
- [ ] Parse compliance results
- [ ] Update `uploaded_files` table with status and results
- [ ] Insert transaction records into database
- [ ] Add error handling and update status to "failed" on errors

**Testing:**
- [ ] Test file upload to Supabase Storage
- [ ] Test n8n webhook trigger
- [ ] Integration test: upload → process → database
- [ ] Manual testing with sample PDF contracts

### Phase 2: Enhancements (Week 2)

**Frontend:**
- [ ] Implement batch upload (5 files at once)
- [ ] Add file upload history page
- [ ] Implement retry button for failed uploads
- [ ] Show detailed processing logs/errors
- [ ] Add download button for original files
- [ ] Implement duplicate file detection

**n8n Workflow:**
- [ ] Add image OCR support (Tesseract or cloud OCR)
- [ ] Implement retry mechanism for failed extractions
- [ ] Add email notifications for CRITICAL compliance issues
- [ ] Add Slack webhook for team notifications
- [ ] Add processing time metrics

**Supabase:**
- [ ] Replace polling with Realtime subscriptions
- [ ] Add file retention policy (auto-delete after 90 days)

### Phase 3: Advanced Features (Future)

**Frontend:**
- [ ] Mobile-optimized upload UI
- [ ] Batch operations (delete multiple, re-process)
- [ ] Upload analytics dashboard
- [ ] Drag-and-drop anywhere on page

**n8n Workflow:**
- [ ] DOCX support
- [ ] Multi-page TIFF support
- [ ] Virus scanning integration
- [ ] File compression before storage

**Supabase:**
- [ ] CDN optimization for faster downloads
- [ ] Automatic image thumbnail generation

---

## 13. Dependencies

### Frontend Packages (React)
```bash
npm install react-dropzone        # Drag-and-drop file upload UI
npm install @supabase/supabase-js # Supabase client (already installed)
# Note: lucide-react already installed for icons
```

### n8n Workflow Dependencies
- **n8n nodes:** Webhook, HTTP Request, Supabase, Code
- **External services (optional):**
  - Cloud OCR API (Google Vision, AWS Textract) OR
  - Self-hosted Tesseract container
  - PDF extraction service OR pdfplumber Python script

### Supabase Configuration
- Storage bucket: `contract-uploads`
- Tables: `uploaded_files`, `transactions`
- Realtime enabled on `uploaded_files` (optional for Phase 2)

---

## 14. Configuration

### Frontend Environment Variables (.env)

```bash
# Supabase Configuration (already configured)
VITE_SUPABASE_URL=https://zdbakftwcpfnpmwrrydy.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key-here

# File Upload Configuration
VITE_MAX_FILE_SIZE_MB=10
VITE_MAX_BATCH_FILES=5
VITE_ALLOWED_MIME_TYPES=application/pdf,image/jpeg,image/png,text/plain

# n8n Webhook Integration
VITE_N8N_WEBHOOK_URL=https://jerbud.app.n8n.cloud/webhook/contract-upload

# Storage
VITE_SUPABASE_STORAGE_BUCKET=contract-uploads

# Polling Configuration
VITE_STATUS_POLL_INTERVAL_MS=2000
VITE_MAX_POLL_ATTEMPTS=150  # 5 minutes max (150 * 2s)
```

### Supabase Storage Bucket Configuration

**Bucket Settings:**
- Name: `contract-uploads`
- Public: `false` (files accessible via signed URLs)
- File size limit: 10 MB
- Allowed MIME types: PDF, JPEG, PNG, TXT

**Bucket Policies:**
```sql
-- Allow authenticated users to upload
CREATE POLICY "Allow authenticated uploads"
ON storage.objects FOR INSERT
TO authenticated
WITH CHECK (bucket_id = 'contract-uploads');

-- Allow authenticated users to read their own files
CREATE POLICY "Allow authenticated reads"
ON storage.objects FOR SELECT
TO authenticated
USING (bucket_id = 'contract-uploads');
```

---

## 15. Monitoring & Observability

### Metrics to Track
- **Upload volume:** Files uploaded per day/hour
- **Processing time:** Avg/p95/p99 time from upload to completion
- **Success rate:** % of uploads successfully processed
- **Error rate:** % by error type
- **Storage usage:** Total bytes stored, growth rate

### Logging
```python
logger.info("File uploaded",
           file_id=file_id,
           filename=filename,
           size_bytes=size,
           mime_type=mime_type)

logger.info("Processing complete",
           file_id=file_id,
           processing_time_ms=elapsed,
           transaction_id=txn_id)

logger.error("Processing failed",
            file_id=file_id,
            error_type=error.__class__.__name__,
            error_message=str(error))
```

---

## 16. Open Questions

1. **Authentication:** How do we identify users? Add auth system or rely on IP/session?
2. **File retention:** Should we keep original files forever or auto-delete after X days?
3. **Duplicate handling:** If same file uploaded twice, reprocess or return cached results?
4. **Priority queue:** Should executive users get faster processing?
5. **Cost management:** How to handle high Claude API costs from many uploads?

---

## 17. Success Criteria

### MVP Launch Criteria
- ✅ Upload 5 PDFs in < 2 minutes total processing time
- ✅ 95%+ accuracy on text extraction (manual spot-check)
- ✅ Zero data loss (all uploads tracked in DB)
- ✅ Error messages clear and actionable
- ✅ Mobile browser upload works

### Post-Launch Goals
- **Month 1:** 100+ contracts uploaded
- **Month 3:** < 5% error rate
- **Month 6:** Support for 3+ file formats

---

## 18. References

- [Supabase Storage Documentation](https://supabase.com/docs/guides/storage)
- [FastAPI File Uploads](https://fastapi.tiangolo.com/tutorial/request-files/)
- [pdfplumber Documentation](https://github.com/jsvine/pdfplumber)
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract)
- [React Dropzone](https://react-dropzone.js.org/)

---

**Document Version History:**
- v1.0 (2025-11-19): Initial draft
