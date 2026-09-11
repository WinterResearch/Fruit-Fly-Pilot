$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$Root = $PSScriptRoot
$Downloads = Join-Path $Root 'downloads'
$Data = Join-Path $Root 'data'
$Vendor = Join-Path $Root 'web/vendor'
$Upstream = Join-Path $Root 'third_party/flybrain'
foreach ($Dir in @($Downloads, $Data, $Vendor, $Upstream)) { New-Item -ItemType Directory -Force -Path $Dir | Out-Null }

function Get-File($Url, $Destination, $Sha256 = '') {
    if (Test-Path $Destination) {
        if ((Get-Item $Destination).Length -gt 0 -and (!$Sha256 -or ((Get-FileHash $Destination -Algorithm SHA256).Hash -eq $Sha256))) {
            Write-Host "Already downloaded: $(Split-Path $Destination -Leaf)"
            return
        }
    }
    Write-Host "Downloading: $(Split-Path $Destination -Leaf)"
    $Part = "$Destination.partial"
    Invoke-WebRequest -UseBasicParsing -Uri $Url -OutFile $Part
    if ($Sha256 -and ((Get-FileHash $Part -Algorithm SHA256).Hash -ne $Sha256)) { throw "Checksum mismatch: $Destination" }
    Move-Item -Force $Part $Destination
}

# Pin the upstream snapshot so the binary, metadata, and parser agree.
$LockPath = Join-Path $Upstream 'source.json'
if (Test-Path $LockPath) {
    $Commit = (Get-Content $LockPath -Raw | ConvertFrom-Json).commit
} else {
    $Commit = (Invoke-RestMethod 'https://api.github.com/repos/snedea/flybrain/commits/main').sha
    @{ repository = 'https://github.com/snedea/flybrain'; commit = $Commit } | ConvertTo-Json | Set-Content $LockPath
}
$Base = "https://raw.githubusercontent.com/snedea/flybrain/$Commit"
Get-File "$Base/data/connectome.bin.gz" (Join-Path $Data 'connectome.bin.gz')
Get-File "$Base/data/neuron_meta.json" (Join-Path $Data 'neuron_meta.json')
Get-File "$Base/js/sim-worker.js" (Join-Path $Upstream 'sim-worker.js')
Get-File "$Base/license.md" (Join-Path $Upstream 'LICENSE.md')
Get-File 'https://cdn.jsdelivr.net/npm/three@0.160.1/build/three.module.js' (Join-Path $Vendor 'three.module.js')
Get-File 'https://raw.githubusercontent.com/mrdoob/three.js/r160/LICENSE' (Join-Path $Vendor 'THREE-LICENSE.txt')

# Download Linux wheels only. No packages are installed into Windows Python.
$Specs = @(
    @('jsbsim', '1.2.3'),
    @('imageio-ffmpeg', '0.6.0'),
    @('playwright', '1.51.0'),
    @('pyee', '12.1.1'),
    @('greenlet', '3.1.1'),
    @('typing-extensions', '4.12.2')
)
foreach ($Spec in $Specs) {
    $Name = $Spec[0]; $Version = $Spec[1]
    $Meta = Invoke-RestMethod "https://pypi.org/pypi/$Name/$Version/json"
    $Wheel = $Meta.urls | Where-Object {
        $_.filename -match '\.whl$' -and (
            $_.filename -match '(py3|py2.py3)-none-any' -or
            ($_.filename -match 'manylinux.*x86_64' -and $_.filename -match '(cp310-cp310|cp39-abi3|py3-none)')
        )
    } | Select-Object -First 1
    if (!$Wheel) { throw "No Linux Python 3.10 wheel found for $Name $Version" }
    Get-File $Wheel.url (Join-Path $Downloads $Wheel.filename) $Wheel.digests.sha256
}
Get-File 'https://cdn.playwright.dev/dbazure/download/playwright/builds/chromium/1161/chromium-headless-shell-linux.zip' (Join-Path $Downloads 'chromium-headless-shell-linux.zip')

$Hashes = Get-ChildItem $Data, $Vendor, $Downloads -File | Get-FileHash -Algorithm SHA256 | Select-Object Path, Hash
$Hashes | ConvertTo-Json | Set-Content (Join-Path $Downloads 'checksums.json')
Write-Host ''
Write-Host 'READY - downloads complete. Tell Codex to continue.' -ForegroundColor Green
