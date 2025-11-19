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
         │ HTTP POST /api/upload
         ▼
┌─────────────────┐
│  FastAPI Server │
│  Upload Handler │
└────────┬────────┘
         │
         ├──────────────────┐
         │                  │
         ▼                  ▼
┌─────────────────┐  ┌──────────────┐
│ Supabase Storage│  │ Processing   │
│  (File Storage) │  │    Queue     │
└─────────────────┘  └──────┬───────┘
                            │
                            ▼
                     ┌──────────────┐
                     │  OCR Service │
                     │ (if needed)  │
                     └──────┬───────┘
                            │
                            ▼
                     ┌──────────────────┐
                     │ Claude Compliance│
                     │      Agent       │
                     └──────┬───────────┘
                            │
                            ▼
                     ┌──────────────────┐
                     │  Supabase DB     │
                     │  (Results)       │
                     └──────────────────┘
```

### 4.2 Data Flow

1. **User uploads file(s)** → Frontend validates format/size
2. **Frontend sends file(s)** → FastAPI receives via multipart/form-data
3. **FastAPI validates** → Check MIME type, size, malware scan (future)
4. **Store original file** → Supabase Storage bucket
5. **Extract text** → OCR for images/PDFs, direct read for .txt
6. **Process with Claude** → Call compliance agent
7. **Save to database** → Insert transaction record with file reference
8. **Return results** → WebSocket or polling for real-time updates
9. **Update UI** → Show new contract in dashboard table

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

## 6. Backend API Endpoints

### 6.1 Upload Endpoint

**POST** `/api/upload`

**Request:**
```
Content-Type: multipart/form-data

files: File[] (1-5 files)
user_id: string (optional, from auth)
```

**Response:**
```json
{
  "success": true,
  "upload_id": "upl_xyz123",
  "files": [
    {
      "filename": "contract_123.pdf",
      "file_id": "file_abc456",
      "status": "queued",
      "storage_url": "https://supabase.co/storage/..."
    }
  ]
}
```

**Error Response:**
```json
{
  "success": false,
  "error": "FILE_TOO_LARGE",
  "message": "File contract_123.pdf exceeds 10 MB limit",
  "max_size_mb": 10
}
```

### 6.2 Processing Status Endpoint

**GET** `/api/upload/{upload_id}/status`

**Response:**
```json
{
  "upload_id": "upl_xyz123",
  "status": "processing",
  "files": [
    {
      "file_id": "file_abc456",
      "filename": "contract_123.pdf",
      "status": "completed",
      "transaction_id": "txn_789",
      "compliance_status": "PASS",
      "processing_time_ms": 2340
    }
  ]
}
```

### 6.3 File Download Endpoint

**GET** `/api/files/{file_id}/download`

**Response:**
- Returns original file with appropriate Content-Type header
- Requires authentication
- Includes Content-Disposition header for download

---

## 7. File Processing Flow

### 7.1 Text Extraction Strategy

```python
def extract_text_from_file(file_path: str, mime_type: str) -> str:
    """Extract text from uploaded file based on type."""

    if mime_type == "text/plain":
        # Direct read
        with open(file_path, 'r') as f:
            return f.read()

    elif mime_type == "application/pdf":
        # Use PyPDF2 or pdfplumber
        import pdfplumber
        with pdfplumber.open(file_path) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text() or ""
            return text

    elif mime_type in ["image/jpeg", "image/png"]:
        # Use Tesseract OCR
        import pytesseract
        from PIL import Image
        img = Image.open(file_path)
        return pytesseract.image_to_string(img)

    else:
        raise ValueError(f"Unsupported file type: {mime_type}")
```

### 7.2 Processing Pipeline

```python
async def process_uploaded_file(file_id: str):
    """Process uploaded file through compliance pipeline."""

    # 1. Get file from storage
    file_record = get_file_record(file_id)
    file_path = download_from_storage(file_record.storage_url)

    # 2. Extract text
    update_status(file_id, "extracting_text")
    text = extract_text_from_file(file_path, file_record.mime_type)

    if not text or len(text) < 50:
        raise ValueError("Insufficient text extracted from document")

    # 3. Process with Claude
    update_status(file_id, "processing_compliance")
    from claude_compliance_agent import process_contract_text
    result = process_contract_text(text)

    # 4. Save to database
    update_status(file_id, "saving_results")
    transaction_id = save_transaction(result, file_id)

    # 5. Mark complete
    update_status(file_id, "completed", transaction_id=transaction_id)

    return transaction_id
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

**Backend:**
- [ ] Create `/api/upload` endpoint
- [ ] Implement file validation
- [ ] Set up Supabase Storage bucket
- [ ] Create `uploaded_files` table
- [ ] Implement PDF text extraction (pdfplumber)
- [ ] Integrate with existing Claude agent
- [ ] Create processing status endpoint

**Frontend:**
- [ ] Create upload modal component
- [ ] Implement drag-and-drop UI
- [ ] Add file preview/validation
- [ ] Show upload progress
- [ ] Display processing status
- [ ] Update dashboard to show newly processed contracts

**Testing:**
- [ ] Unit tests for file validation
- [ ] Integration tests for upload flow
- [ ] Manual testing with real contracts

### Phase 2: Enhancements (Week 2)

- [ ] Add OCR for images (Tesseract)
- [ ] Implement batch upload (multiple files)
- [ ] Add file history view
- [ ] Create download endpoint for original files
- [ ] Add duplicate detection
- [ ] Implement retry mechanism
- [ ] Add WebSocket for real-time updates

### Phase 3: Advanced Features (Future)

- [ ] DOCX support
- [ ] Virus scanning integration
- [ ] File compression before storage
- [ ] Bulk export functionality
- [ ] Email notification on completion
- [ ] Mobile-optimized upload UI

---

## 13. Dependencies

### Python Packages
```bash
pip install pdfplumber  # PDF text extraction
pip install pytesseract  # OCR for images
pip install python-multipart  # FastAPI file uploads
pip install pillow  # Image processing
pip install python-magic  # MIME type detection
```

### System Dependencies
```bash
# For Tesseract OCR
apt-get install tesseract-ocr
apt-get install libtesseract-dev
```

### Frontend Packages
```bash
npm install react-dropzone  # Drag-and-drop UI
npm install axios  # File upload with progress
```

---

## 14. Configuration

### Environment Variables

```bash
# File Upload Configuration
MAX_FILE_SIZE_MB=10
MAX_BATCH_FILES=5
MAX_BATCH_SIZE_MB=25
ALLOWED_MIME_TYPES=application/pdf,image/jpeg,image/png,text/plain

# Supabase Storage
SUPABASE_STORAGE_BUCKET=contract-uploads
FILE_RETENTION_DAYS=90

# Processing
UPLOAD_PROCESSING_TIMEOUT=60
MAX_RETRY_ATTEMPTS=3
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
