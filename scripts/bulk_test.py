import os
import subprocess

# --- PATH CONFIGURATION ---
# Inside the container:
# /data/shared = n8n-mount/
# property-image-compositor = /data/shared/property-image-compositor
# test_data = /data/shared/test_data

BASE_PATH = "/data/shared/property-image-compositor"
DATA_PATH = "/data/shared/test_data"

# Fallback output: If /data/generated is permission-locked, we use n8n-mount/test_results
OUTPUT_PATH_PRIMARY = "/data/generated/test_results"
OUTPUT_PATH_FALLBACK = "/data/shared/test_results"

# Determine which output path to use
if os.access("/data/generated", os.W_OK):
    OUTPUT_PATH = OUTPUT_PATH_PRIMARY
else:
    print("⚠️  Warning: /data/generated is not writable. Falling back to /data/shared/test_results")
    OUTPUT_PATH = OUTPUT_PATH_FALLBACK

# Ensure output directory exists
os.makedirs(OUTPUT_PATH, exist_ok=True)

views = ["north", "east", "south", "west", "nadir"]

print(f"--- Starting Bulk Composition Test ---")
print(f"Inputs: {DATA_PATH}")
print(f"Outputs: {OUTPUT_PATH}")

for view in views:
    png = os.path.join(DATA_PATH, f"{view}.png")
    json_data = os.path.join(DATA_PATH, f"{view}.json")
    output = os.path.join(OUTPUT_PATH, f"final_{view}.png")
    
    if not os.path.exists(png) or not os.path.exists(json_data):
        print(f"   - {view}: ⚠️  Missing .png or .json")
        continue
        
    print(f"🚀 Processing {view}...")
    
    # Run the compose script
    cmd = [
        "python3", "-m", "src.compositor.compose",
        "--png", png,
        "--json", json_data,
        "--output", output
    ]
    
    # Set PYTHONPATH so the internal imports work correctly
    env = os.environ.copy()
    env["PYTHONPATH"] = f"{BASE_PATH}:{env.get('PYTHONPATH', '')}"
    
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=BASE_PATH, env=env)
    
    if result.returncode == 0:
        print(f"   - {view}: ✅ Success")
    else:
        print(f"   - {view}: ❌ Failed")
        print(f"     Error: {result.stderr}")

print("--- Test Complete ---")
