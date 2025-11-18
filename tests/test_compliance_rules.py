"""
Unit tests for Claude Compliance Agent

Tests all compliance rules (CC-001 through CC-007) using the test cases
defined in test_cases.json.

Run with: pytest tests/test_compliance_rules.py -v
"""

import json
import os
import sys
from pathlib import Path

import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from claude_compliance_agent import ClaudeComplianceAgent, TransactionData, ComplianceFlag


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def test_cases():
    """Load test cases from JSON file."""
    test_file = Path(__file__).parent / 'test_cases.json'
    with open(test_file) as f:
        data = json.load(f)
    return data['test_cases']


@pytest.fixture
def mock_agent():
    """Create a mock agent for testing compliance logic without API calls."""
    # We'll use this to test validation logic in isolation
    class MockAgent(ClaudeComplianceAgent):
        def __init__(self):
            # Skip parent __init__ to avoid needing API key
            self.model = "mock"

        def _extract_data(self, contract_text: str) -> TransactionData:
            """Mock extraction - parse from test case format."""
            # Simple parser for test contract format
            data = {
                'property_address': None,
                'buyer_name': None,
                'seller_name': None,
                'purchase_price': None,
                'earnest_money_amount': None,
                'closing_date': None,
                'inspection_deadline': None,
                'financing_contingency_date': None,
                'appraisal_contingency_date': None,
                'title_contingency_date': None,
                'listing_agent_name': None,
                'buyer_agent_name': None,
                'escrow_company': None,
                'title_company': None,
                'extraction_confidence_score': 0.95
            }

            lines = contract_text.split('\n')
            for line in lines:
                line = line.strip()

                if line.startswith('Property Address:'):
                    data['property_address'] = line.split(':', 1)[1].strip()
                elif line.startswith('Buyer:'):
                    data['buyer_name'] = line.split(':', 1)[1].strip()
                elif line.startswith('Seller:'):
                    data['seller_name'] = line.split(':', 1)[1].strip()
                elif line.startswith('Purchase Price:'):
                    price_str = line.split(':', 1)[1].strip().replace('$', '').replace(',', '')
                    data['purchase_price'] = float(price_str)
                elif line.startswith('Earnest Money Deposit:'):
                    amount_str = line.split(':', 1)[1].strip().split()[0].replace('$', '').replace(',', '')
                    data['earnest_money_amount'] = float(amount_str)
                elif 'Closing Date:' in line:
                    date_str = line.split('Closing Date:', 1)[1].strip().split()[0]
                    data['closing_date'] = date_str
                elif 'Inspection Deadline:' in line or '- Inspection Deadline:' in line:
                    date_str = line.split('Deadline:', 1)[1].strip().split()[0]
                    data['inspection_deadline'] = date_str
                elif 'Financing Contingency:' in line:
                    date_str = line.split('Contingency:', 1)[1].strip().split()[0]
                    data['financing_contingency_date'] = date_str
                elif 'Appraisal Contingency:' in line:
                    date_str = line.split('Contingency:', 1)[1].strip().split()[0]
                    data['appraisal_contingency_date'] = date_str
                elif 'Title Contingency:' in line:
                    date_str = line.split('Contingency:', 1)[1].strip().split()[0]
                    data['title_contingency_date'] = date_str
                elif line.startswith('- Listing Agent:') or line.startswith('Listing Agent:'):
                    data['listing_agent_name'] = line.split('Agent:', 1)[1].strip()
                elif line.startswith("- Buyer's Agent:") or line.startswith("Buyer's Agent:"):
                    data['buyer_agent_name'] = line.split('Agent:', 1)[1].strip()
                elif line.startswith('Escrow Company:'):
                    data['escrow_company'] = line.split(':', 1)[1].strip()
                elif line.startswith('Title Company:'):
                    data['title_company'] = line.split(':', 1)[1].strip()

            return TransactionData(**data)

    return MockAgent()


# ============================================================================
# COMPLIANCE RULE TESTS
# ============================================================================

