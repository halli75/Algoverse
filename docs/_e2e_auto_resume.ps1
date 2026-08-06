# Auto-resume local E2E when CUDA returns after driver crash / reboot.
$root = "C:\Users\arnav\Projects\algoverse"
$log = Join-Path $root "docs\e2e-monitor.log"
$run = Join-Path $root "docs\e2e-local-run.log"
$err = Join-Path $root "docs\e2e-local-run.err.log"
$res = Join-Path $root "docs\e2e_results.json"
$py = "C:\Python313\python.exe"
$pipe = Join-Path $root "scripts\e2e_local_pipeline.py"

function Tick($msg) {
  Add-Content $log ("{0} AUTO {1}" -f (Get-Date).ToString("o"), $msg)
}

Tick "watcher_start"
while ($true) {
  if (Test-Path $res) {
    try {
      $j = Get-Content $res -Raw | ConvertFrom-Json
      if ($j.finished) { Tick "E2E_COMPLETE"; break }
    } catch {}
  }

  $alive = Get-CimInstance Win32_Process -Filter "Name = 'python.exe'" |
    Where-Object { $_.CommandLine -match 'e2e_local_pipeline' }
  if ($alive) {
    $tail = if (Test-Path $run) { (Get-Content $run -Tail 3) -join " | " } else { "" }
    Tick ("RUNNING pid={0} :: {1}" -f $alive.ProcessId, $tail)
    Start-Sleep -Seconds 120
    continue
  }

  $cuda = & $py -c "import torch; print(int(torch.cuda.is_available()))" 2>$null
  if ($cuda -ne "1") {
    Tick "waiting_cuda"
    Start-Sleep -Seconds 120
    continue
  }

  Tick "cuda_ok_launching"
  Remove-Item $res -ErrorAction SilentlyContinue
  "" | Set-Content $run
  "" | Set-Content $err
  $env:CUDA_VISIBLE_DEVICES = "0"
  $env:PYTHONUNBUFFERED = "1"
  $p = Start-Process -FilePath $py -ArgumentList "-u", $pipe -WorkingDirectory $root `
    -RedirectStandardOutput $run -RedirectStandardError $err -WindowStyle Hidden -PassThru
  $p.Id | Set-Content (Join-Path $root "docs\e2e-local.pid")
  Tick ("launched pid={0}" -f $p.Id)
  Start-Sleep -Seconds 120
}
