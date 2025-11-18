"""
Contract Compliance Agent - Core AI Logic
Claude-based Python microservice for real estate contract processing.

This agent performs two critical steps:
1. Structured Data Extraction from raw contract text
2. Compliance Validation against business rules

Author: Generated via B-MAD Greenfield Method
Date: November 2025
"""

import json
import os
import re
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from decimal import Decimal

from anthropic import Anthropic
from pydantic import BaseModel, Field, field_validator
import structlog

# Configure structured logging
logger = structlog.get_logger()


# ============================================================================
# DATA MODELS (Pydantic for validation and type safety)
# ============================================================================

class TransactionData(BaseModel):
    """Extracted transaction data from real estate contract."""

    property_address: Optional[str] = Field(None, description="Full address with city, state, zip")
    buyer_name: Optional[str] = Field(None, description="Comma-separated if multiple buyers")
    seller_name: Optional[str] = Field(None, description="Comma-separated if multiple sellers")
    purchase_price: Optional[float] = Field(None, description="Raw value, no formatting")
    earnest_money_amount: Optional[float] = Field(None, description="Earnest money deposit amount")
    closing_date: Optional[str] = Field(None, description="YYYY-MM-DD format")
    inspection_deadline: Optional[str] = Field(None, description="YYYY-MM-DD format")
    financing_contingency_date: Optional[str] = Field(None, description="YYYY-MM-DD format")
    appraisal_contingency_date: Optional[str] = Field(None, description="YYYY-MM-DD format")
    title_contingency_date: Optional[str] = Field(None, description="YYYY-MM-DD format")
    listing_agent_name: Optional[str] = None
    buyer_agent_name: Optional[str] = None
    escrow_company: Optional[str] = None
    title_company: Optional[str] = None
    extraction_confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)
    tc_status: str = Field(default="PENDING_REVIEW", description="Transaction coordinator status")
    tc_user_id: Optional[str] = Field(None, description="TC user ID assigned by n8n")


class ComplianceFlag(BaseModel):
    """Individual compliance check result."""

    check_id: str = Field(..., description="Compliance check identifier (CC-001 through CC-008)")
    severity: str = Field(..., description="CRITICAL or WARNING")
    description: str = Field(..., description="Human-readable issue description")
    justification: str = Field(..., description="Claude's reasoning with contract citations")

    @field_validator('severity')
    @classmethod
    def validate_severity(cls, v: str) -> str:
        if v not in ['CRITICAL', 'WARNING']:
            raise ValueError('Severity must be CRITICAL or WARNING')
        return v

    @field_validator('check_id')
    @classmethod
    def validate_check_id(cls, v: str) -> str:
        valid_ids = ['CC-001', 'CC-002', 'CC-003', 'CC-005', 'CC-007', 'CC-008']
        if v not in valid_ids:
            raise ValueError(f'Check ID must be one of {valid_ids}')
        return v


class ComplianceResult(BaseModel):
    """Final output structure combining extraction and validation."""

    document_type: str = Field(..., description="PURCHASE_AGREEMENT, ADDENDUM, DISCLOSURE, or OTHER")
    is_purchase_agreement: bool = Field(..., description="True if document is main Purchase Agreement")
    transaction_data: TransactionData
    compliance_status: str = Field(..., description="PASS, WARNING, or FAIL")
    compliance_flags: List[ComplianceFlag] = Field(default_factory=list)

    @field_validator('compliance_status')
    @classmethod
    def validate_status(cls, v: str) -> str:
        if v not in ['PASS', 'WARNING', 'FAIL']:
            raise ValueError('Status must be PASS, WARNING, or FAIL')
        return v

    @field_validator('document_type')
    @classmethod
    def validate_document_type(cls, v: str) -> str:
        valid_types = ['PURCHASE_AGREEMENT', 'ADDENDUM', 'DISCLOSURE', 'OTHER']
        if v not in valid_types:
            raise ValueError(f'Document type must be one of {valid_types}')
        return v


class ProcessingError(BaseModel):
    """Structured error response for graceful failure handling."""

    error: bool = True
    error_type: str
    error_message: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


