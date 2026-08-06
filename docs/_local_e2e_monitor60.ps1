$log='C:\Users\arnav\Projects\algoverse\docs\e2e-monitor.log'
$run='C:\Users\arnav\Projects\algoverse\docs\e2e-local-run.log'
$err='C:\Users\arnav\Projects\algoverse\docs\e2e-local-run.err.log'
$res='C:\Users\arnav\Projects\algoverse\docs\e2e_results.json'
$t=7384
while($true){
  $ts=(Get-Date).ToString('o')
  $alive=Get-Process -Id $t -EA SilentlyContinue
  $tail=if(Test-Path $run){(Get-Content $run -Tail 4)-join' || '}else{''}
  $phase='?'; $done=$false
  if(Test-Path $res){ try{ $j=Get-Content $res -Raw|ConvertFrom-Json; $phase=($j.phases.PSObject.Properties.Name|Select-Object -Last 1); if($j.finished){$done=$true} }catch{} }
  if($done){ Add-Content $log "$ts LOCAL_E2E_COMPLETE phase=$phase"; break }
  if(-not $alive){ $et=if(Test-Path $err){((Get-Content $err -Tail 40)|?{$_ -match 'Error|Traceback|OOM|Exception'}) -join ' || '}else{''}; Add-Content $log "$ts LOCAL_DEAD pid=$t err=$et"; break }
  Add-Content $log "$ts LOCAL60 RUNNING pid=$t phase=$phase :: $tail"
  Start-Sleep 60
}
