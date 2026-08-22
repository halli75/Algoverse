import torch, os
print("exe", __import__("sys").executable)
print("cuda_avail", torch.cuda.is_available())
print("count", torch.cuda.device_count())
print("CUDA_VISIBLE_DEVICES", os.environ.get("CUDA_VISIBLE_DEVICES"))
if torch.cuda.is_available():
    print("name", torch.cuda.get_device_name(0))
    x = torch.zeros(1, device="cuda")
    print("alloc_ok", x.device)
