# Supabase Integration Setup Guide

This guide will help you connect your dashboard to Supabase database.

## Step 1: Get Your Supabase Credentials

1. Go to your Supabase project dashboard
2. Click on **Settings** (gear icon) in the sidebar
3. Click on **API** tab
4. Copy the following:
   - **Project URL** (looks like: `https://xxxxx.supabase.co`)
   - **anon/public key** (starts with `eyJ...`)

## Step 2: Create Database Tables

1. In your Supabase dashboard, go to **SQL Editor**
2. Click **New Query**
3. Copy and paste the entire contents of `backend/supabase_schema.sql`
4. Click **Run** to create the tables

This will create:
- `contracts` table - stores all contract data
- `compliance_flags` table - stores compliance issues
- Indexes for performance
- Row Level Security policies

## Step 3: Configure Environment Variables

### For Local Development:

Create a `.env` file in the `dashboard/backend/` directory:

```bash
cd dashboard/backend
cp .env.example .env
```

Then edit `.env` and add your credentials:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_anon_key_here
```

### For Docker:

The same `.env` file will be used by Docker automatically via `docker-compose.yml`.

## Step 4: Install Dependencies

The Supabase client library will be installed automatically when you rebuild:

```bash
docker-compose down
docker-compose up --build
```

## Step 5: Verify Connection

When you start the backend, you should see:

```
🗄️  Connecting to Supabase database...
✅ Connected to Supabase successfully!
```

If it fails, you'll see:

```
⚠️  Failed to connect to Supabase: [error message]
📦 Falling back to mock data service...
```

## Step 6: Add Sample Data (Optional)

You can insert sample contracts using the API:

```bash
curl -X POST http://localhost:8000/api/contracts \
  -H "Content-Type: application/json" \
  -d '{
    "id": "CNT-2025-0001",
    "transaction_data": {
      "property_address": "123 Main St, City, ST 12345",
      "buyer_name": "John Doe",
      "seller_name": "Jane Smith",
      "purchase_price": 500000,
      "earnest_money_amount": 10000,
      "closing_date": "2025-06-15",
      "extraction_confidence_score": 0.95
    },
    "compliance_status": "PASS",
    "compliance_flags": [],
    "processing_time_ms": 25000
  }'
```

## Troubleshooting

### "Missing Supabase credentials" Error
- Make sure your `.env` file exists in `dashboard/backend/`
- Verify the credentials are correct (no extra spaces)
- Rebuild the Docker containers: `docker-compose up --build`

### Connection Timeout
- Check your Supabase project is active (not paused)
- Verify your network can reach Supabase
- Check if you need to add your IP to allowed list in Supabase settings

### Permission Errors
- Verify Row Level Security policies are created
- Check the SQL ran successfully without errors

## What Happens

- **With Supabase configured**: Dashboard reads/writes from your Supabase database
- **Without Supabase**: Dashboard falls back to mock data from `test_cases.json`

This allows you to develop locally with mock data and deploy with real database seamlessly!

## Next Steps

Once Supabase is connected:
1. Build your n8n workflow to process contracts
2. Have n8n POST contract results to `/api/contracts` endpoint
3. View real-time data in your dashboard at http://localhost:3000
