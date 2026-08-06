nvidia-smi --gpu-reset -i 0
Start-Sleep 3
Get-PnpDevice | Where-Object { $_.FriendlyName -like "*3050*" } | ForEach-Object {
  Disable-PnpDevice -InstanceId $_.InstanceId -Confirm:$false -ErrorAction SilentlyContinue
  Start-Sleep 2
  Enable-PnpDevice -InstanceId $_.InstanceId -Confirm:$false -ErrorAction SilentlyContinue
}
Start-Sleep 5
