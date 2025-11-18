"""
Supabase Service for Contract Compliance Dashboard
Handles all database operations for storing and retrieving contract data.
"""
import os
from typing import List, Optional, Dict, Any
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class SupabaseService:
    """Service for interacting with Supabase database."""

    def __init__(self):
        """Initialize Supabase client."""
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")

        if not url or not key:
            raise ValueError(
                "Missing Supabase credentials. "
                "Please set SUPABASE_URL and SUPABASE_KEY environment variables."
            )

        self.client: Client = create_client(url, key)

    def insert_contract(self, contract_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Insert a new contract with its compliance flags.

        Args:
            contract_data: Dictionary containing contract and compliance data

        Returns:
            The inserted contract data
        """
        # Extract compliance flags
        compliance_flags = contract_data.pop("compliance_flags", [])
        transaction_data = contract_data.pop("transaction_data", {})

        # Prepare contract record
        contract_record = {
            "id": contract_data["id"],
            "processed_at": contract_data.get("processed_at", datetime.utcnow().isoformat()),
            "compliance_status": contract_data["compliance_status"],
            "processing_time_ms": contract_data["processing_time_ms"],
            # Transaction data fields
            "property_address": transaction_data.get("property_address"),
            "buyer_name": transaction_data.get("buyer_name"),
            "seller_name": transaction_data.get("seller_name"),
            "purchase_price": transaction_data.get("purchase_price"),
            "earnest_money_amount": transaction_data.get("earnest_money_amount"),
            "closing_date": transaction_data.get("closing_date"),
            "inspection_deadline": transaction_data.get("inspection_deadline"),
            "financing_contingency_date": transaction_data.get("financing_contingency_date"),
            "appraisal_contingency_date": transaction_data.get("appraisal_contingency_date"),
            "title_contingency_date": transaction_data.get("title_contingency_date"),
            "listing_agent_name": transaction_data.get("listing_agent_name"),
            "buyer_agent_name": transaction_data.get("buyer_agent_name"),
            "escrow_company": transaction_data.get("escrow_company"),
            "title_company": transaction_data.get("title_company"),
            "extraction_confidence_score": transaction_data.get("extraction_confidence_score", 0.0),
        }

        # Insert contract
        result = self.client.table("contracts").insert(contract_record).execute()

        # Insert compliance flags
        if compliance_flags:
            flags_to_insert = [
                {
                    "contract_id": contract_data["id"],
                    "check_id": flag["check_id"],
                    "severity": flag["severity"],
                    "description": flag["description"],
                    "justification": flag["justification"],
                }
                for flag in compliance_flags
            ]
            self.client.table("compliance_flags").insert(flags_to_insert).execute()

        return result.data[0] if result.data else {}

    def get_all_contracts(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get all contracts with their compliance flags.

        Args:
            limit: Maximum number of contracts to return

        Returns:
            List of contract dictionaries
        """
        # Fetch contracts
        contracts_response = self.client.table("contracts") \
            .select("*") \
            .order("processed_at", desc=True) \
            .limit(limit) \
            .execute()

        contracts = []
        for contract in contracts_response.data:
            # Fetch compliance flags for this contract
            flags_response = self.client.table("compliance_flags") \
                .select("*") \
                .eq("contract_id", contract["id"]) \
                .execute()

            # Restructure to match expected format
            contract_result = {
                "id": contract["id"],
                "processed_at": contract["processed_at"],
                "transaction_data": {
                    "property_address": contract.get("property_address"),
                    "buyer_name": contract.get("buyer_name"),
                    "seller_name": contract.get("seller_name"),
                    "purchase_price": float(contract["purchase_price"]) if contract.get("purchase_price") else None,
                    "earnest_money_amount": float(contract["earnest_money_amount"]) if contract.get("earnest_money_amount") else None,
                    "closing_date": contract.get("closing_date"),
                    "extraction_confidence_score": float(contract.get("extraction_confidence_score", 0.0)),
                },
                "compliance_status": contract["compliance_status"],
                "compliance_flags": [
                    {
                        "check_id": flag["check_id"],
                        "severity": flag["severity"],
                        "description": flag["description"],
                        "justification": flag["justification"],
                    }
                    for flag in flags_response.data
                ],
                "processing_time_ms": contract["processing_time_ms"],
            }
            contracts.append(contract_result)

        return contracts

    def get_contract_by_id(self, contract_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific contract by ID.

        Args:
            contract_id: The contract ID

        Returns:
            Contract dictionary or None if not found
        """
        response = self.client.table("contracts") \
            .select("*") \
            .eq("id", contract_id) \
            .execute()

        if not response.data:
            return None

        contract = response.data[0]

        # Fetch compliance flags
        flags_response = self.client.table("compliance_flags") \
            .select("*") \
            .eq("contract_id", contract_id) \
            .execute()

        return {
            "id": contract["id"],
            "processed_at": contract["processed_at"],
            "transaction_data": {
                "property_address": contract.get("property_address"),
                "buyer_name": contract.get("buyer_name"),
                "seller_name": contract.get("seller_name"),
                "purchase_price": float(contract["purchase_price"]) if contract.get("purchase_price") else None,
                "earnest_money_amount": float(contract["earnest_money_amount"]) if contract.get("earnest_money_amount") else None,
                "closing_date": contract.get("closing_date"),
                "extraction_confidence_score": float(contract.get("extraction_confidence_score", 0.0)),
            },
            "compliance_status": contract["compliance_status"],
            "compliance_flags": [
                {
                    "check_id": flag["check_id"],
                    "severity": flag["severity"],
                    "description": flag["description"],
                    "justification": flag["justification"],
                }
                for flag in flags_response.data
            ],
            "processing_time_ms": contract["processing_time_ms"],
        }

    def get_dashboard_stats(self) -> Dict[str, Any]:
        """
        Calculate dashboard statistics from database.

        Returns:
            Dictionary containing dashboard stats
        """
        # Get all contracts for stats calculation
        contracts = self.get_all_contracts(limit=1000)

        total = len(contracts)
        if total == 0:
            return {
                "total_contracts": 0,
                "pass_count": 0,
                "warning_count": 0,
                "fail_count": 0,
                "pass_rate": 0,
                "avg_processing_time_ms": 0,
                "total_transaction_value": 0,
                "critical_flags_count": 0,
                "warning_flags_count": 0,
            }

        pass_count = sum(1 for c in contracts if c["compliance_status"] == "PASS")
        warning_count = sum(1 for c in contracts if c["compliance_status"] == "WARNING")
        fail_count = sum(1 for c in contracts if c["compliance_status"] == "FAIL")

        pass_rate = round((pass_count / total * 100), 1) if total > 0 else 0

        avg_processing_time = sum(c["processing_time_ms"] for c in contracts) // total if total > 0 else 0

        total_value = sum(
            c["transaction_data"].get("purchase_price", 0) or 0
            for c in contracts
        )

        critical_flags = sum(
            len([f for f in c["compliance_flags"] if f["severity"] == "CRITICAL"])
            for c in contracts
        )

        warning_flags = sum(
            len([f for f in c["compliance_flags"] if f["severity"] == "WARNING"])
            for c in contracts
        )

        return {
            "total_contracts": total,
            "pass_count": pass_count,
            "warning_count": warning_count,
            "fail_count": fail_count,
            "pass_rate": pass_rate,
            "avg_processing_time_ms": avg_processing_time,
            "total_transaction_value": total_value,
            "critical_flags_count": critical_flags,
            "warning_flags_count": warning_flags,
        }
