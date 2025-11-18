"""
Supabase Service for Contract Compliance Dashboard
Handles all database operations for storing and retrieving contract data.
Compatible with existing transactions and compliance_flags schema.
"""
import os
import uuid
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
        Insert a new transaction with its compliance flags.

        Args:
            contract_data: Dictionary containing contract and compliance data

        Returns:
            The inserted transaction data
        """
        # Extract compliance flags
        compliance_flags = contract_data.pop("compliance_flags", [])
        transaction_data = contract_data.pop("transaction_data", {})

        # Generate UUID if not provided (or convert existing id to UUID)
        transaction_id = contract_data.get("id", str(uuid.uuid4()))

        # Prepare transaction record (matching actual database schema)
        transaction_record = {
            "transaction_id": transaction_id,
            # Note: created_at and updated_at have defaults, don't need to set them
            "compliance_status": contract_data["compliance_status"],
            # Transaction data fields (all required fields must be present)
            "property_address": transaction_data.get("property_address", "Unknown"),
            "buyer_name": transaction_data.get("buyer_name", "Unknown"),
            "seller_name": transaction_data.get("seller_name", "Unknown"),
            "purchase_price": transaction_data.get("purchase_price", 0),
            "earnest_money_amount": transaction_data.get("earnest_money_amount"),
            "closing_date": transaction_data.get("closing_date", datetime.utcnow().date().isoformat()),
            "inspection_deadline": transaction_data.get("inspection_deadline"),
            "financing_contingency_date": transaction_data.get("financing_contingency_date"),
            "appraisal_contingency_date": transaction_data.get("appraisal_contingency_date"),
            "title_contingency_date": transaction_data.get("title_contingency_date"),
            "listing_agent_name": transaction_data.get("listing_agent_name"),
            "buyer_agent_name": transaction_data.get("buyer_agent_name"),
            "escrow_company": transaction_data.get("escrow_company"),
            "title_company": transaction_data.get("title_company"),
            "extraction_confidence_score": transaction_data.get("extraction_confidence_score", 0.0),
            # Add required tc_status field
            "tc_status": transaction_data.get("tc_status", "PENDING_REVIEW"),
        }

        # Insert transaction
        result = self.client.table("transactions").insert(transaction_record).execute()

        # Insert compliance flags
        if compliance_flags:
            flags_to_insert = [
                {
                    "transaction_id": transaction_id,
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
        Get all transactions with their compliance flags.

        Args:
            limit: Maximum number of transactions to return

        Returns:
            List of contract dictionaries (using 'id' for compatibility with frontend)
        """
        # Fetch transactions (order by created_at, not processed_at)
        transactions_response = self.client.table("transactions") \
            .select("*") \
            .order("created_at", desc=True) \
            .limit(limit) \
            .execute()

        contracts = []
        for transaction in transactions_response.data:
            # Fetch compliance flags for this transaction
            flags_response = self.client.table("compliance_flags") \
                .select("*") \
                .eq("transaction_id", transaction["transaction_id"]) \
                .execute()

            # Restructure to match expected format (map database fields to frontend format)
            contract_result = {
                "id": transaction["transaction_id"],  # Map transaction_id to id for frontend
                "processed_at": transaction["created_at"],  # Map created_at to processed_at for frontend
                "transaction_data": {
                    "property_address": transaction.get("property_address"),
                    "buyer_name": transaction.get("buyer_name"),
                    "seller_name": transaction.get("seller_name"),
                    "purchase_price": float(transaction["purchase_price"]) if transaction.get("purchase_price") else None,
                    "earnest_money_amount": float(transaction["earnest_money_amount"]) if transaction.get("earnest_money_amount") else None,
                    "closing_date": transaction.get("closing_date"),
                    "extraction_confidence_score": float(transaction.get("extraction_confidence_score", 0.0)),
                    "tc_status": transaction.get("tc_status", "PENDING_REVIEW"),
                },
                "compliance_status": transaction["compliance_status"],
                "compliance_flags": [
                    {
                        "check_id": flag["check_id"],
                        "severity": flag["severity"],
                        "description": flag["description"],
                        "justification": flag["justification"],
                    }
                    for flag in flags_response.data
                ],
                "processing_time_ms": 0,  # Not stored in database, default to 0
            }
            contracts.append(contract_result)

        return contracts

    def get_contract_by_id(self, contract_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific transaction by ID.

        Args:
            contract_id: The transaction ID (UUID or string)

        Returns:
            Contract dictionary or None if not found
        """
        response = self.client.table("transactions") \
            .select("*") \
            .eq("transaction_id", contract_id) \
            .execute()

        if not response.data:
            return None

        transaction = response.data[0]

        # Fetch compliance flags
        flags_response = self.client.table("compliance_flags") \
            .select("*") \
            .eq("transaction_id", contract_id) \
            .execute()

        return {
            "id": transaction["transaction_id"],
            "processed_at": transaction["created_at"],  # Map created_at to processed_at
            "transaction_data": {
                "property_address": transaction.get("property_address"),
                "buyer_name": transaction.get("buyer_name"),
                "seller_name": transaction.get("seller_name"),
                "purchase_price": float(transaction["purchase_price"]) if transaction.get("purchase_price") else None,
                "earnest_money_amount": float(transaction["earnest_money_amount"]) if transaction.get("earnest_money_amount") else None,
                "closing_date": transaction.get("closing_date"),
                "extraction_confidence_score": float(transaction.get("extraction_confidence_score", 0.0)),
                "tc_status": transaction.get("tc_status", "PENDING_REVIEW"),
            },
            "compliance_status": transaction["compliance_status"],
            "compliance_flags": [
                {
                    "check_id": flag["check_id"],
                    "severity": flag["severity"],
                    "description": flag["description"],
                    "justification": flag["justification"],
                }
                for flag in flags_response.data
            ],
            "processing_time_ms": 0,  # Not stored in database
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
