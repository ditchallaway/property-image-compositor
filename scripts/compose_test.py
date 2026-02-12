#!/usr/bin/env python3
"""
Local test harness for compositor development.
Processes test_data/raw/*.{png,json} and outputs to output/
"""
import os
import sys

# Ensure the compositor module is importable
sys.path.insert(0, '/app')

from src.compositor.compose import compose_image

def main():
    test_dir = "/app/test_data/raw"
    output_dir = "/app/output"
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Check if test directory exists
    if not os.path.exists(test_dir):
        print(f"❌ Test directory not found: {test_dir}")
        print(f"Please create test_data/raw/ and add PNG+JSON pairs from the renderer")
        return 1
    
    # Find all PNG files
    png_files = sorted([f for f in os.listdir(test_dir) if f.endswith('.png')])
    
    if not png_files:
        print(f"❌ No PNG files found in {test_dir}")
        return 1
    
    print(f"--- Compositor Test Harness ---")
    print(f"Inputs: {test_dir}")
    print(f"Outputs: {output_dir}\n")
    
    success_count = 0
    fail_count = 0
    
    for png_file in png_files:
        base = png_file.replace('.png', '')
        json_file = f"{base}.json"
        
        png_path = os.path.join(test_dir, png_file)
        json_path = os.path.join(test_dir, json_file)
        output_path = os.path.join(output_dir, f"composed_{png_file}")
        
        if not os.path.exists(json_path):
            print(f"⚠️  {base}: Missing JSON sidecar")
            fail_count += 1
            continue
            
        try:
            print(f"🚀 Processing {base}...")
            compose_image(png_path, json_path, output_path)
            print(f"   ✅ Success: {output_path}\n")
            success_count += 1
        except Exception as e:
            print(f"   ❌ Failed: {str(e)}\n")
            fail_count += 1
    
    print(f"--- Test Complete ---")
    print(f"✅ Success: {success_count}")
    print(f"❌ Failed: {fail_count}")
    
    return 0 if fail_count == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
