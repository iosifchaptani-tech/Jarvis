#Requires -Version 5.1
<#
.SYNOPSIS
  One-click setup of the dropshipping agents on a Windows PC.

.DESCRIPTION
  Installs Docker Desktop and cloudflared if needed, starts n8n 2.41.3 with a public HTTPS
  address, then (through n8n's own API):
    - creates your n8n owner account (or logs in)
    - checks and saves your keys as n8n credentials (typed here, never written to disk)
    - finds your Telegram chat ID
    - creates the 9 Data Tables and loads the starting playbook rules
    - imports the 8 workflows, fills their Settings, attaches the credentials, switches them on
  At the end it prints the few things left to click by hand.

  Safe to run again: anything already done is skipped. Run it again after restarting the PC,
  because the free tunnel gets a new web address each time.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File .\dropshipping\setup.ps1
#>
[CmdletBinding()]
param(
    [string]$N8nUrl = 'http://localhost:5678',
    [string]$PublicUrl = '',          # skip the tunnel and use your own https address
    [switch]$SkipInstall,             # don't install / start Docker, cloudflared or n8n
    [switch]$SkipKeyChecks,           # don't test the keys against Claude, Telegram and CJ
    [switch]$ReplaceWorkflows,        # re-import workflows that already exist (your edits are lost)
    [string]$OwnerEmail = '', [string]$OwnerPassword = '',
    [string]$ClaudeKey = '', [string]$TelegramToken = '', [string]$TelegramChatId = '',
    [string]$CjKey = '', [string]$Json2VideoKey = '',     # 'skip' = leave out for now
    [string]$SupportEmail = '', [string]$SupportAppPassword = '',
    [string]$StoreName = '', [string]$WarehouseCountry = '', [string]$SellCountries = '', [string]$TimeZone = '',
    [string]$ShippingPolicy = '', [string]$RefundPolicy = ''
)

$ErrorActionPreference = 'Stop'
# Everything shown in the window is also saved to setup-log.txt (keys are typed hidden, so they never appear in it).
try { Start-Transcript -Path (Join-Path $PSScriptRoot 'setup-log.txt') -Force | Out-Null } catch { }
$ProgressPreference = 'SilentlyContinue'
# Windows PowerShell 5.1 can serialise arrays as {"value":[..],"Count":n}; this undoes that.
if ($PSVersionTable.PSVersion.Major -lt 6) { Remove-TypeData System.Array -ErrorAction SilentlyContinue }
[Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$StateFile = Join-Path $Root '.setup-state.json'
$TunnelLog = Join-Path $Root '.tunnel.log'
$N8nImage = 'docker.n8n.io/n8nio/n8n:2.41.3'
$Session = New-Object Microsoft.PowerShell.Commands.WebRequestSession

# ------------------------------------------------------------------ output helpers

function Step($text) { Write-Host ''; Write-Host "==> $text" -ForegroundColor Cyan }
function Ok($text) { Write-Host "    [ok] $text" -ForegroundColor Green }
function Warn($text) { Write-Host "    [!] $text" -ForegroundColor Yellow }
function Info($text) { Write-Host "    $text" }
function Fail($text) { Write-Host ''; Write-Host "[X] $text" -ForegroundColor Red; exit 1 }

function Ask($question, $default = '') {
    $suffix = ''
    if ($default) { $suffix = " [$default]" }
    $answer = Read-Host "    $question$suffix"
    if ([string]::IsNullOrWhiteSpace($answer)) { return $default }
    return $answer.Trim()
}

function AskSecret($question) {
    $secure = Read-Host "    $question" -AsSecureString
    $bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
    try { return [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr).Trim() }
    finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr) }
}

function Load-State {
    if (Test-Path $StateFile) { return Get-Content $StateFile -Raw -Encoding UTF8 | ConvertFrom-Json }
    return New-Object PSObject
}

function Save-State($state) {
    # Only non-secret values are stored here (no keys or passwords).
    [IO.File]::WriteAllText($StateFile, (ConvertTo-Json -InputObject $state -Depth 10), [Text.Encoding]::UTF8)
}

function Set-Prop($obj, $name, $value) {
    if ($obj.PSObject.Properties.Name -contains $name) { $obj.$name = $value }
    else { $obj | Add-Member -NotePropertyName $name -NotePropertyValue $value }
}

