/**
 * n8n Code Node Integration for Claude Compliance Agent
 *
 * This snippet demonstrates how to call the Claude Compliance Agent
 * from within an n8n Code Node.
 *
 * Prerequisites:
 * 1. Python 3.11+ installed on n8n host
 * 2. Required packages installed: anthropic, pydantic, python-dateutil, structlog
 * 3. ANTHROPIC_API_KEY set as environment variable or n8n credential
 * 4. claude_compliance_agent.py accessible to n8n
 *
 * Integration Options:
 * A) Execute Python script directly (shown below)
 * B) Deploy as REST API microservice and call via HTTP Request node
 * C) Use Python code node (if available in your n8n instance)
 */

// ============================================================================
// OPTION A: Execute Python Script Directly
// ============================================================================

/**
 * Execute the Claude Compliance Agent Python script
 *
 * Input: Contract text from previous node
 * Output: Compliance result JSON
 */
const { exec } = require('child_process');
const util = require('util');
const execPromise = util.promisify(exec);

// Get contract text from previous node
const contractText = $input.item.json.contract_text;

// Path to your Python script (adjust as needed)
const pythonScriptPath = '/path/to/src/claude_compliance_agent.py';

// Get API key from n8n credentials or environment
const apiKey = $credentials.anthropicApi.apiKey || process.env.ANTHROPIC_API_KEY;

// Create temporary file with contract text
const fs = require('fs');
const path = require('path');
const tmpDir = '/tmp';
const contractFile = path.join(tmpDir, `contract_${Date.now()}.txt`);
fs.writeFileSync(contractFile, contractText);

try {
  // Execute Python script
  const pythonCommand = `
    export ANTHROPIC_API_KEY="${apiKey}"
    cat "${contractFile}" | python3 "${pythonScriptPath}"
  `;

  const { stdout, stderr } = await execPromise(pythonCommand);

  // Clean up temp file
  fs.unlinkSync(contractFile);

  if (stderr && !stderr.includes('INFO')) {
    throw new Error(`Python script error: ${stderr}`);
  }

  // Parse result
  const result = JSON.parse(stdout);

  // Return result for next node
  return {
    json: {
      ...result,
      processing_timestamp: new Date().toISOString(),
      n8n_execution_id: $execution.id
    }
  };

} catch (error) {
  // Clean up temp file on error
  if (fs.existsSync(contractFile)) {
    fs.unlinkSync(contractFile);
  }

  // Return structured error
  return {
    json: {
      error: true,
      error_type: 'N8N_EXECUTION_ERROR',
      error_message: error.message,
      timestamp: new Date().toISOString()
    }
  };
}


// ============================================================================
// OPTION B: Call REST API Microservice
// ============================================================================

/**
 * If you deploy the Claude Compliance Agent as a REST API,
 * use an HTTP Request node instead with this configuration:
 *
 * Method: POST
 * URL: http://your-service-host:8000/api/v1/process-contract
 * Headers:
 *   - Content-Type: application/json
 *   - X-API-Key: {{ $credentials.claudeAgentApi.apiKey }}
 * Body (JSON):
 * {
 *   "contract_text": "{{ $json.contract_text }}"
 * }
 */


// ============================================================================
// OPTION C: Inline Python Execution (If n8n supports Python Code Node)
// ============================================================================

/**
 * If your n8n instance has a Python Code Node, you can embed the logic:
 */

/*
# Python Code Node

import json
import os
from claude_compliance_agent import process_contract_text

# Get input from previous node
contract_text = items[0]['json']['contract_text']

# Get API key from environment
api_key = os.getenv('ANTHROPIC_API_KEY')

# Process contract
result = process_contract_text(contract_text, api_key)

# Return result
return [{
    'json': {
        **result,
        'processing_timestamp': datetime.utcnow().isoformat()
    }
}]
*/


// ============================================================================
// ERROR HANDLING & RETRY LOGIC
// ============================================================================

/**
 * Recommended error handling for production:
 */

const MAX_RETRIES = 3;
const RETRY_DELAY_MS = 2000;

async function processContractWithRetry(contractText, apiKey, retries = 0) {
  try {
    // Your processing logic here
    const result = await processContract(contractText, apiKey);
    return result;

  } catch (error) {
    // Check if error is retryable (API timeout, rate limit, etc.)
    const isRetryable =
      error.message.includes('timeout') ||
      error.message.includes('rate_limit') ||
      error.message.includes('503');

    if (isRetryable && retries < MAX_RETRIES) {
      // Wait and retry
      await new Promise(resolve => setTimeout(resolve, RETRY_DELAY_MS * (retries + 1)));
      return processContractWithRetry(contractText, apiKey, retries + 1);
    }

    // Non-retryable error or max retries reached
    throw error;
  }
}


// ============================================================================
// RESPONSE HANDLING FOR DOWNSTREAM NODES
// ============================================================================

/**
 * Structure the output for downstream n8n nodes:
 */

// After successful processing:
const complianceResult = JSON.parse(stdout);

// Create structured output for different downstream paths
return [
  // Output 1: Success path (for database insert)
  {
    json: {
      transaction_id: $input.item.json.transaction_id,
      ...complianceResult.transaction_data,
      compliance_status: complianceResult.compliance_status,
      compliance_flags: complianceResult.compliance_flags,
      processed_at: new Date().toISOString()
    }
  },

  // Output 2: Notification path (if flags exist)
  complianceResult.compliance_flags.length > 0 ? {
    json: {
      notification_type: complianceResult.compliance_status,
      property_address: complianceResult.transaction_data.property_address,
      flag_count: complianceResult.compliance_flags.length,
      critical_flags: complianceResult.compliance_flags.filter(f => f.severity === 'CRITICAL'),
      warning_flags: complianceResult.compliance_flags.filter(f => f.severity === 'WARNING')
    }
  } : null
].filter(Boolean);


// ============================================================================
// MONITORING & LOGGING
// ============================================================================

/**
 * Add monitoring metadata for tracking:
 */

const enrichedResult = {
  ...complianceResult,
  metadata: {
    n8n_workflow_id: $workflow.id,
    n8n_execution_id: $execution.id,
    processing_timestamp: new Date().toISOString(),
    contract_length: contractText.length,
    api_model: 'claude-3-opus-20240229'
  }
};

return { json: enrichedResult };
