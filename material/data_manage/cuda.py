import torch

# Check version CUDA yang PyTorch guna
print(f"PyTorch CUDA Version: {torch.version.cuda}")

# Check adakah CUDA boleh digunakan?
print(f"CUDA Available: {torch.cuda.is_available()}")

# Check nama GPU
if torch.cuda.is_available():
    print(f"GPU Name: {torch.cuda.get_device_name(0)}")