$log = "C:\Users\arnav\Projects\algoverse\docs\e2e-monitor.log"
$run = "C:\Users\arnav\Projects\algoverse\docs\e2e-local-run.log"
$err = "C:\Users\arnav\Projects\algoverse\docs\e2e-local-run.err.log"
$res = "C:\Users\arnav\Projects\algoverse\docs\e2e_results.json"
while ($true) {
  $ts = (Get-Date).ToString("o")
  $tail = ""
  if (Test-Path $run) {
    $lines = Get-Content $run -Tail 8 -ErrorAction SilentlyContinue
    $tail = ($lines -join " | ")
  }
  $phase = "unknown"
  if (Test-Path $res) {
    try {
      $j = Get-Content $res -Raw | ConvertFrom-Json
      $phase = ($j.phases.PSObject.Properties.Name | Select-Object -Last 1)
      if ($j.finished) { Add-Content $log "$ts LOCAL_E2E_COMPLETE phase=$phase"; break }
    } catch {}
  }
  $alive = Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Where-Object { $_.CommandLine -match 'e2e_local_pipeline' }
  $status = if ($alive) { "RUNNING pid=$($alive.ProcessId)" } else { "NO_PROCESS" }
  Add-Content $log "$ts LOCAL_TICK $status last_phase=$phase :: $tail"
  if (-not $alive) {
    $et = if (Test-Path $err) { (Get-Content $err -Tail 15) -join " | " } else { "" }
    Add-Content $log "$ts LOCAL_EXIT_NO_PROCESS err_tail=$et"
    break
  }
  Start-Sleep -Seconds 180
}