function Get-Prop($obj, $name, $default = '') {
    if ($null -ne $obj -and $obj.PSObject.Properties.Name -contains $name -and $null -ne $obj.$name) { return $obj.$name }
    return $default
}

# ------------------------------------------------------------------ n8n API helpers

function ApiErrorText($err) {
    if ($err.ErrorDetails -and $err.ErrorDetails.Message) {
        try {
            $j = $err.ErrorDetails.Message | ConvertFrom-Json
            if ($j.error -and $j.error.message) { return $j.error.message }
            if ($j.message) { return $j.message }
            if ($j.description) { return $j.description }
        } catch { }
        return $err.ErrorDetails.Message
    }
    return $err.Exception.Message
}

function N8n($method, $path, $body = $null) {
    $params = @{ Method = $method; Uri = "$N8nUrl$path"; WebSession = $Session; ContentType = 'application/json; charset=utf-8' }
    if ($null -ne $body) {
        $json = $body
        if ($body -isnot [string]) { $json = ConvertTo-Json -InputObject $body -Depth 100 -Compress }
        $params.Body = [Text.Encoding]::UTF8.GetBytes($json)
    }
    try { $r = Invoke-RestMethod @params }
    catch { throw "n8n $method $path failed: $(ApiErrorText $_)" }
    if ($null -ne $r -and $r.PSObject.Properties.Name -contains 'data') { return $r.data }
    return $r
}

function AsList($value) {
    # n8n list endpoints return either an array or { count, data: [...] }
    if ($null -eq $value) { return @() }
    if ($value -is [array]) { return $value }
    if ($value.PSObject.Properties.Name -contains 'data') { return @($value.data) }
    return @($value)
}

# ------------------------------------------------------------------ 1. install and start

function Find-Exe($name, $candidates) {
    $cmd = Get-Command $name -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    foreach ($c in $candidates) { if ($c -and (Test-Path $c)) { return $c } }
    return $null
}

# Runs a program and returns its text (normal output and error output together); $LASTEXITCODE says if it worked.
# Windows PowerShell 5.1 turns any line a program prints as an error into a crash while ErrorActionPreference
# is 'Stop' (for example "no such object: n8n"), so it is relaxed for this call only.
function Run-Native([scriptblock]$Command) {
    $ErrorActionPreference = 'Continue'
    & $Command 2>&1 | ForEach-Object { "$_" }
}

function Refresh-Path {
    $env:Path = [Environment]::GetEnvironmentVariable('Path', 'Machine') + ';' + [Environment]::GetEnvironmentVariable('Path', 'User')
}

function Winget-Install($id, $label) {
    if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
        Fail "winget is missing. Install '$label' by hand, then run this script again."
    }
    Info "Installing $label (this can take a few minutes)..."
    Run-Native { winget install -e --id $id --accept-source-agreements --accept-package-agreements --silent } | Out-Host
    Refresh-Path
}

function Ensure-Docker {
    Step 'Checking Docker'
    $docker = Find-Exe 'docker' @("$env:ProgramFiles\Docker\Docker\resources\bin\docker.exe")
    if (-not $docker) {
        Winget-Install 'Docker.DockerDesktop' 'Docker Desktop'
        Warn 'Docker Desktop was installed. Restart your PC, open Docker Desktop once and accept its terms, then run this script again.'
        exit 0
    }
    Run-Native { & $docker info } | Out-Null
    if ($LASTEXITCODE -ne 0) {
        # Docker Desktop needs WSL 2. Without it Docker never starts, so say how to fix it right away.
        $wslOk = $false
        if (Get-Command wsl.exe -ErrorAction SilentlyContinue) { Run-Native { wsl.exe --status } | Out-Null; $wslOk = ($LASTEXITCODE -eq 0) }
        if (-not $wslOk) {
            Fail ('Docker needs WSL (Windows Subsystem for Linux), and it is not installed. Fix: click Start, type powershell, ' +
                  'right-click "Windows PowerShell" -> Run as administrator, type: wsl --install  and press Enter. ' +
                  'Restart your PC, open Docker Desktop until it says "Engine running", then run this script again.')
        }
        $app = "$env:ProgramFiles\Docker\Docker\Docker Desktop.exe"
        if (Test-Path $app) { Info 'Starting Docker Desktop...'; Start-Process $app }
        for ($i = 0; $i -lt 60; $i++) {
            Start-Sleep -Seconds 3
            Run-Native { & $docker info } | Out-Null
            if ($LASTEXITCODE -eq 0) { break }
        }
        if ($LASTEXITCODE -ne 0) { Fail 'Docker is not running. Open Docker Desktop, wait until it says "running", then run this script again.' }
    }
    Ok 'Docker is running'
    return $docker
}

