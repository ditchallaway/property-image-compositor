#!/usr/bin/env python3
"""
Local test harness for compositor development.
Processes test_data/raw/*.{png,json} and outputs to output/

Supports --format png|psd|both to test different output modes.
"""
import os
import sys
import argparse

# Ensure the compositor module is importable
sys.path.insert(0, '/app')

from src.compositor.compose import compose_image


def main():
    parser = argparse.ArgumentParser(description="Compositor Test Harness")
    parser.add_argument("--format", default="both", choices=["png", "psd", "both"],
                        help="Output format (default: both)")
    parser.add_argument("--view", default=None,
                        help="Process only a specific view (e.g., 'west')")
    parser.add_argument("--stage", type=int, default=2,
                        help="Rendering stage: 1=lines only, 2=full (default: 2)")
    args = parser.parse_args()

    test_dir = "/app/test_data/raw"
    output_dir = "/app/output"
    os.makedirs(output_dir, exist_ok=True)

    if not os.path.exists(test_dir):
        print(f"❌ Test directory not found: {test_dir}")
        print(f"Please create test_data/raw/ and add PNG+JSON pairs from the renderer")
        return 1

    # Find all PNG files
    png_files = sorted([f for f in os.listdir(test_dir) if f.endswith('.png')])

    if args.view:
        png_files = [f for f in png_files if f.replace('.png', '') == args.view]

    if not png_files:
        print(f"❌ No PNG files found in {test_dir}")
        return 1

    print(f"--- Compositor Test Harness ---")
    print(f"Inputs: {test_dir}")
    print(f"Outputs: {output_dir}")
    print(f"Format: {args.format}")
    print(f"Stage: {args.stage}\n")

    success_count = 0
    fail_count = 0

    for png_file in png_files:
        base = png_file.replace('.png', '')
        json_file = f"{base}.json"

        png_path = os.path.join(test_dir, png_file)
        json_path = os.path.join(test_dir, json_file)

        # Determine output path
        if args.format == 'psd':
            output_path = os.path.join(output_dir, f"composed_{base}.psd")
        else:
            output_path = os.path.join(output_dir, f"composed_{base}.png")

        if not os.path.exists(json_path):
            print(f"⚠️  {base}: Missing JSON sidecar")
            fail_count += 1
            continue

        try:
            print(f"🚀 Processing {base}...")
            compose_image(png_path, json_path, output_path,
                          output_format=args.format, stage=args.stage)
            print(f"   ✅ Success: {output_path}\n")
            success_count += 1
        except Exception as e:
            import traceback
            print(f"   ❌ Failed: {str(e)}")
            traceback.print_exc()
            print()
            fail_count += 1

    print(f"--- Test Complete ---")
    print(f"✅ Success: {success_count}")
    print(f"❌ Failed: {fail_count}")

    return 0 if fail_count == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
