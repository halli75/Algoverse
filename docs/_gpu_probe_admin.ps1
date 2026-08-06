$out = "C:\Users\arnav\Projects\algoverse\docs\_gpu_status.txt"
try {
  $smi = & nvidia-smi --query-gpu=name,driver_version,memory.total,memory.free --format=csv 2>&1 | Out-String
} catch { $smi = "$_" }
Add-Content $out ("==== " + (Get-Date).ToString('o') + " ====")
Add-Content $out $smi
try {
  Get-PnpDevice | Where-Object { $_.FriendlyName -match 'NVIDIA|3050' } | ForEach-Object {
    Add-Content $out ("PNP " + $_.Status + " | " + $_.FriendlyName)
    if ($_.Status -ne 'OK') {
      try { Enable-PnpDevice -InstanceId $_.InstanceId -Confirm:$false -ErrorAction Stop; Add-Content $out "enabled" } catch { Add-Content $out ("enable fail: " + $_) }
    }
  }
} catch { Add-Content $out ("pnp err " + $_) }
try { & nvidia-smi --gpu-reset -i 0 2>&1 | Out-String | Add-Content $out } catch { Add-Content $out ("reset " + $_) }
Start-Sleep 5
try { & nvidia-smi --query-gpu=name,memory.free --format=csv 2>&1 | Out-String | Add-Content $out } catch {}
