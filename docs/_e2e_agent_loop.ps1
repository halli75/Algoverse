# Emits AGENT_LOOP_TICK_e2e every 20 minutes for the Cursor agent.
$ErrorActionPreference = "Continue"
$out = "C:\Users\arnav\Projects\algoverse\docs\e2e_agent_loop.out.log"
$prompt = @'
E2E 20m check: verify pipeline/guardian alive; read docs/e2e-local-run.log tail, docs/e2e_heartbeat.json, docs/e2e_results.json, docs/e2e-monitor.log; compare pace to read-only-affect plan (order 2->3->4->1->5->6->7); detect hang (hb>25m); if hung intervene via guardian or kill+smart fix; append status to docs/e2e_run_journal.md; do NOT stop until finished+E2E_COMPLETE and verified solid headline/phases (C_validate_r, D decision, ratios finite, later phases or STOP); Demand elegance; record everything.
'@
$payload = (@{ prompt = $prompt } | ConvertTo-Json -Compress)
while ($true) {
  Start-Sleep -Seconds 1200
  $line = "AGENT_LOOP_TICK_e2e $payload"
  Add-Content -Path $out -Value $line
  Write-Output $line
}