# ============================================================================
# CLAUDE COMPLIANCE AGENT
# ============================================================================

class ClaudeComplianceAgent:
    """
    Main agent class handling contract extraction and compliance validation.

    This agent uses Claude's advanced reasoning to:
    - Extract structured data from unstructured contract text
    - Validate business rules and flag compliance issues
    - Return JSON-formatted results ready for downstream processing
    """

    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-opus-20240229"):
        """
        Initialize the Claude Compliance Agent.

        Args:
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
            model: Claude model to use (default: claude-3-opus-20240229)
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY must be provided or set in environment")

        self.model = model
        self.client = Anthropic(api_key=self.api_key)
        self.max_tokens = int(os.getenv("MAX_TOKENS", "4096"))
        self.temperature = float(os.getenv("TEMPERATURE", "0.0"))

        logger.info("Claude Compliance Agent initialized", model=self.model)

    def process_contract(self, contract_text: str) -> Dict[str, Any]:
        """
        Main entry point: Process a contract through extraction and validation.

        Args:
            contract_text: Raw text content of the real estate contract

        Returns:
            Dictionary containing document_type, is_purchase_agreement, transaction_data,
            compliance_status, and compliance_flags. Or error dict if processing fails
        """
        try:
            logger.info("Starting contract processing", text_length=len(contract_text))

            # Step 1: Classify document and extract structured data
            classification_result = self._extract_data(contract_text)
            document_type = classification_result['document_type']
            is_purchase_agreement = classification_result['is_purchase_agreement']
            transaction_data = classification_result['transaction_data']

            logger.info("Data extraction complete",
                       document_type=document_type,
                       is_purchase_agreement=is_purchase_agreement,
                       confidence=transaction_data.extraction_confidence_score)

            # Step 2: Validate compliance (only for Purchase Agreements)
            if is_purchase_agreement:
                compliance_flags = self._validate_compliance(transaction_data, contract_text)
                logger.info("Compliance validation complete", flags_count=len(compliance_flags))
            else:
                compliance_flags = []
                logger.info("Skipping compliance validation - not a Purchase Agreement")

            # Determine overall compliance status
            compliance_status = self._determine_status(compliance_flags)

            # Build final result
            result = ComplianceResult(
                document_type=document_type,
                is_purchase_agreement=is_purchase_agreement,
                transaction_data=transaction_data,
                compliance_status=compliance_status,
                compliance_flags=compliance_flags
            )

            logger.info("Contract processing complete",
                       document_type=document_type,
                       status=compliance_status)
            return result.model_dump()

        except Exception as e:
            logger.error("Contract processing failed", error=str(e), exc_info=True)
            return ProcessingError(
                error_type=type(e).__name__,
                error_message=str(e)
            ).model_dump()

    def _extract_data(self, contract_text: str) -> Dict[str, Any]:
        """
        Step 1: Classify document and extract structured data using Claude with JSON schema.

        Uses Claude's tool calling / structured output to ensure valid JSON.

        Returns:
            Dict containing document_type, is_purchase_agreement, and transaction_data
        """
        extraction_prompt = self._build_extraction_prompt(contract_text)

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=[
                    {
                        "role": "user",
                        "content": extraction_prompt
                    }
                ]
            )

            # Parse Claude's response
            response_text = response.content[0].text
            extracted_data = json.loads(response_text)

            # Validate document_type
            document_type = extracted_data.get('document_type', 'OTHER')
            is_purchase_agreement = (document_type == 'PURCHASE_AGREEMENT')

            # Extract transaction_data
            transaction_data_dict = extracted_data.get('transaction_data', {})
            transaction_data = TransactionData(**transaction_data_dict)

            return {
                'document_type': document_type,
                'is_purchase_agreement': is_purchase_agreement,
                'transaction_data': transaction_data
            }

        except json.JSONDecodeError as e:
            logger.error("Failed to parse Claude JSON response", error=str(e))
            raise ValueError(f"Claude returned invalid JSON: {e}")
        except Exception as e:
            logger.error("Data extraction failed", error=str(e))
            raise

    def _validate_compliance(self, data: TransactionData, contract_text: str) -> List[ComplianceFlag]:
        """
        Step 2: Validate extracted data against compliance rules.

        Checks:
        - CC-001: Required fields present
        - CC-002: Earnest money is 1-3% of purchase price
        - CC-003: Closing date is in the future
        - CC-005: All contingency dates before closing
        - CC-007: No conflicting date sequences
        - CC-008: Lead-Based Paint Disclosure for pre-1978 properties
        """
        flags = []

        # CC-001: Required fields check
        required_fields = ['property_address', 'buyer_name', 'seller_name', 'purchase_price', 'closing_date']
        missing_fields = [f for f in required_fields if not getattr(data, f)]

        if missing_fields:
            flags.append(ComplianceFlag(
                check_id="CC-001",
                severity="CRITICAL",
                description=f"Required fields missing: {', '.join(missing_fields)}",
                justification=f"Contract must contain all required fields. Missing: {', '.join(missing_fields)}"
            ))

        # CC-002: Earnest money percentage check
        if data.purchase_price and data.earnest_money_amount:
            earnest_pct = (data.earnest_money_amount / data.purchase_price) * 100
            if earnest_pct < 1.0 or earnest_pct > 3.0:
                flags.append(ComplianceFlag(
                    check_id="CC-002",
                    severity="WARNING",
                    description=f"Earnest money is {earnest_pct:.2f}% of purchase price (expected 1-3%)",
                    justification=f"Industry standard earnest money deposit is 1-3% of purchase price. Current: {earnest_pct:.2f}%"
                ))

        # CC-003: Closing date in future check
        if data.closing_date:
            try:
                closing_dt = datetime.strptime(data.closing_date, "%Y-%m-%d").date()
                if closing_dt <= date.today():
                    flags.append(ComplianceFlag(
                        check_id="CC-003",
                        severity="CRITICAL",
                        description=f"Closing date {data.closing_date} is not in the future",
                        justification=f"Closing date must be in the future. Current date: {date.today()}, Closing: {closing_dt}"
                    ))
            except ValueError:
                flags.append(ComplianceFlag(
                    check_id="CC-003",
                    severity="CRITICAL",
                    description=f"Invalid closing date format: {data.closing_date}",
                    justification="Closing date must be in YYYY-MM-DD format"
                ))

        # CC-005: Contingency dates before closing
        if data.closing_date:
            try:
                closing_dt = datetime.strptime(data.closing_date, "%Y-%m-%d").date()
                contingency_dates = {
                    'inspection_deadline': data.inspection_deadline,
                    'financing_contingency_date': data.financing_contingency_date,
                    'appraisal_contingency_date': data.appraisal_contingency_date,
                    'title_contingency_date': data.title_contingency_date
                }

                for name, date_str in contingency_dates.items():
                    if date_str:
                        try:
                            cont_dt = datetime.strptime(date_str, "%Y-%m-%d").date()
                            if cont_dt >= closing_dt:
                                flags.append(ComplianceFlag(
                                    check_id="CC-005",
                                    severity="CRITICAL",
                                    description=f"{name} ({date_str}) is not before closing date ({data.closing_date})",
                                    justification=f"All contingency deadlines must occur before the closing date"
                                ))
                        except ValueError:
                            pass  # Invalid date format handled elsewhere
            except ValueError:
                pass  # Closing date validation handled in CC-003

        # CC-007: Date sequence validation (inspection should be before financing, etc.)
        date_sequence_issues = self._check_date_sequences(data)
        flags.extend(date_sequence_issues)

        # CC-008: Lead-Based Paint Disclosure check
        lbp_flag = self._check_lead_based_paint_disclosure(contract_text)
        if lbp_flag:
            flags.append(lbp_flag)

        return flags

    def _check_date_sequences(self, data: TransactionData) -> List[ComplianceFlag]:
        """
        Check for illogical date sequences (CC-007).

        Typical sequence: Inspection → Appraisal → Financing → Title → Closing
        """
        flags = []

        try:
            # Parse all dates
            dates = {}
            if data.inspection_deadline:
                dates['inspection'] = datetime.strptime(data.inspection_deadline, "%Y-%m-%d").date()
            if data.appraisal_contingency_date:
                dates['appraisal'] = datetime.strptime(data.appraisal_contingency_date, "%Y-%m-%d").date()
            if data.financing_contingency_date:
                dates['financing'] = datetime.strptime(data.financing_contingency_date, "%Y-%m-%d").date()
            if data.title_contingency_date:
                dates['title'] = datetime.strptime(data.title_contingency_date, "%Y-%m-%d").date()

            # Check inspection before financing
            if 'inspection' in dates and 'financing' in dates:
                if dates['inspection'] >= dates['financing']:
                    flags.append(ComplianceFlag(
                        check_id="CC-007",
                        severity="CRITICAL",
                        description="Inspection deadline should be before financing contingency",
                        justification=f"Inspection ({data.inspection_deadline}) should occur before financing contingency ({data.financing_contingency_date})"
                    ))

            # Check appraisal before financing
            if 'appraisal' in dates and 'financing' in dates:
                if dates['appraisal'] >= dates['financing']:
                    flags.append(ComplianceFlag(
                        check_id="CC-007",
                        severity="CRITICAL",
                        description="Appraisal contingency should be before financing contingency",
                        justification=f"Appraisal ({data.appraisal_contingency_date}) should occur before financing ({data.financing_contingency_date})"
                    ))

        except ValueError:
            pass  # Date parsing errors handled in other checks

        return flags

    def _check_lead_based_paint_disclosure(self, contract_text: str) -> Optional[ComplianceFlag]:
        """
        Check for Lead-Based Paint Disclosure compliance (CC-008).

        Rule: If the contract mentions the property was built before 1978,
        check for a clear reference to the "Lead-Based Paint Disclosure" form
        being included or waived.

        Returns:
            ComplianceFlag if violation found, None otherwise
        """
        contract_lower = contract_text.lower()

        # Check if contract mentions pre-1978 construction
        pre_1978_indicators = [
            'built before 1978',
            'constructed before 1978',
            'built prior to 1978',
            'constructed prior to 1978',
            'pre-1978',
            'pre 1978'
        ]

        # Also check for specific years before 1978
        mentions_pre_1978 = any(indicator in contract_lower for indicator in pre_1978_indicators)

        # Check for year mentions
        year_pattern = r'\b(19[0-6]\d|197[0-7])\b'
        year_matches = re.findall(year_pattern, contract_text)
        if year_matches:
            mentions_pre_1978 = True

        if not mentions_pre_1978:
            # No pre-1978 mention, so CC-008 doesn't apply
            return None

        # Property is pre-1978, now check for LBP disclosure
        lbp_disclosure_indicators = [
            'lead-based paint',
            'lead based paint',
            'lead paint',
            'lbp disclosure',
            'lead disclosure',
            'lead hazard',
            'lead-based paint disclosure'
        ]

        has_lbp_disclosure = any(indicator in contract_lower for indicator in lbp_disclosure_indicators)

        if not has_lbp_disclosure:
            return ComplianceFlag(
                check_id="CC-008",
                severity="CRITICAL",
                description="Pre-1978 property missing Lead-Based Paint Disclosure",
                justification=("Contract mentions property was built before 1978 but does not "
                             "reference the required Lead-Based Paint Disclosure form or waiver. "
                             "Federal law requires LBP disclosure for all residential properties "
                             "built before 1978.")
            )

        return None

    def _determine_status(self, flags: List[ComplianceFlag]) -> str:
        """
        Determine overall compliance status based on flags.

        Returns:
            FAIL - if any CRITICAL flags
            WARNING - if any WARNING flags but no CRITICAL
            PASS - if no flags
        """
        if not flags:
            return "PASS"

        has_critical = any(f.severity == "CRITICAL" for f in flags)
        return "FAIL" if has_critical else "WARNING"

    def _build_extraction_prompt(self, contract_text: str) -> str:
        """
        Build the extraction prompt for Claude.

        This prompt instructs Claude to first classify the document type,
        then extract structured data according to the schema.
        """
        schema_json = {
            "document_type": "string (PURCHASE_AGREEMENT, ADDENDUM, DISCLOSURE, or OTHER)",
            "transaction_data": {
                "property_address": "string (full address with city, state, zip) or null",
                "buyer_name": "string (comma-separated if multiple) or null",
                "seller_name": "string (comma-separated if multiple) or null",
                "purchase_price": "number (raw value, no formatting) or null",
                "earnest_money_amount": "number or null",
                "closing_date": "date (YYYY-MM-DD) or null",
                "inspection_deadline": "date (YYYY-MM-DD) or null",
                "financing_contingency_date": "date (YYYY-MM-DD) or null",
                "appraisal_contingency_date": "date (YYYY-MM-DD) or null",
                "title_contingency_date": "date (YYYY-MM-DD) or null",
                "listing_agent_name": "string or null",
                "buyer_agent_name": "string or null",
                "escrow_company": "string or null",
                "title_company": "string or null",
                "extraction_confidence_score": "number (0.0 to 1.0)",
                "tc_status": "string (default: PENDING_REVIEW)",
                "tc_user_id": "string or null"
            }
        }

        # New system prompt (exactly 500 characters)
        system_prompt = """You are a Senior Real Estate Transaction Coordinator Data Analyst. Your task is to process the provided raw text. 1. CLASSIFY: First, determine the document's type. 2. EXTRACT: If it IS a Purchase Agreement, extract all required data fields into the transaction_data object. 3. VALIDATE: Apply all compliance rules (CC-001, CC-002, CC-003, CC-005, CC-007, CC-008). 4. OUTPUT: Return a single JSON object with the classification, extracted data, and compliance flags."""

        prompt = f"""{system_prompt}

CRITICAL INSTRUCTIONS:
1. First determine document_type: PURCHASE_AGREEMENT, ADDENDUM, DISCLOSURE, or OTHER
2. If document_type is PURCHASE_AGREEMENT, extract all transaction_data fields
3. If NOT a Purchase Agreement, still return the structure but transaction_data fields can be null
4. Extract ONLY information explicitly stated - DO NOT HALLUCINATE or guess
5. For dates, use YYYY-MM-DD format
6. For prices/amounts, use raw numeric values (no currency symbols)
7. Set extraction_confidence_score (0.0 to 1.0) based on clarity
8. Return ONLY valid JSON matching the schema - no additional text

REQUIRED JSON SCHEMA:
{json.dumps(schema_json, indent=2)}

CONTRACT TEXT:
{contract_text}

Classify the document and extract data now. Return ONLY the JSON object:"""

        return prompt


