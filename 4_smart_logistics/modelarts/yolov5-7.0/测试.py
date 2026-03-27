import torch
print(torch.__version__)

print("Is CUDA available", torch.cuda.is_available())
print("CUDA version: ",torch.version.cuda )
