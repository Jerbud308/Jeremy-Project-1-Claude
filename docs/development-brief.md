# B-MAD Greenfield Development Brief: Claude Contract Compliance Agent

**Project Name**: TC AI Agent System - Agent 1: Contract Compliance Bot (Claude Core)
**Methodology**: B-MAD Greenfield (PRD-First)
**Target Agent**: Claude 3 Opus (or equivalent Anthropic model)
**Target Environment**: Python 3.11+ (Executed via n8n Code Node or dedicated microservice)
**Author**: Manus AI
**Date**: November 17, 2025

---

## 1. Breakthrough (B): Project Overview and Goal

### 1.1. Goal

To develop a highly accurate, robust, and scalable Claude-based Python microservice responsible for the core AI logic of the Contract Compliance Bot (Agent 1). This service must reliably extract structured data and perform compliance validation from raw real estate purchase agreement text.

### 1.2. Scope (Greenfield Focus)

This brief focuses exclusively on the core AI logic, which will be integrated into the existing n8n orchestration layer.

#### In Scope
- Structured Data Extraction (FR-3)
- Compliance Validation Logic (FR-4)
- Confidence Scoring & Flagging
- Code for Claude API Integration
- Unit Testing for Core Logic

#### Out of Scope (Handled by n8n/Supabase)
- Document Intake (Webhooks, Email)
- OCR/Text Extraction (Google Document AI)
- Database Population (Supabase Insert)
- Notification System (SendGrid/Twilio)
- Human-in-the-Loop UI

### 1.3. Context and Justification

The original system design specified GPT-4. This project pivots to Claude to leverage its superior long-context reasoning capabilities for processing lengthy real estate contracts (10-25 pages), ensuring higher accuracy and alignment with the client's strategic focus on Claude-based development.

---

## 2. Method (M): System Architecture and Integration

The Claude Agent will function as a critical component within the overall system architecture, receiving input from the OCR stage and delivering output to the database and notification stages.

### 2.1. Component Role

The Claude Agent is a **Stateless Processing Service**. It receives a single input (raw contract text) and returns a single, structured output (validated transaction data and compliance flags).

### 2.2. Integration Points

The agent will be invoked via a standard REST API call or a dedicated Python script executed within an n8n Code Node.

| Integration Point | Data Flow | Format |
|------------------|-----------|--------|
| Input (From n8n) | Raw Text from OCR (FR-2) | String (Full contract text) |
| Output (To n8n) | Validated Transaction Data (FR-5) | JSON Object |
| Dependency | Claude API Key (Environment Variable) | String |

---

## 3. Agent (A): Detailed Agent Specification

The Claude Agent will perform a two-step process: **Extraction** and **Validation**.

### 3.1. Step 1: Structured Data Extraction (FR-3)

The agent must use Claude's tools or response_schema feature to guarantee the output conforms to the required JSON structure.

#### 3.1.1. Input Prompt Template

The prompt must instruct Claude to act as a "Senior Real Estate Transaction Coordinator Data Analyst" and use the provided schema to extract all required fields from the contract text. It must also be instructed to return null or an empty string for any field that cannot be found, rather than hallucinating data.

#### 3.1.2. Required Output Schema (JSON)

The agent must return a single JSON object conforming to the following structure:

```json
{
  "property_address": "string (full address with city, state, zip)",
  "buyer_name": "string (comma-separated if multiple)",
  "seller_name": "string (comma-separated if multiple)",
  "purchase_price": "number (raw value, no formatting)",
  "earnest_money_amount": "number",
  "closing_date": "date (YYYY-MM-DD)",
  "inspection_deadline": "date (YYYY-MM-DD)",
  "financing_contingency_date": "date (YYYY-MM-DD)",
  "appraisal_contingency_date": "date (YYYY-MM-DD)",
  "title_contingency_date": "date (YYYY-MM-DD)",
  "listing_agent_name": "string",
  "buyer_agent_name": "string",
  "escrow_company": "string",
  "title_company": "string",
  "extraction_confidence_score": "number (0.0 to 1.0, overall confidence in extraction)"
}
```

### 3.2. Step 2: Compliance Validation and Flagging (FR-4)

The agent must then use the extracted data and the original contract text to perform the required compliance checks. This can be done in a subsequent Claude call or a dedicated Python function that uses Claude for complex reasoning.

#### 3.2.1. Compliance Rules (Business Logic)

The agent must check and flag issues based on the following rules:

| Check ID | Rule | Severity |
|----------|------|----------|
| CC-001 | Required fields present (address, buyer, seller, price, closing date) | CRITICAL |
| CC-002 | Earnest money is 1-3% of purchase price | WARNING |
| CC-003 | Closing date is in the future | CRITICAL |
| CC-005 | All contingency dates are before the closing date | CRITICAL |
| CC-007 | No conflicting date sequences (e.g., inspection after financing) | CRITICAL |

#### 3.2.2. Final Output Structure

The final output of the Claude Agent must be a single JSON object containing the extracted data and the compliance flags, ready for insertion into Supabase.

```json
{
  "transaction_data": { /* ... all fields from 3.1.2 ... */ },
  "compliance_status": "string (PASS, WARNING, or FAIL)",
  "compliance_flags": [
    {
      "check_id": "string (e.g., CC-001)",
      "severity": "string (CRITICAL or WARNING)",
      "description": "string (Human-readable description of the issue)",
      "justification": "string (Claude's reasoning for the flag, citing contract text if possible)"
    }
    // ... list of all triggered flags
  ]
}
```

---

## 4. Development (D): Deliverables and Acceptance Criteria

### 4.1. Deliverables

1. **claude_compliance_agent.py**: A clean, well-commented Python script containing the core logic for the two-step Claude process (Extraction and Validation).

2. **test_cases.json**: A set of unit tests covering all compliance rules (CC-001, CC-002, CC-003, CC-005, CC-007) with mock contract text inputs.

3. **n8n_code_node_snippet.js**: A JavaScript/TypeScript snippet demonstrating how to call the Python agent from an n8n Code Node.

### 4.2. Acceptance Criteria

| Criterion | Target |
|-----------|--------|
| Accuracy (FR-3) | >95% for all extracted fields on a test set of 10 sample contracts. |
| Compliance Logic (FR-4) | 100% of test cases for CC-001, CC-003, CC-005, and CC-007 must pass. |
| Output Format | The final output must strictly conform to the JSON schema defined in 3.2.2. |
| Performance (NFR-1) | Processing time for a standard contract (10-15 pages) must be <45 seconds (allowing for Claude API latency). |
| Error Handling | The agent must gracefully handle API errors and return a structured error object to n8n if processing fails. |
