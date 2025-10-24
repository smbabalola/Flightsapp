# Generate Paystack webhook signature for local testing
# Usage:
#   pwsh -File scripts\gen_paystack_sig.ps1 -Secret "test_secret" -Reference "REF_ABC12345"
# Or from PowerShell:
#   .\scripts\gen_paystack_sig.ps1 -Secret "test_secret" -Reference "REF_ABC12345"

param(
  [Parameter(Mandatory=$true)] [string]$Secret,
  [Parameter(Mandatory=$true)] [string]$Reference
)

$body = '{"event":"charge.success","data":{"reference":"' + $Reference + '"}}'
$hmac = New-Object System.Security.Cryptography.HMACSHA512 ([Text.Encoding]::UTF8.GetBytes($Secret))
$hashBytes = $hmac.ComputeHash([Text.Encoding]::UTF8.GetBytes($body))
$sig = -join ($hashBytes | ForEach-Object { $_.ToString('x2') })

Write-Host "Body:" $body
Write-Host "X-Paystack-Signature:" $sig
