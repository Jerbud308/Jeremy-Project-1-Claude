"""
Usage Examples for Claude Compliance Agent

This file demonstrates various ways to use the Contract Compliance Agent.
"""

import json
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from claude_compliance_agent import (
    ClaudeComplianceAgent,
    process_contract_text
)


# ============================================================================
# EXAMPLE 1: Simple Usage with Convenience Function
# ============================================================================

def example_1_simple_usage():
    """Most straightforward way to process a contract."""
    print("=" * 80)
    print("EXAMPLE 1: Simple Usage")
    print("=" * 80)

    contract_text = """
    REAL ESTATE PURCHASE AGREEMENT

    Property Address: 456 Oak Avenue, Chicago, IL 60614

    This agreement dated November 18, 2025 is made between:
    Buyer: Alice Johnson
    Seller: David Martinez

    Purchase Price: $425,000
    Earnest Money Deposit: $8,500

    Key Dates:
    - Inspection Deadline: December 5, 2025
    - Appraisal Contingency: December 12, 2025
    - Financing Contingency: December 20, 2025
    - Title Contingency: December 28, 2025
    - Closing Date: January 15, 2026

    Agents:
    - Listing Agent: Tom Wilson, Premier Realty
    - Buyer's Agent: Lisa Chen, HomeFirst Properties

    Escrow Company: Chicago Escrow Services
    Title Company: North Shore Title Company
    """

    # Process the contract
    result = process_contract_text(contract_text)

    # Display results
    print(f"\nCompliance Status: {result['compliance_status']}")
    print(f"Number of Flags: {len(result['compliance_flags'])}")

    if result['compliance_flags']:
        print("\nCompliance Issues:")
        for flag in result['compliance_flags']:
            print(f"  - [{flag['severity']}] {flag['check_id']}: {flag['description']}")
    else:
        print("\n✅ No compliance issues found!")

    print(f"\nExtracted Data:")
    print(f"  Property: {result['transaction_data']['property_address']}")
    print(f"  Buyer: {result['transaction_data']['buyer_name']}")
    print(f"  Seller: {result['transaction_data']['seller_name']}")
    print(f"  Price: ${result['transaction_data']['purchase_price']:,.2f}")
    print(f"  Closing: {result['transaction_data']['closing_date']}")
    print(f"  Confidence: {result['transaction_data']['extraction_confidence_score']:.2%}")


# ============================================================================
# EXAMPLE 2: Using Agent Class Directly
# ============================================================================

def example_2_agent_class():
    """Using the agent class for more control."""
    print("\n" + "=" * 80)
    print("EXAMPLE 2: Using Agent Class")
    print("=" * 80)

    # Initialize agent with custom settings
    agent = ClaudeComplianceAgent(
        model="claude-3-opus-20240229"
        # api_key is loaded from environment
    )

    contract_text = """
    REAL ESTATE PURCHASE AGREEMENT

    Property Address: 789 Elm Street, Boston, MA 02101

    Purchase Price: $550,000
    Earnest Money Deposit: $2,750 (0.5% - below standard)

    Closing Date: February 1, 2026

    Inspection Deadline: December 10, 2025
    Financing Contingency: December 20, 2025

    Escrow Company: Boston Escrow LLC
    """

    # Process
    result = agent.process_contract(contract_text)

    # Check for errors
    if result.get('error'):
        print(f"❌ Processing failed: {result['error_message']}")
        return

    # Analyze results
    print(f"\nStatus: {result['compliance_status']}")

    if result['compliance_status'] == 'FAIL':
        print("\n⚠️  CRITICAL ISSUES DETECTED!")
        critical_flags = [
            f for f in result['compliance_flags']
            if f['severity'] == 'CRITICAL'
        ]
        for flag in critical_flags:
            print(f"\n  {flag['check_id']}: {flag['description']}")
            print(f"  Reason: {flag['justification']}")

    elif result['compliance_status'] == 'WARNING':
        print("\n⚠️  Warnings found (non-critical):")
        for flag in result['compliance_flags']:
            print(f"  - {flag['description']}")


# ============================================================================
# EXAMPLE 3: Processing Multiple Contracts
# ============================================================================

def example_3_batch_processing():
    """Process multiple contracts efficiently."""
    print("\n" + "=" * 80)
    print("EXAMPLE 3: Batch Processing")
    print("=" * 80)

    contracts = {
        "Contract A": "REAL ESTATE PURCHASE AGREEMENT\nProperty: 123 Main St\nBuyer: John Doe\nSeller: Jane Smith\nPrice: $500,000\nClosing: 2026-01-15",
        "Contract B": "REAL ESTATE PURCHASE AGREEMENT\nProperty: 456 Oak Ave\nBuyer: Alice Brown\nSeller: Bob Wilson\nPrice: $600,000\nClosing: 2020-01-01",  # Past date!
        "Contract C": "REAL ESTATE PURCHASE AGREEMENT\nProperty: 789 Elm St\nPrice: $700,000\nClosing: 2026-02-01"  # Missing buyer/seller!
    }

    results = {}

    for name, text in contracts.items():
        print(f"\nProcessing {name}...")
        result = process_contract_text(text)
        results[name] = result

        # Quick summary
        status_emoji = {
            'PASS': '✅',
            'WARNING': '⚠️',
            'FAIL': '❌'
        }
        emoji = status_emoji.get(result['compliance_status'], '❓')
        print(f"  {emoji} Status: {result['compliance_status']}")
        print(f"  Flags: {len(result['compliance_flags'])}")

    # Summary
    print("\n" + "-" * 80)
    print("BATCH SUMMARY:")
    pass_count = sum(1 for r in results.values() if r['compliance_status'] == 'PASS')
    warn_count = sum(1 for r in results.values() if r['compliance_status'] == 'WARNING')
    fail_count = sum(1 for r in results.values() if r['compliance_status'] == 'FAIL')

    print(f"  Passed: {pass_count}")
    print(f"  Warnings: {warn_count}")
    print(f"  Failed: {fail_count}")


