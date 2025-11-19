"""
Document Validation Specialist - Claude-based validation function
Validates specific rules against document text for checklist validation.

This function is designed to be called from n8n workflows to validate
individual rules against contract documents.

Author: Generated for n8n workflow integration
Date: November 2025
"""

import json
import os
from typing import Dict, Any, Optional

from anthropic import Anthropic
import structlog

# Configure structured logging
logger = structlog.get_logger()


# ============================================================================
# DOCUMENT VALIDATION SPECIALIST
# ============================================================================

class DocumentValidationSpecialist:
    """
    Validates specific rules against document text using Claude.

    This specialist focuses on checklist-style validation where each
    rule is evaluated independently against the document.
    """

    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-opus-20240229"):
        """
        Initialize the Document Validation Specialist.

        Args:
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
            model: Claude model to use (default: claude-3-opus-20240229)
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY must be provided or set in environment")

        self.model = model
        self.client = Anthropic(api_key=self.api_key)
        self.max_tokens = int(os.getenv("VALIDATION_MAX_TOKENS", "2048"))
        self.temperature = float(os.getenv("VALIDATION_TEMPERATURE", "0.0"))

        logger.info("Document Validation Specialist initialized", model=self.model)

    def validate_document_compliance(
        self,
        document_text: str,
        validation_rule: str
    ) -> Dict[str, Any]:
        """
        Validate a specific rule against the document text.

        Args:
            document_text: Raw text content of the document to validate
            validation_rule: Specific rule to check (e.g., "Check for signatures from Buyer and Seller")

        Returns:
            Dictionary containing validation results in structured JSON format
        """
        try:
            logger.info(
                "Starting document validation",
                text_length=len(document_text),
                rule=validation_rule[:100]  # Log first 100 chars of rule
            )

            # Build the prompt
            prompt = self._build_validation_prompt(document_text, validation_rule)

            # Call Claude API
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system=self._get_system_prompt(),
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            # Parse Claude's response
            response_text = response.content[0].text

            # Extract JSON from response (Claude might wrap it in markdown)
            validation_result = self._parse_json_response(response_text)

            logger.info(
                "Document validation complete",
                status=validation_result.get("status"),
                rule_passed=validation_result.get("rule_passed")
            )

            return validation_result

        except Exception as e:
            logger.error("Document validation failed", error=str(e), exc_info=True)
            return {
                "error": True,
                "error_type": type(e).__name__,
                "error_message": str(e),
                "status": "ERROR",
                "rule_passed": False
            }

    def _get_system_prompt(self) -> str:
        """
        Return the system prompt for document validation.
        """
        system_prompt = """You are a Document Validation Specialist. Your task is to verify if the provided document text is a valid, complete, and signed version of the requested form. Your output MUST be a single JSON object."""

        return system_prompt

    def _get_json_schema(self) -> Dict[str, Any]:
        """
        Return the JSON schema for validation results.
        """
        schema = {
            "type": "object",
            "properties": {
                "validation_status": {
                    "type": "string",
                    "enum": ["VALID", "INVALID_MISSING_SIGNATURE", "INVALID_WRONG_VERSION", "INVALID_OTHER"],
                    "description": "The result of the validation check."
                },
                "document_title": {
                    "type": "string",
                    "description": "The title of the document as identified by Claude."
                },
                "confidence_score": {
                    "type": "number",
                    "description": "Claude's confidence (0.0 to 1.0) in the validation status."
                },
                "justification": {
                    "type": "string",
                    "description": "A brief explanation of the validation status, especially if invalid."
                }
            },
            "required": ["validation_status", "document_title", "confidence_score", "justification"]
        }

        return schema

    def _build_validation_prompt(self, document_text: str, validation_rule: str) -> str:
        """
        Build the user message prompt for Claude.

        Args:
            document_text: The document to validate
            validation_rule: The specific rule to check

        Returns:
            Formatted prompt string
        """
        schema = self._get_json_schema()

        prompt = f"""Document Text:
{document_text}

Validation Rule:
{validation_rule}

Please validate whether the above rule is satisfied in the provided document text.

Return your response as valid JSON matching this schema:
{json.dumps(schema, indent=2)}

IMPORTANT: Return ONLY the JSON object, with no additional text or explanation outside the JSON."""

        return prompt

    def _parse_json_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse JSON from Claude's response, handling markdown code blocks if present.

        Args:
            response_text: Raw response from Claude

        Returns:
            Parsed JSON dictionary
        """
        # Try direct JSON parse first
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            pass

        # Try extracting from markdown code block
        import re
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # Try finding JSON object in the text
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass

        # If all else fails, raise error
        raise ValueError(f"Could not parse JSON from Claude response: {response_text[:200]}...")


# ============================================================================
# CONVENIENCE FUNCTION FOR N8N INTEGRATION
# ============================================================================

def validate_document_compliance(
    document_text: str,
    validation_rule: str,
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Convenience function for n8n integration.

    Validates a specific rule against document text.

    Args:
        document_text: Raw text of the document to validate
        validation_rule: Specific rule to check (e.g., "Check for signatures from Buyer and Seller")
        api_key: Optional API key (uses env var if not provided)

    Returns:
        Dictionary with validation results in structured JSON format

    Example:
        >>> result = validate_document_compliance(
        ...     document_text="[HOA Addendum text...]",
        ...     validation_rule="Verify that the document is signed by both the Buyer and the Seller."
        ... )
        >>> print(result['status'])  # PASS, FAIL, or INCONCLUSIVE
        >>> print(result['rule_passed'])  # True or False
    """
    validator = DocumentValidationSpecialist(api_key=api_key)
    return validator.validate_document_compliance(document_text, validation_rule)


# ============================================================================
# MAIN - FOR TESTING/DEBUGGING
# ============================================================================

if __name__ == "__main__":
    # Example usage
    import sys
    from dotenv import load_dotenv

    load_dotenv()

    # Sample document text
    sample_document = """
    HOMEOWNERS ASSOCIATION (HOA) ADDENDUM

    Property Address: 123 Main Street, Springfield, IL 62701

    This addendum is made between:
    Buyer: John Smith and Jane Smith
    Seller: Robert Johnson

    The Buyer acknowledges receipt of the following HOA documents:
    - CC&Rs (Covenants, Conditions & Restrictions) dated January 2024
    - HOA Bylaws (latest version - Rev 3.2)
    - Financial statements for the past 12 months

    Monthly HOA Fee: $250.00
    Special Assessment: None currently planned

    Buyer Signature: ____John Smith____ Date: 11/15/2025
    Buyer Signature: ____Jane Smith____ Date: 11/15/2025

    Seller Signature: ____Robert Johnson____ Date: 11/15/2025
    """

    # Sample validation rules
    test_rules = [
        "Verify that the document is signed by both the Buyer and the Seller.",
        "Check that the monthly HOA fee amount is clearly stated.",
        "Confirm that the Buyer received the HOA CC&Rs.",
        "Verify the document is the latest version of the HOA Addendum."
    ]

    print("=" * 80)
    print("Document Validation Specialist - Test Run")
    print("=" * 80)

    for i, rule in enumerate(test_rules, 1):
        print(f"\n{i}. Testing Rule: {rule}")
        print("-" * 80)

        result = validate_document_compliance(
            document_text=sample_document,
            validation_rule=rule
        )

        print(json.dumps(result, indent=2))
        print("-" * 80)
