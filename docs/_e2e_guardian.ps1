# Hang-aware E2E guardian. Archives partial results before restart.
$ErrorActionPreference = "Continue"
$root = "C:\Users\arnav\Projects\algoverse"
$log = Join-Path $root "docs\e2e-monitor.log"
$run = Join-Path $root "docs\e2e-local-run.log"
$err = Join-Path $root "docs\e2e-local-run.err.log"
$res = Join-Path $root "docs\e2e_results.json"
$hb = Join-Path $root "docs\e2e_heartbeat.json"
$journal = Join-Path $root "docs\e2e_run_journal.md"
$py = "C:\Python313\python.exe"
$pipe = Join-Path $root "scripts\e2e_local_pipeline.py"
$STALE_SEC = 1500
$MAX_RESTARTS = 4
$restarts = 0

function Tick([string]$msg) {
  $line = "{0} GUARDIAN {1}" -f (Get-Date).ToString("o"), $msg
  Add-Content -Path $log -Value $line
  Add-Content -Path $journal -Value ("- `{0}` {1}" -f (Get-Date).ToString("yyyy-MM-dd HH:mm:ss"), $msg)
}

function Archive-Partial {
  if (Test-Path $res) {
    $stamp = (Get-Date).ToString("yyyyMMdd_HHmmss")
    $dest = Join-Path $root ("docs\e2e_results.partial.{0}.json" -f $stamp)
    Copy-Item $res $dest -Force
    Tick ("archived_partial " + (Split-Path $dest -Leaf))
  }
}

function Is-Finished {
  if (-not (Test-Path $res)) { return $false }
  try {
    $j = Get-Content $res -Raw | ConvertFrom-Json
    return [bool]$j.finished
  } catch {
    return $false
  }
}

function Get-PipelinePid {
  $p = Get-CimInstance Win32_Process -Filter "Name = 'python.exe'" |
    Where-Object { $_.CommandLine -match 'e2e_local_pipeline' } |
    Select-Object -First 1
  if ($p) { return [int]$p.ProcessId }
  return $null
}

function Get-HeartbeatAgeSec {
  # Prefer heartbeat file; if missing during boot, fall back to process uptime
  # (never treat "no file yet" as infinitely stale — that false-killed launch).
  if (Test-Path $hb) {
    try {
      $j = Get-Content $hb -Raw | ConvertFrom-Json
      if ($null -ne $j.unix) {
        $epoch = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
        return [int]($epoch - [int64]$j.unix)
      }
    } catch {}
    return [int](((Get-Date) - (Get-Item $hb).LastWriteTime).TotalSeconds)
  }
  $pp = Get-PipelinePid
  if ($pp) {
    $proc = Get-Process -Id $pp -ErrorAction SilentlyContinue
    if ($proc) {
      return [int](((Get-Date) - $proc.StartTime).TotalSeconds)
    }
  }
  return 0
}

function Launch-Pipeline([string]$reason) {
  if ($restarts -ge $MAX_RESTARTS) {
    Tick ("ABORT max_restarts=$MAX_RESTARTS reason=$reason")
    return $false
  }
  $cuda = & $py -c "import torch; print(int(torch.cuda.is_available()))" 2>$null
  if ("$cuda" -ne "1") {
    Tick "waiting_cuda"
    return $true
  }
  Archive-Partial
  $script:restarts++
  Tick ("launch reason=$reason restart=$restarts")
  Set-Content -Path $run -Value ""
  Set-Content -Path $err -Value ""
  $env:CUDA_VISIBLE_DEVICES = "0"
  $env:PYTHONUNBUFFERED = "1"
  $env:E2E_LOCAL_SAFE = "1"
  $proc = Start-Process -FilePath $py -ArgumentList @("-u", $pipe) -WorkingDirectory $root `
    -RedirectStandardOutput $run -RedirectStandardError $err -WindowStyle Hidden -PassThru
  Set-Content -Path (Join-Path $root "docs\e2e-local.pid") -Value $proc.Id
  Tick ("launched pid=$($proc.Id)")
  return $true
}

Tick "guardian_start stale_sec=$STALE_SEC max_restarts=$MAX_RESTARTS local_safe=1"

if ((-not (Get-PipelinePid)) -and (-not (Is-Finished))) {
  if (-not (Launch-Pipeline "initial")) { exit 2 }
  Start-Sleep -Seconds 90
}

while ($true) {
  if (Is-Finished) {
    Tick "E2E_COMPLETE detected - guardian idle"
    break
  }

  $pipePid = Get-PipelinePid
  if ($pipePid) {
    $age = Get-HeartbeatAgeSec
    $stage = "?"
    if (Test-Path $hb) {
      try { $stage = (Get-Content $hb -Raw | ConvertFrom-Json).stage } catch {}
    }
    $tail = ""
    if (Test-Path $run) {
      $tail = ((Get-Content $run -Tail 2) -join " | ")
    }
    Tick ("RUNNING pid=$pipePid hb_age_s=$age stage=$stage :: $tail")

    if ($age -gt $STALE_SEC) {
      Tick ("HANG_DETECTED pid=$pipePid hb_age_s=$age - killing")
      Stop-Process -Id $pipePid -Force -ErrorAction SilentlyContinue
      Start-Sleep -Seconds 3
      if (-not (Launch-Pipeline "hang_restart age=$age")) { break }
    }
    Start-Sleep -Seconds 120
    continue
  }

  Tick "pipeline_dead unfinished - relaunch"
  if (-not (Launch-Pipeline "dead_relaunch")) { break }
  Start-Sleep -Seconds 120
}

Tick "guardian_exit"