def test_cc001_required_fields_present(mock_agent):
    """Test CC-001: Required fields must be present."""
    # Valid contract with all required fields
    valid_contract = """
    Property Address: 123 Main St, Chicago, IL 60601
    Buyer: John Doe
    Seller: Jane Smith
    Purchase Price: $500,000
    Closing Date: 2026-01-15
    """

    data = mock_agent._extract_data(valid_contract)
    flags = mock_agent._validate_compliance(data, valid_contract)

    # Should have no CC-001 flags
    cc001_flags = [f for f in flags if f.check_id == 'CC-001']
    assert len(cc001_flags) == 0, "Valid contract should not trigger CC-001"

    # Invalid contract missing buyer and seller
    invalid_contract = """
    Property Address: 123 Main St, Chicago, IL 60601
    Purchase Price: $500,000
    Closing Date: 2026-01-15
    """

    data = mock_agent._extract_data(invalid_contract)
    flags = mock_agent._validate_compliance(data, invalid_contract)

    # Should have CC-001 flag
    cc001_flags = [f for f in flags if f.check_id == 'CC-001']
    assert len(cc001_flags) == 1, "Missing required fields should trigger CC-001"
    assert cc001_flags[0].severity == 'CRITICAL'
    assert 'buyer_name' in cc001_flags[0].description
    assert 'seller_name' in cc001_flags[0].description


def test_cc002_earnest_money_percentage(mock_agent):
    """Test CC-002: Earnest money should be 1-3% of purchase price."""
    # Valid: 2% earnest money
    valid_contract = """
    Property Address: 123 Main St
    Buyer: John Doe
    Seller: Jane Smith
    Purchase Price: $500,000
    Earnest Money Deposit: $10,000
    Closing Date: 2026-01-15
    """

    data = mock_agent._extract_data(valid_contract)
    flags = mock_agent._validate_compliance(data, valid_contract)
    cc002_flags = [f for f in flags if f.check_id == 'CC-002']
    assert len(cc002_flags) == 0, "2% earnest money should not trigger CC-002"

    # Too low: 0.5%
    low_contract = """
    Property Address: 123 Main St
    Buyer: John Doe
    Seller: Jane Smith
    Purchase Price: $500,000
    Earnest Money Deposit: $2,500
    Closing Date: 2026-01-15
    """

    data = mock_agent._extract_data(low_contract)
    flags = mock_agent._validate_compliance(data, low_contract)
    cc002_flags = [f for f in flags if f.check_id == 'CC-002']
    assert len(cc002_flags) == 1, "0.5% earnest money should trigger CC-002"
    assert cc002_flags[0].severity == 'WARNING'

    # Too high: 5%
    high_contract = """
    Property Address: 123 Main St
    Buyer: John Doe
    Seller: Jane Smith
    Purchase Price: $500,000
    Earnest Money Deposit: $25,000
    Closing Date: 2026-01-15
    """

    data = mock_agent._extract_data(high_contract)
    flags = mock_agent._validate_compliance(data, high_contract)
    cc002_flags = [f for f in flags if f.check_id == 'CC-002']
    assert len(cc002_flags) == 1, "5% earnest money should trigger CC-002"
    assert cc002_flags[0].severity == 'WARNING'


def test_cc003_closing_date_future(mock_agent):
    """Test CC-003: Closing date must be in the future."""
    # Valid: Future date
    valid_contract = """
    Property Address: 123 Main St
    Buyer: John Doe
    Seller: Jane Smith
    Purchase Price: $500,000
    Closing Date: 2026-12-31
    """

    data = mock_agent._extract_data(valid_contract)
    flags = mock_agent._validate_compliance(data, valid_contract)
    cc003_flags = [f for f in flags if f.check_id == 'CC-003']
    assert len(cc003_flags) == 0, "Future closing date should not trigger CC-003"

    # Invalid: Past date
    invalid_contract = """
    Property Address: 123 Main St
    Buyer: John Doe
    Seller: Jane Smith
    Purchase Price: $500,000
    Closing Date: 2020-01-01
    """

    data = mock_agent._extract_data(invalid_contract)
    flags = mock_agent._validate_compliance(data, invalid_contract)
    cc003_flags = [f for f in flags if f.check_id == 'CC-003']
    assert len(cc003_flags) == 1, "Past closing date should trigger CC-003"
    assert cc003_flags[0].severity == 'CRITICAL'