# ============================================================================
# EXAMPLE 4: Error Handling
# ============================================================================

def example_4_error_handling():
    """Demonstrate proper error handling."""
    print("\n" + "=" * 80)
    print("EXAMPLE 4: Error Handling")
    print("=" * 80)

    # Try processing with empty text
    empty_text = ""

    print("\nProcessing empty contract...")
    result = process_contract_text(empty_text)

    if result.get('error'):
        print(f"❌ Error occurred:")
        print(f"  Type: {result['error_type']}")
        print(f"  Message: {result['error_message']}")
        print(f"  Timestamp: {result['timestamp']}")
    else:
        # Even with empty text, agent should return valid structure
        print(f"Status: {result['compliance_status']}")
        print(f"Flags: {len(result['compliance_flags'])}")


# ============================================================================
# EXAMPLE 5: Detailed Flag Analysis
# ============================================================================

def example_5_flag_analysis():
    """Analyze compliance flags in detail."""
    print("\n" + "=" * 80)
    print("EXAMPLE 5: Detailed Flag Analysis")
    print("=" * 80)

    # Contract with multiple issues
    problematic_contract = """
    REAL ESTATE PURCHASE AGREEMENT

    Property Address: 999 Problem Lane, Test City, ST 12345

    Purchase Price: $800,000
    Earnest Money Deposit: $50,000 (6.25% - way too high!)

    Closing Date: 2020-01-01 (Past date!)

    Key Dates:
    - Financing Contingency: December 10, 2025
    - Inspection Deadline: December 20, 2025 (After financing - wrong order!)
    - Appraisal Contingency: 2020-05-01 (After closing!)
    """

    result = process_contract_text(problematic_contract)

    print(f"\nCompliance Status: {result['compliance_status']}")
    print(f"Total Flags: {len(result['compliance_flags'])}")

    # Group by severity
    critical = [f for f in result['compliance_flags'] if f['severity'] == 'CRITICAL']
    warnings = [f for f in result['compliance_flags'] if f['severity'] == 'WARNING']

    print(f"\n🔴 CRITICAL ISSUES ({len(critical)}):")
    for i, flag in enumerate(critical, 1):
        print(f"\n  {i}. {flag['check_id']}: {flag['description']}")
        print(f"     Justification: {flag['justification']}")

    print(f"\n🟡 WARNINGS ({len(warnings)}):")
    for i, flag in enumerate(warnings, 1):
        print(f"\n  {i}. {flag['check_id']}: {flag['description']}")
        print(f"     Justification: {flag['justification']}")


# ============================================================================
# EXAMPLE 6: Exporting Results
# ============================================================================

def example_6_export_results():
    """Export results to JSON file."""
    print("\n" + "=" * 80)
    print("EXAMPLE 6: Exporting Results")
    print("=" * 80)

    contract_text = """
    REAL ESTATE PURCHASE AGREEMENT
    Property: 555 Export St, Data City, DC 20001
    Buyer: Test Buyer
    Seller: Test Seller
    Price: $450,000
    Earnest Money: $9,000
    Closing: 2026-03-15
    """

    result = process_contract_text(contract_text)

    # Export to JSON
    output_file = Path('/tmp/contract_result.json')
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)

    print(f"\n✅ Results exported to: {output_file}")
    print(f"   File size: {output_file.stat().st_size} bytes")

    # Also export just the transaction data
    transaction_file = Path('/tmp/transaction_data.json')
    with open(transaction_file, 'w') as f:
        json.dump(result['transaction_data'], f, indent=2)

    print(f"✅ Transaction data exported to: {transaction_file}")


# ============================================================================
# RUN ALL EXAMPLES
# ============================================================================

if __name__ == "__main__":
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "CLAUDE COMPLIANCE AGENT EXAMPLES" + " " * 26 + "║")
    print("╚" + "=" * 78 + "╝")

    # Check for API key
    import os
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("\n❌ ERROR: ANTHROPIC_API_KEY not found in environment!")
        print("   Please set your API key before running examples:")
        print("   export ANTHROPIC_API_KEY=your_key_here")
        sys.exit(1)

    try:
        # Run examples
        example_1_simple_usage()
        # Uncomment to run other examples:
        # example_2_agent_class()
        # example_3_batch_processing()
        # example_4_error_handling()
        # example_5_flag_analysis()
        # example_6_export_results()

        print("\n" + "=" * 80)
        print("✅ Examples completed successfully!")
        print("=" * 80 + "\n")

    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        import traceback
        traceback.print_exc()
