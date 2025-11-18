"""
Executive Dashboard API - FastAPI Backend
Serves contract compliance data for the executive dashboard
"""

import json
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


# ============================================================================
# DATA MODELS
# ============================================================================

class ComplianceFlag(BaseModel):
    check_id: str
    severity: str
    description: str
    justification: str


class TransactionData(BaseModel):
    property_address: Optional[str] = None
    buyer_name: Optional[str] = None
    seller_name: Optional[str] = None
    purchase_price: Optional[float] = None
    earnest_money_amount: Optional[float] = None
    closing_date: Optional[str] = None
    inspection_deadline: Optional[str] = None
    financing_contingency_date: Optional[str] = None
    appraisal_contingency_date: Optional[str] = None
    title_contingency_date: Optional[str] = None
    listing_agent_name: Optional[str] = None
    buyer_agent_name: Optional[str] = None
    escrow_company: Optional[str] = None
    title_company: Optional[str] = None
    extraction_confidence_score: float = 0.95


class ContractResult(BaseModel):
    id: str
    processed_at: str
    transaction_data: TransactionData
    compliance_status: str
    compliance_flags: List[ComplianceFlag]
    processing_time_ms: int


class DashboardStats(BaseModel):
    total_contracts: int
    pass_count: int
    warning_count: int
    fail_count: int
    pass_rate: float
    avg_processing_time_ms: int
    total_transaction_value: float
    critical_flags_count: int
    warning_flags_count: int


# ============================================================================
# MOCK DATA SERVICE
# ============================================================================

class MockDataService:
    """Service to generate realistic mock contract data from test cases."""

    def __init__(self):
        self.contracts: List[ContractResult] = []
        self._load_test_cases()

    def _load_test_cases(self):
        """Load test cases and convert to processed contract results."""
        # Check Docker mount location first, then development path
        docker_path = Path("/app/test_cases.json")
        dev_path = Path(__file__).parent.parent.parent / "tests" / "test_cases.json"

        if docker_path.exists():
            test_cases_path = docker_path
        elif dev_path.exists():
            test_cases_path = dev_path
        else:
            print(f"Warning: test_cases.json not found at {docker_path} or {dev_path}")
            self._generate_fallback_data()
            return

        with open(test_cases_path) as f:
            data = json.load(f)

        # Convert test cases to contract results
        base_time = datetime.now() - timedelta(days=30)

        for i, test_case in enumerate(data.get('test_cases', [])):
            # Parse transaction data from contract text
            transaction_data = self._parse_contract_text(test_case['contract_text'])

            # Create compliance flags from expected flags
            flags = []
            for expected_flag in test_case.get('expected_flags', []):
                flags.append(ComplianceFlag(
                    check_id=expected_flag['check_id'],
                    severity=expected_flag['severity'],
                    description=expected_flag['description'],
                    justification=f"Automated compliance check identified: {expected_flag['description']}"
                ))

            # Create contract result
            contract = ContractResult(
                id=f"CNT-2025-{1000 + i}",
                processed_at=(base_time + timedelta(days=i * 3, hours=random.randint(8, 17))).isoformat(),
                transaction_data=transaction_data,
                compliance_status=test_case['expected_status'],
                compliance_flags=flags,
                processing_time_ms=random.randint(15000, 42000)
            )

            self.contracts.append(contract)

        # Sort by processed_at descending (most recent first)
        self.contracts.sort(key=lambda x: x.processed_at, reverse=True)

        print(f"Loaded {len(self.contracts)} mock contracts")

    def _parse_contract_text(self, text: str) -> TransactionData:
        """Parse contract text to extract transaction data."""
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
            'extraction_confidence_score': random.uniform(0.88, 0.99)
        }

        lines = text.split('\n')
        for line in lines:
            line = line.strip()

            if line.startswith('Property Address:'):
                data['property_address'] = line.split(':', 1)[1].strip()
            elif line.startswith('Buyer:'):
                data['buyer_name'] = line.split(':', 1)[1].strip()
            elif line.startswith('Seller:'):
                data['seller_name'] = line.split(':', 1)[1].strip()
            elif line.startswith('Purchase Price:'):
                price_str = line.split(':', 1)[1].strip().replace('$', '').replace(',', '').split()[0]
                try:
                    data['purchase_price'] = float(price_str)
                except:
                    pass
            elif 'Earnest Money' in line and ':' in line:
                amount_str = line.split(':', 1)[1].strip().replace('$', '').replace(',', '').split()[0]
                try:
                    data['earnest_money_amount'] = float(amount_str)
                except:
                    pass
            elif 'Closing Date:' in line:
                date_str = line.split('Closing Date:', 1)[1].strip().split()[0]
                data['closing_date'] = date_str
            elif 'Inspection Deadline:' in line:
                date_str = line.split('Deadline:', 1)[1].strip().split()[0]
                data['inspection_deadline'] = date_str
            elif 'Financing Contingency:' in line:
                date_str = line.split('Contingency:', 1)[1].strip().split()[0]
                data['financing_contingency_date'] = date_str
            elif 'Appraisal Contingency:' in line:
                date_str = line.split('Contingency:', 1)[1].strip().split()[0]
                data['appraisal_contingency_date'] = date_str
            elif 'Listing Agent:' in line:
                data['listing_agent_name'] = line.split('Agent:', 1)[1].strip()
            elif "Buyer's Agent:" in line or 'Buyer Agent:' in line:
                data['buyer_agent_name'] = line.split('Agent:', 1)[1].strip()
            elif line.startswith('Escrow Company:'):
                data['escrow_company'] = line.split(':', 1)[1].strip()
            elif line.startswith('Title Company:'):
                data['title_company'] = line.split(':', 1)[1].strip()

        return TransactionData(**data)

    def _generate_fallback_data(self):
        """Generate fallback data if test cases not available."""
        print("Generating fallback mock data...")

        statuses = ['PASS', 'WARNING', 'FAIL']
        base_time = datetime.now() - timedelta(days=30)

        for i in range(10):
            status = random.choice(statuses)
            flags = []

            if status == 'FAIL':
                flags.append(ComplianceFlag(
                    check_id="CC-001",
                    severity="CRITICAL",
                    description="Required fields missing",
                    justification="Missing buyer or seller information"
                ))
            elif status == 'WARNING':
                flags.append(ComplianceFlag(
                    check_id="CC-002",
                    severity="WARNING",
                    description="Earnest money outside typical range",
                    justification="Earnest money is below 1% of purchase price"
                ))

            contract = ContractResult(
                id=f"CNT-2025-{1000 + i}",
                processed_at=(base_time + timedelta(days=i * 3)).isoformat(),
                transaction_data=TransactionData(
                    property_address=f"{100 + i} Sample St, Test City, ST 12345",
                    buyer_name="Sample Buyer",
                    seller_name="Sample Seller",
                    purchase_price=float(random.randint(300000, 800000)),
                    earnest_money_amount=float(random.randint(5000, 20000)),
                    closing_date="2026-01-15",
                    extraction_confidence_score=random.uniform(0.90, 0.99)
                ),
                compliance_status=status,
                compliance_flags=flags,
                processing_time_ms=random.randint(15000, 42000)
            )

            self.contracts.append(contract)

    def get_all_contracts(self) -> List[ContractResult]:
        """Get all contracts."""
        return self.contracts

    def get_contract_by_id(self, contract_id: str) -> Optional[ContractResult]:
        """Get specific contract by ID."""
        for contract in self.contracts:
            if contract.id == contract_id:
                return contract
        return None

    def get_dashboard_stats(self) -> DashboardStats:
        """Calculate dashboard statistics."""
        total = len(self.contracts)
        pass_count = sum(1 for c in self.contracts if c.compliance_status == 'PASS')
        warning_count = sum(1 for c in self.contracts if c.compliance_status == 'WARNING')
        fail_count = sum(1 for c in self.contracts if c.compliance_status == 'FAIL')

        pass_rate = (pass_count / total * 100) if total > 0 else 0

        avg_processing_time = sum(c.processing_time_ms for c in self.contracts) // total if total > 0 else 0

        total_value = sum(
            c.transaction_data.purchase_price or 0
            for c in self.contracts
        )

        critical_flags = sum(
            sum(1 for flag in c.compliance_flags if flag.severity == 'CRITICAL')
            for c in self.contracts
        )

        warning_flags = sum(
            sum(1 for flag in c.compliance_flags if flag.severity == 'WARNING')
            for c in self.contracts
        )

        return DashboardStats(
            total_contracts=total,
            pass_count=pass_count,
            warning_count=warning_count,
            fail_count=fail_count,
            pass_rate=round(pass_rate, 1),
            avg_processing_time_ms=avg_processing_time,
            total_transaction_value=total_value,
            critical_flags_count=critical_flags,
            warning_flags_count=warning_flags
        )


