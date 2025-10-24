<#
.SYNOPSIS
    Test Paystack webhook with proper HMAC signature verification.

.DESCRIPTION
    This script generates the correct X-Paystack-Signature header and sends a test webhook
    to your local SureFlights API. Useful for testing webhook handling without waiting for
    real payments.

.PARAMETER Reference
    The payment reference to mark as successful (e.g., "REF_64DE5BB6DAA0")

.PARAMETER Amount
    Amount in kobo (minor currency units). E.g., 15000000 = 150,000 NGN

.PARAMETER ApiUrl
    Base URL of your API (default: http://127.0.0.1:8000)

.PARAMETER Secret
    Paystack secret key from your .env file. If not provided, will try to read from .env

.EXAMPLE
    .\test_paystack_webhook.ps1 -Reference "REF_ABC123" -Amount 15000000

.EXAMPLE
    .\test_paystack_webhook.ps1 -Reference "REF_ABC123" -Amount 15000000 -Secret "sk_test_your_key"
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$Reference,

    [Parameter(Mandatory=$true)]
    [int]$Amount,

    [Parameter(Mandatory=$false)]
    [string]$ApiUrl = "http://127.0.0.1:8000",

    [Parameter(Mandatory=$false)]
    [string]$Secret = ""
)

# Try to read secret from .env if not provided
if ([string]::IsNullOrEmpty($Secret)) {
    Write-Host "No secret provided, attempting to read from .env..." -ForegroundColor Yellow
    
    if (Test-Path ".env") {
        $envContent = Get-Content ".env"
        foreach ($line in $envContent) {
            if ($line -match "^PAYSTACK_SECRET=(.+)$") {
                $Secret = $matches[1].Trim()
                Write-Host "Found PAYSTACK_SECRET in .env" -ForegroundColor Green
                break
            }
        }
    }
    
    if ([string]::IsNullOrEmpty($Secret)) {
        Write-Error "Could not find PAYSTACK_SECRET. Provide via -Secret parameter or set in .env file"
        exit 1
    }
}

# Create webhook payload
$payload = @{
    event = "charge.success"
    data = @{
        reference = $Reference
        status = "success"
        amount = $Amount
        currency = "NGN"
        paid_at = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ss.000Z")
        channel = "test"
    }
} | ConvertTo-Json -Compress

Write-Host "`nWebhook Payload:" -ForegroundColor Cyan
Write-Host $payload -ForegroundColor Gray

# Compute HMAC SHA-512 signature
$hmac = New-Object System.Security.Cryptography.HMACSHA512
$hmac.Key = [System.Text.Encoding]::UTF8.GetBytes($Secret)
$hashBytes = $hmac.ComputeHash([System.Text.Encoding]::UTF8.GetBytes($payload))
$signature = [System.BitConverter]::ToString($hashBytes).Replace('-', '').ToLower()

Write-Host "`nComputed Signature:" -ForegroundColor Cyan
Write-Host $signature -ForegroundColor Gray

# Generate random event ID (Paystack format)
$eventId = "evt_test_" + -join ((48..57) + (97..122) | Get-Random -Count 12 | ForEach-Object {[char]$_})

# Send webhook request
$headers = @{
    "Content-Type" = "application/json"
    "X-Paystack-Signature" = $signature
    "X-Paystack-Event-Id" = $eventId
}

$webhookUrl = "$ApiUrl/webhooks/paystack"

Write-Host "`nSending webhook to: $webhookUrl" -ForegroundColor Cyan
Write-Host "Reference: $Reference" -ForegroundColor White
Write-Host "Amount: $Amount kobo" -ForegroundColor White

try {
    $response = Invoke-WebRequest -Uri $webhookUrl -Method POST -Headers $headers -Body $payload -UseBasicParsing
    
    Write-Host "`n✓ Webhook sent successfully!" -ForegroundColor Green
    Write-Host "Status Code: $($response.StatusCode)" -ForegroundColor Green
    Write-Host "Response:" -ForegroundColor Cyan
    Write-Host $response.Content -ForegroundColor Gray
    
} catch {
    Write-Host "`n✗ Webhook failed!" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $responseBody = $reader.ReadToEnd()
        Write-Host "Response Body:" -ForegroundColor Yellow
        Write-Host $responseBody -ForegroundColor Gray
    }
    
    exit 1
}

Write-Host "`nNext steps:" -ForegroundColor Cyan
Write-Host "1. Check trip created: curl http://127.0.0.1:8000/v1/ops/trips?limit=5 -u admin:change_me" -ForegroundColor White
Write-Host "2. Get payment status: curl http://127.0.0.1:8000/v1/payments/$Reference" -ForegroundColor White
