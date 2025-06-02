import csv
import os
from typing import List, Dict, Any
from .shopify_config_manager import ShopifyConfigManager

class ShopifyCSVExporter:
    def __init__(self, shopify_config: ShopifyConfigManager):
        self.shopify_config = shopify_config

    def get_shopify_headers(self) -> List[str]:
        """Trả về headers chuẩn cho Shopify CSV"""
        return [
            "Handle", "Title", "Body (HTML)", "Vendor", "Product Category", "Type",
            "Tags", "Published", "Option1 Name", "Option1 Value", "Option2 Name", 
            "Option2 Value", "Option3 Name", "Option3 Value", "Variant SKU",
            "Variant Grams", "Variant Inventory Tracker", "Variant Inventory Qty",
            "Variant Inventory Policy", "Variant Fulfillment Service", "Variant Price",
            "Variant Compare At Price", "Variant Requires Shipping", "Variant Taxable",
            "Variant Barcode", "Image Src", "Image Position", "Image Alt Text",
            "Gift Card", "SEO Title", "SEO Description", "Google Shopping / Google Product Category",
            "Google Shopping / Gender", "Google Shopping / Age Group", "Google Shopping / MPN",
            "Google Shopping / AdWords Grouping", "Google Shopping / AdWords Labels",
            "Google Shopping / Condition", "Google Shopping / Custom Product",
            "Google Shopping / Custom Label 0", "Google Shopping / Custom Label 1",
            "Google Shopping / Custom Label 2", "Google Shopping / Custom Label 3",
            "Google Shopping / Custom Label 4", "Variant Image", "Variant Weight Unit",
            "Variant Tax Code", "Cost per item", "Status"
        ]

    def generate_product_data(self, design_name: str, mockup_files: List[str], 
                            output_folder: str) -> List[Dict[str, Any]]:
        """Tạo dữ liệu sản phẩm cho một design"""
        business_info = self.shopify_config.get_business_info()
        colors = self.shopify_config.get_colors()
        size_configs = self.shopify_config.get_size_configs()
        
        # Loại bỏ extension từ design name để làm handle
        design_base = os.path.splitext(design_name)[0]
        handle = design_base.lower().replace(" ", "-").replace("_", "-")
        
        rows = []
        variant_position = 1
        
        for color in colors:
            for size in size_configs.keys():
                # Tạo SKU
                sku = self.shopify_config.generate_sku(design_base, color, size)
                
                # Tạo description
                description = self.shopify_config.generate_description(design_base, color, size)
                
                # Lấy giá
                price, compare_price = self.shopify_config.get_price_for_size(size)
                
                # Tạo product title
                product_title = f"{design_base} - {business_info.get('product_type', 'T-Shirt')}"
                
                # Tìm image tương ứng với design này
                image_src = ""
                for mockup_file in mockup_files:
                    if design_base.lower() in mockup_file.lower():
                        # Tạo đường dẫn tương đối từ output folder
                        image_src = os.path.join(output_folder, mockup_file).replace("\\", "/")
                        break
                
                # Tạo row data
                row = {
                    "Handle": handle,
                    "Title": product_title if variant_position == 1 else "",
                    "Body (HTML)": description if variant_position == 1 else "",
                    "Vendor": business_info.get("vendor", "") if variant_position == 1 else "",
                    "Product Category": "",
                    "Type": business_info.get("product_type", "") if variant_position == 1 else "",
                    "Tags": business_info.get("tags", "") if variant_position == 1 else "",
                    "Published": "TRUE" if variant_position == 1 else "",
                    "Option1 Name": "Color" if variant_position == 1 else "",
                    "Option1 Value": color,
                    "Option2 Name": "Size" if variant_position == 1 else "",
                    "Option2 Value": size,
                    "Option3 Name": "",
                    "Option3 Value": "",
                    "Variant SKU": sku,
                    "Variant Grams": "200",  # Default weight
                    "Variant Inventory Tracker": "shopify",
                    "Variant Inventory Qty": "100",  # Default quantity
                    "Variant Inventory Policy": "deny",
                    "Variant Fulfillment Service": "manual",
                    "Variant Price": price,
                    "Variant Compare At Price": compare_price,
                    "Variant Requires Shipping": "TRUE",
                    "Variant Taxable": "TRUE",
                    "Variant Barcode": "",
                    "Image Src": image_src if variant_position == 1 else "",
                    "Image Position": "1" if variant_position == 1 else "",
                    "Image Alt Text": f"{product_title}" if variant_position == 1 else "",
                    "Gift Card": "FALSE",
                    "SEO Title": "",
                    "SEO Description": "",
                    "Google Shopping / Google Product Category": "",
                    "Google Shopping / Gender": "",
                    "Google Shopping / Age Group": "",
                    "Google Shopping / MPN": "",
                    "Google Shopping / AdWords Grouping": "",
                    "Google Shopping / AdWords Labels": "",
                    "Google Shopping / Condition": "new",
                    "Google Shopping / Custom Product": "",
                    "Google Shopping / Custom Label 0": "",
                    "Google Shopping / Custom Label 1": "",
                    "Google Shopping / Custom Label 2": "",
                    "Google Shopping / Custom Label 3": "",
                    "Google Shopping / Custom Label 4": "",
                    "Variant Image": "",
                    "Variant Weight Unit": "g",
                    "Variant Tax Code": "",
                    "Cost per item": "",
                    "Status": "active" if variant_position == 1 else ""
                }
                
                rows.append(row)
                variant_position += 1
        
        return rows

    def export_csv(self, design_names: List[str], mockup_files: List[str], 
                   output_folder: str, csv_filename: str = "shopify_products.csv") -> str:
        """Xuất CSV cho tất cả designs"""
        csv_path = os.path.join(output_folder, csv_filename)
        
        try:
            with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                headers = self.get_shopify_headers()
                writer = csv.DictWriter(csvfile, fieldnames=headers)
                writer.writeheader()
                
                for design_name in design_names:
                    product_rows = self.generate_product_data(design_name, mockup_files, output_folder)
                    for row in product_rows:
                        writer.writerow(row)
            
            print(f"Shopify CSV exported successfully to: {csv_path}")
            return csv_path
            
        except Exception as e:
            print(f"Error exporting CSV: {e}")
            raise e

    def preview_csv_data(self, design_names: List[str], mockup_files: List[str], 
                        output_folder: str, max_rows: int = 10) -> List[Dict[str, Any]]:
        """Xem trước dữ liệu CSV (để hiển thị trong UI)"""
        preview_data = []
        row_count = 0
        
        for design_name in design_names:
            if row_count >= max_rows:
                break
                
            product_rows = self.generate_product_data(design_name, mockup_files, output_folder)
            for row in product_rows:
                if row_count >= max_rows:
                    break
                preview_data.append(row)
                row_count += 1
        
        return preview_data

    def get_export_summary(self, design_names: List[str]) -> Dict[str, int]:
        """Lấy thống kê về số lượng sản phẩm sẽ được tạo"""
        colors = self.shopify_config.get_colors()
        sizes = list(self.shopify_config.get_size_configs().keys())
        
        total_variants = len(design_names) * len(colors) * len(sizes)
        
        return {
            "total_designs": len(design_names),
            "total_colors": len(colors),
            "total_sizes": len(sizes),
            "total_variants": total_variants,
            "total_products": len(design_names)
        } 