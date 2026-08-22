$tick = 0
while ($true) {
  $tick++
  $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
  $line = "AGENT_LOOP_TICK_publish #$tick $ts"
  Add-Content -Path "C:\Users\arnav\Projects\algoverse\.agent_publish_loop.log" -Value $line
  Write-Output $line
  Start-Sleep -Seconds 900
}