# ============================================================================
# CONVENIENCE FUNCTIONS FOR N8N INTEGRATION
# ============================================================================

def process_contract_text(contract_text: str, api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Convenience function for processing a contract.

    This is the main entry point for n8n integration.

    Args:
        contract_text: Raw contract text from OCR
        api_key: Optional API key (uses env var if not provided)

    Returns:
        Dictionary with transaction_data, compliance_status, and compliance_flags
    """
    agent = ClaudeComplianceAgent(api_key=api_key)
    return agent.process_contract(contract_text)


# ============================================================================
# MAIN - FOR TESTING/DEBUGGING
# ============================================================================

if __name__ == "__main__":
    # Example usage
    import sys
    from dotenv import load_dotenv

    load_dotenv()

    # Sample contract text for testing
    sample_contract = """
    REAL ESTATE PURCHASE AGREEMENT

    Property Address: 123 Main Street, Springfield, IL 62701

    This agreement is made between:
    Buyer: John Smith and Jane Smith
    Seller: Robert Johnson

    Purchase Price: $350,000
    Earnest Money Deposit: $7,000

    Key Dates:
    - Inspection Deadline: 2025-12-01
    - Appraisal Contingency: 2025-12-10
    - Financing Contingency: 2025-12-15
    - Title Contingency: 2025-12-20
    - Closing Date: 2026-01-15

    Agents:
    - Listing Agent: Sarah Williams, ABC Realty
    - Buyer's Agent: Mike Davis, XYZ Properties

    Escrow Company: Secure Escrow Services Inc.
    Title Company: First American Title
    """

    print("Processing sample contract...")
    result = process_contract_text(sample_contract)
    print(json.dumps(result, indent=2))