function Start-Tunnel {
    Step 'Opening a free public HTTPS address (Cloudflare tunnel)'
    $cf = Find-Exe 'cloudflared' @("$env:ProgramFiles\cloudflared\cloudflared.exe", "${env:ProgramFiles(x86)}\cloudflared\cloudflared.exe")
    if (-not $cf) {
        Winget-Install 'Cloudflare.cloudflared' 'cloudflared'
        $cf = Find-Exe 'cloudflared' @("$env:ProgramFiles\cloudflared\cloudflared.exe", "${env:ProgramFiles(x86)}\cloudflared\cloudflared.exe")
        if (-not $cf) { Fail 'cloudflared was installed but cannot be found. Close this window, open a new one and run the script again.' }
    }
    Get-Process cloudflared -ErrorAction SilentlyContinue | Stop-Process -Force
    if (Test-Path $TunnelLog) { Remove-Item $TunnelLog -Force }
    Start-Process -FilePath $cf -ArgumentList @('tunnel', '--no-autoupdate', '--url', 'http://localhost:5678') `
        -RedirectStandardError $TunnelLog -WindowStyle Hidden | Out-Null
    for ($i = 0; $i -lt 40; $i++) {
        Start-Sleep -Seconds 1
        if (Test-Path $TunnelLog) {
            $m = Select-String -Path $TunnelLog -Pattern 'https://[a-z0-9-]+\.trycloudflare\.com' -ErrorAction SilentlyContinue | Select-Object -First 1
            if ($m) { $url = $m.Matches[0].Value; Ok "Public address: $url"; return $url }
        }
    }
    Fail "The tunnel did not start. See $TunnelLog"
}

function Start-N8n($docker, $publicUrl, $tz) {
    Step 'Starting n8n'
    Run-Native { & $docker volume create n8n_data } | Out-Null
    $current = (Run-Native { & $docker inspect n8n --format '{{range .Config.Env}}{{println .}}{{end}}' }) -join "`n"
    if ($LASTEXITCODE -eq 0 -and $current -match [regex]::Escape("N8N_WEBHOOK_URL=$publicUrl/")) {
        Run-Native { & $docker start n8n } | Out-Null
        Ok 'n8n container already set up for this address'
    } else {
        Run-Native { & $docker rm -f n8n } | Out-Null   # no container yet is fine; your data lives in the n8n_data volume and is kept
        Info 'Downloading and starting n8n (the first time takes a few minutes)...'
        $out = Run-Native { & $docker run -d --name n8n --restart unless-stopped -p 5678:5678 `
            -e "N8N_WEBHOOK_URL=$publicUrl/" -e "GENERIC_TIMEZONE=$tz" -e "TZ=$tz" `
            -e N8N_SECURE_COOKIE=false -e N8N_LISTEN_ADDRESS=0.0.0.0 -e N8N_DIAGNOSTICS_ENABLED=false `
            -v n8n_data:/home/node/.n8n $N8nImage }
        if ($LASTEXITCODE -ne 0) { Fail ("Could not start the n8n container. Is Docker Desktop running? Docker said: " + ((@($out) | Select-Object -Last 3) -join ' ')) }
        Ok "n8n started ($N8nImage)"
    }
    Wait-N8n
}

function Wait-N8n {
    for ($i = 0; $i -lt 90; $i++) {
        try { Invoke-RestMethod "$N8nUrl/rest/settings" -TimeoutSec 5 | Out-Null; Ok "n8n is up at $N8nUrl"; return } catch { Start-Sleep -Seconds 2 }
    }
    Fail "n8n did not start. Check Docker Desktop -> Containers -> n8n -> Logs."
}

# ------------------------------------------------------------------ 2. owner account

function Ensure-Owner($state) {
    Step 'n8n owner account'
    $settings = Invoke-RestMethod "$N8nUrl/rest/settings"
    $needsSetup = $settings.data.userManagement.showSetupOnFirstLoad
    $email = $OwnerEmail
    if (-not $email) { $email = Ask 'Your email for the n8n login' (Get-Prop $state 'owner_email') }
    $password = $OwnerPassword
    if ($needsSetup) {
        Info 'Creating your n8n account (password: 8+ characters with a number and a capital letter).'
        if (-not $password) { $password = AskSecret 'Choose an n8n password' }
        N8n 'POST' '/rest/owner/setup' @{ email = $email; firstName = 'Store'; lastName = 'Owner'; password = $password } | Out-Null
        Ok "Account created for $email"
    } else {
        if (-not $password) { $password = AskSecret 'Your n8n password' }
        N8n 'POST' '/rest/login' @{ emailOrLdapLoginId = $email; password = $password } | Out-Null
        Ok "Logged in as $email"
    }
    Set-Prop $state 'owner_email' $email
}

# ------------------------------------------------------------------ 3. answers and keys

function Collect-Answers($state) {
    Step 'About your store (press Enter to keep the value in brackets)'
    $a = [ordered]@{}
    $a.store_name = $StoreName; if (-not $a.store_name) { $a.store_name = Ask 'Store name' (Get-Prop $state 'store_name') }
    $a.warehouse_country = $WarehouseCountry
    if (-not $a.warehouse_country) { $a.warehouse_country = Ask 'Main market / CJ warehouse the products come from (US, DE...)' (Get-Prop $state 'warehouse_country' 'US') }
    $a.warehouse_country = $a.warehouse_country.Trim().ToUpper()
    $a.sell_countries = $SellCountries
    if (-not $a.sell_countries) { $a.sell_countries = Ask 'All countries you sell to, comma separated' (Get-Prop $state 'sell_countries' 'US,DE,CA,AU') }
    $a.sell_countries = ($a.sell_countries.ToUpper() -replace '\s', '')
    $a.timezone = $TimeZone
    if (-not $a.timezone) { $a.timezone = Ask 'Your time zone (e.g. America/New_York, Europe/London)' (Get-Prop $state 'timezone' 'Europe/London') }
    $a.shipping_policy = $ShippingPolicy
    if (-not $a.shipping_policy) {
        $a.shipping_policy = Ask 'Shipping promise, one sentence' (Get-Prop $state 'shipping_policy' 'Orders are processed in 1-3 business days. Delivery: USA and EU 4-10 business days, other countries 8-18 business days. Every order gets a tracking number by email.')
    }
    $a.refund_policy = $RefundPolicy
    if (-not $a.refund_policy) {
        $a.refund_policy = Ask 'Refund policy summary, same as your Shopify policy' (Get-Prop $state 'refund_policy' 'Damaged or wrong items get a free replacement or full refund within 30 days of delivery (photo needed). Unused items can be returned within 30 days; email us first, the customer pays return shipping.')
    }
    foreach ($k in $a.Keys) { Set-Prop $state $k $a[$k] }
    return $a
}

function Existing-Credentials {
    $map = @{}
    foreach ($c in (AsList (N8n 'GET' '/rest/credentials'))) { $map[$c.name] = $c }
    return $map
}

function Test-GmailLogin($user, $password) {
    # Logs in to Gmail over IMAP once, the same way n8n will, so a wrong App password shows up now.
    $client = New-Object Net.Sockets.TcpClient('imap.gmail.com', 993)
    try {
        $ssl = New-Object Net.Security.SslStream($client.GetStream(), $false)
        $ssl.AuthenticateAsClient('imap.gmail.com')
        $reader = New-Object IO.StreamReader($ssl)
        $writer = New-Object IO.StreamWriter($ssl)
        $writer.AutoFlush = $true
        $null = $reader.ReadLine()
        $writer.WriteLine("a1 LOGIN `"$user`" `"$password`"")
        $line = ''
        for ($i = 0; $i -lt 20; $i++) { $line = $reader.ReadLine(); if ($line -like 'a1 *') { break } }
        $writer.WriteLine('a2 LOGOUT')
        return ($line -like 'a1 OK*')
    } finally { $client.Close() }
}

