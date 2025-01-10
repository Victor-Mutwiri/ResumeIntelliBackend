try:
    from torch import Tensor, device
    print("Import successful")
except ImportError as e:
    print(f"ImportError: {e}")