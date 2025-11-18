-- Contract Compliance Dashboard - Supabase Schema
-- Run this in your Supabase SQL Editor

-- Create contracts table
CREATE TABLE IF NOT EXISTS contracts (
    id TEXT PRIMARY KEY,
    processed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Transaction Data
    property_address TEXT,
    buyer_name TEXT,
    seller_name TEXT,
    purchase_price DECIMAL(12, 2),
    earnest_money_amount DECIMAL(12, 2),
    closing_date DATE,
    inspection_deadline DATE,
    financing_contingency_date DATE,
    appraisal_contingency_date DATE,
    title_contingency_date DATE,
    listing_agent_name TEXT,
    buyer_agent_name TEXT,
    escrow_company TEXT,
    title_company TEXT,
    extraction_confidence_score DECIMAL(3, 2),

    -- Compliance Status
    compliance_status TEXT NOT NULL CHECK (compliance_status IN ('PASS', 'WARNING', 'FAIL')),
    processing_time_ms INTEGER NOT NULL,

    -- Metadata
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create compliance_flags table
CREATE TABLE IF NOT EXISTS compliance_flags (
    id SERIAL PRIMARY KEY,
    contract_id TEXT NOT NULL REFERENCES contracts(id) ON DELETE CASCADE,
    check_id TEXT NOT NULL,
    severity TEXT NOT NULL CHECK (severity IN ('CRITICAL', 'WARNING')),
    description TEXT NOT NULL,
    justification TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_contracts_processed_at ON contracts(processed_at DESC);
CREATE INDEX IF NOT EXISTS idx_contracts_status ON contracts(compliance_status);
CREATE INDEX IF NOT EXISTS idx_compliance_flags_contract_id ON compliance_flags(contract_id);
CREATE INDEX IF NOT EXISTS idx_compliance_flags_severity ON compliance_flags(severity);

-- Create updated_at trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_contracts_updated_at BEFORE UPDATE ON contracts
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Enable Row Level Security (RLS)
ALTER TABLE contracts ENABLE ROW LEVEL SECURITY;
ALTER TABLE compliance_flags ENABLE ROW LEVEL SECURITY;

-- Create policies (allow all for now - you can restrict later)
CREATE POLICY "Allow all operations on contracts" ON contracts
    FOR ALL USING (true) WITH CHECK (true);

CREATE POLICY "Allow all operations on compliance_flags" ON compliance_flags
    FOR ALL USING (true) WITH CHECK (true);
