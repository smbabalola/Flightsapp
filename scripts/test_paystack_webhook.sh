#!/bin/bash
# Test Paystack webhook with proper HMAC signature verification

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
GRAY='\033[0;90m'
NC='\033[0m' # No Color

# Default values
API_URL="${API_URL:-http://127.0.0.1:8000}"
SECRET=""
REFERENCE=""
AMOUNT=""

# Show usage
usage() {
    echo "Usage: $0 -r REFERENCE -a AMOUNT [-s SECRET] [-u API_URL]"
    echo ""
    echo "Options:"
    echo "  -r    Payment reference (e.g., REF_ABC123)"
    echo "  -a    Amount in kobo (e.g., 15000000 for 150,000 NGN)"
    echo "  -s    Paystack secret key (optional, reads from .env if not provided)"
    echo "  -u    API URL (default: http://127.0.0.1:8000)"
    echo ""
    echo "Example:"
    echo "  $0 -r REF_ABC123 -a 15000000"
    exit 1
}

# Parse arguments
while getopts "r:a:s:u:h" opt; do
    case $opt in
        r) REFERENCE="$OPTARG" ;;
        a) AMOUNT="$OPTARG" ;;
        s) SECRET="$OPTARG" ;;
        u) API_URL="$OPTARG" ;;
        h) usage ;;
        *) usage ;;
    esac
done

# Validate required arguments
if [ -z "$REFERENCE" ] || [ -z "$AMOUNT" ]; then
    echo -e "${RED}Error: Reference and Amount are required${NC}"
    usage
fi

# Try to read secret from .env if not provided
if [ -z "$SECRET" ]; then
    echo -e "${YELLOW}No secret provided, attempting to read from .env...${NC}"
    
    if [ -f ".env" ]; then
        SECRET=$(grep "^PAYSTACK_SECRET=" .env | cut -d '=' -f2 | tr -d ' "' || echo "")
        if [ -n "$SECRET" ]; then
            echo -e "${GREEN}Found PAYSTACK_SECRET in .env${NC}"
        fi
    fi
    
    if [ -z "$SECRET" ]; then
        echo -e "${RED}Error: Could not find PAYSTACK_SECRET${NC}"
        echo "Provide via -s parameter or set in .env file"
        exit 1
    fi
fi

# Create webhook payload
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%S.000Z")
PAYLOAD=$(cat <<JSON
{"event":"charge.success","data":{"reference":"$REFERENCE","status":"success","amount":$AMOUNT,"currency":"NGN","paid_at":"$TIMESTAMP","channel":"test"}}
JSON
)

echo -e "\n${CYAN}Webhook Payload:${NC}"
echo -e "${GRAY}$PAYLOAD${NC}"

# Compute HMAC SHA-512 signature
SIGNATURE=$(echo -n "$PAYLOAD" | openssl dgst -sha512 -hmac "$SECRET" | cut -d ' ' -f2)

echo -e "\n${CYAN}Computed Signature:${NC}"
echo -e "${GRAY}$SIGNATURE${NC}"

# Generate random event ID
EVENT_ID="evt_test_$(openssl rand -hex 6)"

# Webhook URL
WEBHOOK_URL="$API_URL/webhooks/paystack"

echo -e "\n${CYAN}Sending webhook to:${NC} $WEBHOOK_URL"
echo -e "Reference: $REFERENCE"
echo -e "Amount: $AMOUNT kobo"

# Send webhook request
HTTP_CODE=$(curl -s -w "%{http_code}" -o /tmp/webhook_response.txt \
    -X POST "$WEBHOOK_URL" \
    -H "Content-Type: application/json" \
    -H "X-Paystack-Signature: $SIGNATURE" \
    -H "X-Paystack-Event-Id: $EVENT_ID" \
    -d "$PAYLOAD")

# Check response
if [ "$HTTP_CODE" -eq 200 ]; then
    echo -e "\n${GREEN}✓ Webhook sent successfully!${NC}"
    echo -e "${GREEN}Status Code: $HTTP_CODE${NC}"
    echo -e "${CYAN}Response:${NC}"
    echo -e "${GRAY}$(cat /tmp/webhook_response.txt)${NC}"
    
    echo -e "\n${CYAN}Next steps:${NC}"
    echo -e "1. Check trip created: curl $API_URL/v1/ops/trips?limit=5 -u admin:change_me"
    echo -e "2. Get payment status: curl $API_URL/v1/payments/$REFERENCE"
else
    echo -e "\n${RED}✗ Webhook failed!${NC}"
    echo -e "${RED}Status Code: $HTTP_CODE${NC}"
    echo -e "${YELLOW}Response:${NC}"
    echo -e "${GRAY}$(cat /tmp/webhook_response.txt)${NC}"
    exit 1
fi

# Cleanup
rm -f /tmp/webhook_response.txt