# ============================================================================
# FASTAPI APP
# ============================================================================

app = FastAPI(
    title="Contract Compliance Dashboard API",
    description="Executive dashboard backend for contract compliance monitoring",
    version="1.0.0"
)

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Vite default ports
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize mock data service
data_service = MockDataService()


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/")
def read_root():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Contract Compliance Dashboard API",
        "version": "1.0.0"
    }


@app.get("/api/stats", response_model=DashboardStats)
def get_stats():
    """Get dashboard statistics."""
    return data_service.get_dashboard_stats()


@app.get("/api/contracts", response_model=List[ContractResult])
def get_contracts(limit: int = 100, status: Optional[str] = None):
    """
    Get all contracts with optional filtering.

    Args:
        limit: Maximum number of contracts to return
        status: Filter by compliance status (PASS, WARNING, FAIL)
    """
    contracts = data_service.get_all_contracts()

    if status:
        contracts = [c for c in contracts if c.compliance_status == status.upper()]

    return contracts[:limit]


@app.get("/api/contracts/{contract_id}", response_model=ContractResult)
def get_contract(contract_id: str):
    """Get specific contract by ID."""
    contract = data_service.get_contract_by_id(contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    return contract


@app.get("/api/recent", response_model=List[ContractResult])
def get_recent_contracts(limit: int = 5):
    """Get most recent contracts."""
    return data_service.get_all_contracts()[:limit]


# ============================================================================
# RUN SERVER
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Contract Compliance Dashboard API...")
    print("📊 Dashboard API available at: http://localhost:8000")
    print("📖 API docs available at: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
