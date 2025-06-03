#!/usr/bin/env python3
"""Test export CSV directly"""

import os
from app.models.shopify_config_manager import ShopifyConfigManager
from app.models.csv_exporter import ShopifyCSVExporter

def test_export_csv():
    """Test export CSV với data có sẵn"""
    
    output_folder = "output"
    designs = ['thiet ke 01.png', 'thiet ke 02.jpg', 'thiet ke 03.jpg']
    
    # Tạo design handle mapping giống controller
    design_handle_mapping = {
        'thiet ke 01.png': 'thiet-ke-01-z69uq8nrad',
        'thiet ke 02.jpg': 'thiet-ke-02-3ikecfcunt', 
        'thiet ke 03.jpg': 'thiet-ke-03-ccjpmmzjxf'
    }
    
    # Get mockup files
    mockup_files = []
    for folder in ['thiet-ke-01-z69uq8nrad', 'thiet-ke-02-3ikecfcunt', 'thiet-ke-03-ccjpmmzjxf']:
        folder_path = os.path.join(output_folder, folder)
        if os.path.exists(folder_path):
            files = os.listdir(folder_path)
            for file in files:
                if file.lower().endswith(('.jpg', '.png')):
                    mockup_files.append(f"{folder}/{file}")
    
    print(f"📂 Designs: {designs}")
    print(f"🖼️ Mockup files: {mockup_files}")
    print(f"🏷️ Handle mapping: {design_handle_mapping}")
    
    # Get mockup templates
    mockup_templates = ['Mk1.jpg', 'Mk2.jpg', 'Mk3.jpg', 'Mk4.jpg']
    
    # Test export
    shopify_config = ShopifyConfigManager()
    csv_exporter = ShopifyCSVExporter(shopify_config)
    
    try:
        csv_path = csv_exporter.export_csv(
            designs, mockup_files, output_folder,
            mockup_templates=mockup_templates,
            design_handle_mapping=design_handle_mapping
        )
        print(f"✅ CSV exported to: {csv_path}")
        
        # Check file size
        if os.path.exists(csv_path):
            size = os.path.getsize(csv_path)
            print(f"📊 CSV file size: {size} bytes")
            
            # Count lines
            with open(csv_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                print(f"📄 CSV lines: {len(lines)} (including header)")
                
                if len(lines) > 1:
                    print(f"✅ CSV has data!")
                    # Show first data line
                    if len(lines) > 1:
                        print(f"📝 First data line (first 100 chars): {lines[1][:100]}...")
                else:
                    print(f"❌ CSV only has header!")
        
    except Exception as e:
        print(f"❌ Export error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_export_csv() 