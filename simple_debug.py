#!/usr/bin/env python3
"""Simple debug script"""

import os
from app.models.shopify_config_manager import ShopifyConfigManager
from app.models.csv_exporter import ShopifyCSVExporter

def simple_debug():
    """Debug CSV export components"""
    
    print("🔍 Simple Debug...")
    
    # 1. Check designs trong thư mục
    designs_dir = "designs"
    if os.path.exists(designs_dir):
        designs = [f for f in os.listdir(designs_dir) if f.lower().endswith(('.png', '.jpg'))]
        print(f"📂 Designs found: {designs}")
    else:
        print(f"❌ Designs directory not found: {designs_dir}")
        return
    
    # 2. Check output folder structure
    output_folder = "output"
    if os.path.exists(output_folder):
        folders = [item for item in os.listdir(output_folder) if os.path.isdir(os.path.join(output_folder, item))]
        print(f"📁 Output folders: {folders}")
        
        # List files in each folder
        for folder in folders:
            folder_path = os.path.join(output_folder, folder)
            files = os.listdir(folder_path)
            print(f"  {folder}: {files}")
    else:
        print(f"❌ Output directory not found: {output_folder}")
        return
    
    # 3. Test shopify config
    shopify_config = ShopifyConfigManager()
    
    colors = shopify_config.get_colors()
    print(f"🎨 Colors: {colors}")
    
    size_configs = shopify_config.get_active_size_configs()
    print(f"📏 Active size configs: {size_configs}")
    
    if not size_configs:
        print("❌ NO ACTIVE SIZE CONFIGS! This is the problem!")
        return
    
    # 4. Test CSV exporter
    csv_exporter = ShopifyCSVExporter(shopify_config)
    
    # Tạo mock mockup files (format subfolder/filename)
    mockup_files = []
    for folder in folders:
        folder_path = os.path.join(output_folder, folder)
        files = [f for f in os.listdir(folder_path) if f.lower().endswith(('.jpg', '.png'))]
        for file in files:
            mockup_files.append(f"{folder}/{file}")
    
    print(f"🖼️ Mockup files for CSV: {mockup_files}")
    
    # Test với design đầu tiên
    if designs:
        design_name = designs[0]
        print(f"\n🧪 Testing generate_product_data for: {design_name}")
        
        # Mock design handle mapping
        design_handle_mapping = {}
        for i, design in enumerate(designs):
            # Simulate mapping giống như controller tạo
            design_base = os.path.splitext(design)[0]
            handle = f"{design_base.lower().replace(' ', '-')}-test{i:02d}"
            design_handle_mapping[design] = handle
        
        print(f"🏷️ Mock design handle mapping: {design_handle_mapping}")
        
        # Get mockup templates
        mockups_dir = "mockups"
        mockup_templates = []
        if os.path.exists(mockups_dir):
            mockup_templates = [f for f in os.listdir(mockups_dir) if f.lower().endswith(('.jpg', '.png'))]
        
        print(f"📋 Mockup templates: {mockup_templates}")
        
        try:
            product_rows = csv_exporter.generate_product_data(
                design_name, mockup_files, output_folder, 
                mockup_templates, design_handle_mapping
            )
            print(f"✅ Generated {len(product_rows)} product rows")
            
            if product_rows:
                print(f"📝 First row handle: {product_rows[0].get('Handle', 'N/A')}")
                print(f"📝 First row SKU: {product_rows[0].get('Variant SKU', 'N/A')}")
                print(f"📝 First row price: {product_rows[0].get('Variant Price', 'N/A')}")
            else:
                print("❌ No product rows generated!")
                
        except Exception as e:
            print(f"❌ Error generating product data: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    simple_debug() 