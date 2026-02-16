
import sys
import os
import unittest
from unittest.mock import patch, MagicMock

# Mock cairo before importing anything that uses it
from unittest.mock import MagicMock
import sys

# Mock cairo since it's a binary dependency often missing locally
mock_cairo = MagicMock()
mock_cairo.ImageSurface.create_from_png.return_value = MagicMock()
mock_cairo.Context.return_value = MagicMock()
sys.modules['cairo'] = mock_cairo

# Mock pytoshop if not present
sys.modules['pytoshop'] = MagicMock()
sys.modules['pytoshop.layers'] = MagicMock()
sys.modules['pytoshop.enums'] = MagicMock()

# Mock numpy
sys.modules['numpy'] = MagicMock()

# Add src to path so we can import compositor
sys.path.append(os.path.join(os.path.dirname(__file__), '../src'))

from compositor.compose import compose_image

class TestPSDFailMode(unittest.TestCase):
    def setUp(self):
        # Paths
        self.base_dir = os.path.dirname(__file__)
        self.test_data_dir = os.path.join(self.base_dir, '../test_data')
        self.output_dir = os.path.join(self.base_dir, '../output')
        
        self.png_path = os.path.join(self.test_data_dir, 'test_image.png')
        self.json_path = os.path.join(self.test_data_dir, 'test_data.json')
        
        # Ensure output dir exists
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Target output path
        self.target_psd = os.path.join(self.output_dir, 'fail_mode_test.psd')
        self.fallback_png = os.path.join(self.output_dir, 'fail_mode_test.png')
        
        # Cleanup before test
        if os.path.exists(self.target_psd): os.remove(self.target_psd)
        if os.path.exists(self.fallback_png): os.remove(self.fallback_png)

        if not os.path.exists(self.png_path):
            with open(self.png_path, 'wb') as f:
                f.write(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c\x48\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82')
            
        if not os.path.exists(self.json_path):
            import json
            with open(self.json_path, 'w') as f:
                json.dump({"matrices": {}, "viewport": {"width": 100, "height": 100}}, f)

    def test_fail_mode_fallback(self):
        print("\n--- Testing PSD Fail Mode ---")
        
        # Mocking psd_export to fail
        # Also mock _export_flat_png so we don't need real cairo for the fallback
        with patch('compositor.psd_export.export_psd', side_effect=RuntimeError("Simulated PSD Explosion")), \
             patch('compositor.compose._export_flat_png') as mock_png_export:
            
            # Side effect for png export: verify it was called and create the file
            def create_png_side_effect(layers, path):
                with open(path, 'w') as f: f.write("dummy png")
            mock_png_export.side_effect = create_png_side_effect

            # Run composition asking for PSD
            compose_image(
                self.png_path,
                self.json_path,
                self.target_psd,
                config_path=None,
                output_format='psd'
            )
            
            # Assertions
            self.assertFalse(os.path.exists(self.target_psd), "PSD file should NOT exist (should be cleaned up)")
            self.assertTrue(os.path.exists(self.fallback_png), "Fallback PNG SHOULD exist")
            
            mock_png_export.assert_called_once()
            print("✅ Verified: PSD failed, cleaned up, and PNG creator called.")

if __name__ == '__main__':
    unittest.main()