def test_cc005_contingencies_before_closing(mock_agent):
    """Test CC-005: All contingency dates must be before closing date."""
    # Valid: All contingencies before closing
    valid_contract = """
    Property Address: 123 Main St
    Buyer: John Doe
    Seller: Jane Smith
    Purchase Price: $500,000
    Closing Date: 2026-01-31
    - Inspection Deadline: 2026-01-05
    - Financing Contingency: 2026-01-15
    - Appraisal Contingency: 2026-01-10
    - Title Contingency: 2026-01-20
    """

    data = mock_agent._extract_data(valid_contract)
    flags = mock_agent._validate_compliance(data, valid_contract)
    cc005_flags = [f for f in flags if f.check_id == 'CC-005']
    assert len(cc005_flags) == 0, "Valid contingency dates should not trigger CC-005"

    # Invalid: Inspection after closing
    invalid_contract = """
    Property Address: 123 Main St
    Buyer: John Doe
    Seller: Jane Smith
    Purchase Price: $500,000
    Closing Date: 2026-01-15
    - Inspection Deadline: 2026-01-20
    """

    data = mock_agent._extract_data(invalid_contract)
    flags = mock_agent._validate_compliance(data, invalid_contract)
    cc005_flags = [f for f in flags if f.check_id == 'CC-005']
    assert len(cc005_flags) >= 1, "Contingency after closing should trigger CC-005"
    assert all(f.severity == 'CRITICAL' for f in cc005_flags)


def test_cc007_date_sequence_logic(mock_agent):
    """Test CC-007: No conflicting date sequences."""
    # Valid: Inspection -> Appraisal -> Financing
    valid_contract = """
    Property Address: 123 Main St
    Buyer: John Doe
    Seller: Jane Smith
    Purchase Price: $500,000
    Closing Date: 2026-01-31
    - Inspection Deadline: 2026-01-05
    - Appraisal Contingency: 2026-01-10
    - Financing Contingency: 2026-01-15
    """

    data = mock_agent._extract_data(valid_contract)
    flags = mock_agent._validate_compliance(data, valid_contract)
    cc007_flags = [f for f in flags if f.check_id == 'CC-007']
    assert len(cc007_flags) == 0, "Valid date sequence should not trigger CC-007"

    # Invalid: Inspection after financing
    invalid_contract = """
    Property Address: 123 Main St
    Buyer: John Doe
    Seller: Jane Smith
    Purchase Price: $500,000
    Closing Date: 2026-01-31
    - Financing Contingency: 2026-01-10
    - Inspection Deadline: 2026-01-15
    """

    data = mock_agent._extract_data(invalid_contract)
    flags = mock_agent._validate_compliance(data, invalid_contract)
    cc007_flags = [f for f in flags if f.check_id == 'CC-007']
    assert len(cc007_flags) >= 1, "Inspection after financing should trigger CC-007"
    assert all(f.severity == 'CRITICAL' for f in cc007_flags)


# ============================================================================
# INTEGRATION TESTS WITH TEST CASES
# ============================================================================

@pytest.mark.parametrize("test_case", [
    pytest.param(tc, id=tc['test_id'])
    for tc in json.load(open(Path(__file__).parent / 'test_cases.json'))['test_cases']
])
def test_all_test_cases(mock_agent, test_case):
    """Test all cases from test_cases.json."""
    contract_text = test_case['contract_text']
    expected_status = test_case['expected_status']
    expected_flag_ids = [f['check_id'] for f in test_case.get('expected_flags', [])]

    # Extract and validate
    data = mock_agent._extract_data(contract_text)
    flags = mock_agent._validate_compliance(data, contract_text)
    status = mock_agent._determine_status(flags)

    # Check status
    assert status == expected_status, (
        f"Test {test_case['test_id']}: Expected status {expected_status}, got {status}"
    )

    # Check flag IDs
    actual_flag_ids = [f.check_id for f in flags]
    for expected_id in expected_flag_ids:
        assert expected_id in actual_flag_ids, (
            f"Test {test_case['test_id']}: Expected flag {expected_id} not found. "
            f"Actual flags: {actual_flag_ids}"
        )


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

def test_error_handling_invalid_json():
    """Test that agent handles invalid JSON gracefully."""
    # This would require mocking Claude API response
    # For now, we test the data model validation
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        TransactionData(
            extraction_confidence_score=1.5  # Invalid: > 1.0
        )


def test_compliance_status_validation():
    """Test that compliance status values are validated."""
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        from claude_compliance_agent import ComplianceResult
        ComplianceResult(
            transaction_data=TransactionData(),
            compliance_status="INVALID_STATUS",  # Should fail
            compliance_flags=[]
        )


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, '-v', '--tb=short'])