function Test-Keys($keys) {
    if ($SkipKeyChecks) { Warn 'Key checks skipped'; return }
    Step 'Checking your keys'
    if ($keys.claude) {
        try {
            Invoke-RestMethod 'https://api.anthropic.com/v1/models' -Headers @{ 'x-api-key' = $keys.claude; 'anthropic-version' = '2023-06-01' } | Out-Null
            Ok 'Claude key works'
        } catch {
            Fail ("The Claude key was rejected: $(ApiErrorText $_)`n    Fix: platform.claude.com -> Settings -> API keys -> Create key, " +
                  'set Workspace to "Default workspace" (not the whole organization), expiry "Never", and add credit under Billing. Then run this script again.')
        }
    }
    if ($keys.telegram) {
        try { $me = Invoke-RestMethod "https://api.telegram.org/bot$($keys.telegram)/getMe"; Ok "Telegram bot: @$($me.result.username)" }
        catch { Fail 'The Telegram bot token was rejected. Copy it again from @BotFather.' }
    }
    if ($keys.cj) {
        try {
            $r = Invoke-RestMethod 'https://developers.cjdropshipping.com/api2.0/v1/authentication/getAccessToken' -Method Post `
                -ContentType 'application/json' -Body (ConvertTo-Json @{ apiKey = $keys.cj })
            if ($r.code -ne 200) { Fail "CJ rejected the API key: $($r.message)" }
            Ok 'CJ key works'
        } catch { Fail "Could not check the CJ key: $(ApiErrorText $_)" }
    }
    if ($keys.email -and $keys.app_password) {
        $okLogin = $false
        try { $okLogin = Test-GmailLogin $keys.email $keys.app_password } catch { Warn "Could not reach Gmail to test the login: $($_.Exception.Message)"; $okLogin = $true }
        if (-not $okLogin) { Fail 'Gmail refused the App password. Create a new one (Google Account -> Security -> App passwords) and use that, not your normal password.' }
        Ok 'Gmail login works'
    }
}

function Ensure-Credentials($state) {
    Step 'Your keys (typed here, saved encrypted inside n8n, never written to a file)'
    $have = Existing-Credentials
    $keys = @{}
    if (-not $have.ContainsKey('Claude')) { $keys.claude = $ClaudeKey; if (-not $keys.claude) { $keys.claude = AskSecret 'Claude API key (console.anthropic.com)' } }
    if (-not $have.ContainsKey('Telegram bot')) { $keys.telegram = $TelegramToken; if (-not $keys.telegram) { $keys.telegram = AskSecret 'Telegram bot token (from @BotFather)' } }
    if (-not $have.ContainsKey('CJ API key')) { $keys.cj = $CjKey; if (-not $keys.cj) { $keys.cj = AskSecret 'CJ API key' } }
    if (-not $have.ContainsKey('JSON2Video')) {
        $keys.json2video = $Json2VideoKey
        if ($keys.json2video -eq 'skip') { $keys.json2video = '' }
        elseif (-not $keys.json2video) { $keys.json2video = AskSecret 'JSON2Video API key (press Enter to skip for now)' }
    }
    if (-not $have.ContainsKey('Support inbox')) {
        $keys.email = $SupportEmail
        if ($keys.email -eq 'skip') { $keys.email = '' }
        elseif (-not $keys.email) { $keys.email = Ask 'Support Gmail address (press Enter to skip for now)' (Get-Prop $state 'support_email') }
        if ($keys.email) {
            $keys.app_password = $SupportAppPassword
            if (-not $keys.app_password) { $keys.app_password = (AskSecret 'Gmail App password (16 letters)') -replace '\s', '' }
        }
    } else {
        $keys.email = Get-Prop $state 'support_email'
    }
    foreach ($required in @('claude', 'telegram', 'cj')) {
        if ($keys.ContainsKey($required) -and -not $keys[$required]) { Fail "The $required key is required." }
    }
    Test-Keys $keys

    $defs = @(
        @{ name = 'Claude'; type = 'anthropicApi'; key = 'claude'; data = { param($k) @{ apiKey = $k.claude } } },
        @{ name = 'Telegram bot'; type = 'telegramApi'; key = 'telegram'; data = { param($k) @{ accessToken = $k.telegram } } },
        @{ name = 'CJ API key'; type = 'httpCustomAuth'; key = 'cj'; data = { param($k) @{ json = (ConvertTo-Json @{ body = @{ apiKey = $k.cj } } -Compress) } } },
        @{ name = 'JSON2Video'; type = 'httpHeaderAuth'; key = 'json2video'; data = { param($k) @{ name = 'x-api-key'; value = $k.json2video } } },
        @{ name = 'Support inbox'; type = 'imap'; key = 'email'; data = { param($k) @{ user = $k.email; password = $k.app_password; host = 'imap.gmail.com'; port = 993; secure = $true } } },
        @{ name = 'Support email'; type = 'smtp'; key = 'email'; data = { param($k) @{ user = $k.email; password = $k.app_password; host = 'smtp.gmail.com'; port = 465; secure = $true } } }
    )
    $ids = @{}
    $empty = @()
    foreach ($d in $defs) {
        if ($have.ContainsKey($d.name)) { $ids[$d.type] = @{ id = $have[$d.name].id; name = $d.name }; Ok "$($d.name): already saved"; continue }
        if (-not $keys[$d.key]) {
            # Saved empty so the workflows can still be switched on; add the real value in n8n later.
            if ($d.type -in @('httpHeaderAuth', 'imap', 'smtp')) {
                $c = N8n 'POST' '/rest/credentials' @{ name = $d.name; type = $d.type; data = @{} }
                $ids[$d.type] = @{ id = $c.id; name = $d.name }
                $empty += $d.type
                Warn "$($d.name): skipped (saved empty; fill it in later under n8n -> Credentials)"
            }
            continue
        }
        $c = N8n 'POST' '/rest/credentials' @{ name = $d.name; type = $d.type; data = (& $d.data $keys) }
        $ids[$d.type] = @{ id = $c.id; name = $d.name }
        Ok "$($d.name): saved"
    }
    if ($keys.email) { Set-Prop $state 'support_email' $keys.email }
    return @{ ids = $ids; telegram = $keys.telegram; empty = $empty }
}

function Find-ChatId($state, $telegramToken) {
    Step 'Your Telegram chat ID'
    if ($TelegramChatId) { Ok "Using $TelegramChatId"; return $TelegramChatId }
    $saved = Get-Prop $state 'telegram_chat_id'
    if ($saved) { Ok "Using $saved (saved from last time)"; return $saved }
    if (-not $telegramToken) { $telegramToken = AskSecret 'Telegram bot token again (needed once to find your chat ID)' }
    $api = "https://api.telegram.org/bot$telegramToken"
    Invoke-RestMethod "$api/deleteWebhook" | Out-Null   # n8n sets it again when workflow 02 is switched on
    Write-Host '    Open Telegram, find your bot and send it any message (for example: hi).' -ForegroundColor Yellow
    for ($i = 0; $i -lt 24; $i++) {
        $u = Invoke-RestMethod "$api/getUpdates?timeout=10"
        $msgs = @($u.result | Where-Object { $_.message })
        if ($msgs.Count -gt 0) {
            $id = [string]$msgs[-1].message.chat.id
            Ok "Found it: $id"
            return $id
        }
    }
    Fail 'No message arrived within 4 minutes. Run the script again and message your bot.'
}

# ------------------------------------------------------------------ 4. data tables

$Tables = [ordered]@{
    playbook = @('version'); products = @('cj_cost', 'ship_cost', 'sell_price', 'profit_per_order', 'score'); content = @()
    feedback = @('views', 'clicks', 'sales'); orders = @('revenue'); clips = @(); support = @('confidence')
    reports = @('orders_today', 'revenue_today', 'orders_7d', 'revenue_7d', 'cj_cost_7d', 'est_profit_7d')
    payments = @('amount', 'revenue', 'profit')
}

function Ensure-Tables {
    Step 'Agent memory (9 Data Tables)'
    $projectId = (N8n 'GET' '/rest/projects/personal').id
    $existing = @{}
    foreach ($t in (AsList (N8n 'GET' "/rest/projects/$projectId/data-tables"))) { $existing[$t.name] = $t.id }
    foreach ($name in $Tables.Keys) {
        if ($existing.ContainsKey($name)) { Ok "${name}: already there"; continue }
        $header = (Get-Content (Join-Path $Root "templates\$name.csv") -TotalCount 1 -Encoding UTF8).Trim()
        $cols = @($header -split ',' | ForEach-Object {
            $type = 'string'; if ($Tables[$name] -contains $_) { $type = 'number' }
            @{ name = $_; type = $type }
        })
        $t = N8n 'POST' "/rest/projects/$projectId/data-tables" @{ name = $name; columns = $cols }
        $existing[$name] = $t.id
        Ok "${name}: created"
    }
    $rows = N8n 'GET' "/rest/projects/$projectId/data-tables/$($existing['playbook'])/rows"
    if ([int](Get-Prop $rows 'count' 0) -eq 0) {
        $seed = @(Import-Csv (Join-Path $Root 'templates\playbook.csv') -Encoding UTF8 | ForEach-Object {
            [ordered]@{ rule_id = $_.rule_id; agent = $_.agent; rule = $_.rule; status = $_.status; version = [int]$_.version; evidence = $_.evidence }
        })
        N8n 'POST' "/rest/projects/$projectId/data-tables/$($existing['playbook'])/insert" @{ data = $seed; returnType = 'count' } | Out-Null
        Ok "playbook: loaded $($seed.Count) starting rules"
    }
}

# ------------------------------------------------------------------ 5. workflows

$CredentialFor = @{
    '@n8n/n8n-nodes-langchain.lmChatAnthropic' = 'anthropicApi'
    'n8n-nodes-base.telegram' = 'telegramApi'; 'n8n-nodes-base.telegramTrigger' = 'telegramApi'
    'n8n-nodes-base.emailReadImap' = 'imap'; 'n8n-nodes-base.emailSend' = 'smtp'
}

function Prepare-Workflow($wf, $answers, $chatId, $credIds, $errorWorkflowId, $state) {
    $signature = 'Best regards,\nThe ' + $answers.store_name + ' team'
    $values = @{
        telegram_chat_id = $chatId; support_email = (Get-Prop $state 'support_email' 'PASTE_YOUR_SUPPORT_EMAIL')
        store_name = $answers.store_name; email_signature = $signature; warehouse_country = $answers.warehouse_country
        sell_countries = $answers.sell_countries
        shipping_policy = $answers.shipping_policy; refund_policy = $answers.refund_policy
    }
    foreach ($node in $wf.nodes) {
        if ($node.name -like '*Settings') {
            foreach ($a in $node.parameters.assignments.assignments) {
                if ($values.ContainsKey($a.name) -and $values[$a.name]) { $a.value = [string]$values[$a.name] }
            }
        }
        $credType = $CredentialFor[$node.type]
        if ($node.type -eq 'n8n-nodes-base.httpRequest') { $credType = Get-Prop $node.parameters 'genericAuthType' $null }
        if ($credType -and $credIds.ContainsKey($credType)) {
            Set-Prop $node 'credentials' ([pscustomobject]@{ $credType = [pscustomobject]$credIds[$credType] })
        }
        if ($node.name -eq 'Shopify: order paid') {
            $path = Get-Prop $state 'shopify_webhook_path'
            if (-not $path) {
                $path = 'shopify-order-' + (-join ((48..57) + (97..122) | Get-Random -Count 12 | ForEach-Object { [char]$_ }))
                Set-Prop $state 'shopify_webhook_path' $path
            }
            $node.parameters.path = $path
        }
    }
    if ($errorWorkflowId) { Set-Prop $wf.settings 'errorWorkflow' $errorWorkflowId }
    return [ordered]@{ name = $wf.name; nodes = $wf.nodes; connections = $wf.connections; settings = $wf.settings }
}

function Ensure-Workflows($answers, $chatId, $credIds, $state) {
    Step 'Importing the 8 workflows'
    $existing = @{}
    foreach ($w in (AsList (N8n 'GET' '/rest/workflows'))) { $existing[$w.name] = $w }
    $files = Get-ChildItem (Join-Path $Root 'n8n-workflows') -Filter '*.json' | Sort-Object Name
    $result = [ordered]@{}
    $errorId = $null
    foreach ($f in $files) {
        $wf = Get-Content $f.FullName -Raw -Encoding UTF8 | ConvertFrom-Json
        $old = $existing[$wf.name]
        if ($old -and -not $ReplaceWorkflows) {
            Ok "$($wf.name): already imported"
            $result[$wf.name] = $old.id
        } else {
            if ($old) {
                if ($old.active) { N8n 'POST' "/rest/workflows/$($old.id)/deactivate" @{} | Out-Null }
                N8n 'POST' "/rest/workflows/$($old.id)/archive" @{} | Out-Null
            }
            $body = Prepare-Workflow $wf $answers $chatId $credIds $errorId $state
            $created = N8n 'POST' '/rest/workflows' $body
            $result[$wf.name] = $created.id
            Ok "$($wf.name): imported"
        }
        if ($f.Name -like '00-*') { $errorId = $result[$wf.name] }
    }
    return $result
}

function Activate-Workflows($workflowIds, $emptyTypes) {
    Step 'Switching the workflows on'
    $failed = @()
    foreach ($name in $workflowIds.Keys) {
        if ($name -like '06*' -and $emptyTypes -contains 'imap') {
            Warn "${name}: left off until the support Gmail is added (n8n -> Credentials -> Support inbox / Support email, then run this script again)"
            continue
        }
        $wf = N8n 'GET' "/rest/workflows/$($workflowIds[$name])"
        if ($wf.active) { Ok "${name}: already on"; continue }
        try {
            N8n 'POST' "/rest/workflows/$($wf.id)/activate" @{ versionId = $wf.versionId } | Out-Null
            Ok "${name}: on"
        } catch {
            $failed += $name
            Warn "${name} could not be switched on: $($_.Exception.Message)"
        }
    }
    return $failed
}

# ------------------------------------------------------------------ main

Write-Host ''
Write-Host '  Dropshipping agents - setup' -ForegroundColor Cyan
Write-Host '  Your keys are typed here and stored encrypted inside n8n on this PC. Nothing is sent to Claude chat.'

$state = Load-State
$answers = Collect-Answers $state

if (-not $SkipInstall) {
    $docker = Ensure-Docker
    if (-not $PublicUrl) { $PublicUrl = Start-Tunnel }
    Start-N8n $docker $PublicUrl $answers.timezone
} else {
    if (-not $PublicUrl) { $PublicUrl = Get-Prop $state 'public_url' $N8nUrl }
    Wait-N8n
}
Set-Prop $state 'public_url' $PublicUrl
Save-State $state

Ensure-Owner $state
Save-State $state
$creds = Ensure-Credentials $state
$chatId = Find-ChatId $state $creds.telegram
Set-Prop $state 'telegram_chat_id' $chatId
Save-State $state
Ensure-Tables
$workflowIds = Ensure-Workflows $answers $chatId $creds.ids $state
Save-State $state
$failed = Activate-Workflows $workflowIds $creds.empty
if ($creds.telegram -and -not $SkipKeyChecks) {
    # n8n reports "on" even if Telegram refused its webhook, so ask Telegram directly.
    Start-Sleep -Seconds 3
    $hook = (Invoke-RestMethod "https://api.telegram.org/bot$($creds.telegram)/getWebhookInfo").result
    if (-not $hook.url) {
        Warn 'Telegram has no webhook for your bot, so /commands will not reach n8n. Check that the public address opens in a browser, then run this script again.'
        $failed += '02 (Telegram webhook)'
    } elseif ($hook.last_error_message) {
        Warn "Telegram reports a problem reaching n8n: $($hook.last_error_message)"
    } else { Ok 'Telegram is connected to n8n' }
}

$webhook = "$PublicUrl/webhook/$(Get-Prop $state 'shopify_webhook_path')"
Write-Host ''
Write-Host '==================================================================' -ForegroundColor Green
Write-Host '  Setup finished' -ForegroundColor Green
Write-Host '==================================================================' -ForegroundColor Green
Write-Host "  n8n (log in here):  $N8nUrl"
Write-Host "  Public address:     $PublicUrl"
Write-Host ''
Write-Host '  Left for you to do:' -ForegroundColor Yellow
Write-Host '  1. Shopify admin -> Settings -> Notifications -> Webhooks -> Create webhook'
Write-Host '       Event: Order payment   Format: JSON'
Write-Host "       URL:   $webhook"
Write-Host '     Then click "Send test notification" - you should get a Telegram message.'
Write-Host '  2. Finish Shopify Payments verification and set your store contact email to the support Gmail.'
Write-Host '  3. Auto-pay stays OFF. When your CJ wallet has money (Payoneer), open workflow'
Write-Host '     "07 - CJ auto-pay" in n8n -> Settings node -> set auto_pay to yes.'
Write-Host '  4. Send /help to your bot to see the commands. Research arrives every morning at 07:00.'
if ($failed.Count -gt 0) {
    Write-Host ''
    Write-Host "  Not switched on yet: $($failed -join ', ')" -ForegroundColor Yellow
    Write-Host '  Usually a key is wrong or missing: open n8n -> Credentials, fix it, then run this script again.'
}
if ($PublicUrl -like '*trycloudflare.com*') {
    Write-Host ''
    Write-Host '  Note: this free public address changes when the PC restarts. After a restart, run this script' -ForegroundColor Yellow
    Write-Host '  again and paste the new webhook URL into Shopify. For 24/7 running, see SETUP.md Part 2, Option A.' -ForegroundColor Yellow
}
Write-Host ''
