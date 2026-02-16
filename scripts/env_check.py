import sys
import json
import os

print("--- n8n Runner Environment Check ---")
print(f"Python Version: {sys.version}")

try:
    import numpy as np
    print(f"✅ NumPy: {np.__version__}")
except ImportError:
    print("❌ NumPy: NOT FOUND")

try:
    from PIL import Image
    print(f"✅ Pillow: {Image.__version__ if hasattr(Image, '__version__') else 'Installed'}")
except ImportError:
    print("❌ Pillow: NOT FOUND")

try:
    import cairocffi as cairo
    print(f"✅ PyCairo (cairocffi): {cairo.version if hasattr(cairo, 'version') else 'Installed'}")
except ImportError:
    try:
        import cairo
        print(f"✅ PyCairo: {cairo.version if hasattr(cairo, 'version') else 'Installed'}")
    except ImportError:
        print("❌ PyCairo: NOT FOUND")

try:
    import pytoshop
    print(f"✅ Pytoshop: {pytoshop.__version__ if hasattr(pytoshop, '__version__') else 'Installed'}")
except ImportError:
    print("❌ Pytoshop: NOT FOUND")

# Check mount access
shared_path = "/data/shared"
if os.path.exists(shared_path):
    print(f"✅ Mount /data/shared: EXISTS")
    print(f"   Contents: {os.listdir(shared_path)[:5]}")
else:
    print(f"❌ Mount /data/shared: NOT FOUND")

print("--- End Check ---")
