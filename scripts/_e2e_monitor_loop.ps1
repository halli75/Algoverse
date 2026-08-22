$log = "C:\Users\arnav\Projects\algoverse\docs\e2e-monitor.log"
while ($true) {
  $ts = Get-Date -Format o
  Add-Content $log "$ts AGENT_LOOP_TICK_e2e"
  Start-Sleep -Seconds 180
}
