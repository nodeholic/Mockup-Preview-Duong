import csv
import os
from typing import List, Dict, Any
from .shopify_config_manager import ShopifyConfigManager

class ShopifyCSVExporter:
    def __init__(self, shopify_config: ShopifyConfigManager):
        self.shopify_config = shopify_config

    def get_shopify_headers(self) -> List[str]:
        """Trả về headers chuẩn cho Shopify CSV giống file mẫu"""
        return [
            "Handle", "Title", "Body (HTML)", "Vendor", "Product Category", "Type",
            "Tags", "Published", "Option1 Name", "Option1 Value", "Option1 Linked To",
            "Option2 Name", "Option2 Value", "Option2 Linked To", "Option3 Name", 
            "Option3 Value", "Option3 Linked To", "Variant SKU", "Variant Grams", 
            "Variant Inventory Tracker", "Variant Inventory Policy", "Variant Fulfillment Service", 
            "Variant Price", "Variant Compare At Price", "Variant Requires Shipping", 
            "Variant Taxable", "Variant Barcode", "Image Src", "Image Position", 
            "Image Alt Text", "Gift Card", "SEO Title", "SEO Description", 
            "Google Shopping / Google Product Category", "Google Shopping / Gender", 
            "Google Shopping / Age Group", "Google Shopping / MPN", 
            "Google Shopping / Condition", "Google Shopping / Custom Product",
            "Google Shopping / Custom Label 0", "Google Shopping / Custom Label 1",
            "Google Shopping / Custom Label 2", "Google Shopping / Custom Label 3",
            "Google Shopping / Custom Label 4", "Case type (product.metafields.custom.case_type)",
            "Google: Custom Product (product.metafields.custom.google_custom_product)",
            "Product rating count (product.metafields.custom.product_rating_count)",
            "Mobile phone case features (product.metafields.shopify.mobile-phone-case-features)",
            "Variant Image", "Variant Weight Unit", "Variant Tax Code", "Cost per item", "Status"
        ]

    def generate_product_data(self, design_name: str, mockup_files: List[str], 
                            output_folder: str, mockup_templates: List[str] = None,
                            design_handle_mapping: dict = None) -> List[Dict[str, Any]]:
        """Tạo dữ liệu sản phẩm cho một design - chỉ tạo variants cho sizes có price"""
        business_info = self.shopify_config.get_business_info()
        colors = self.shopify_config.get_colors()
        # Chỉ lấy sizes có price khác rỗng
        size_configs = self.shopify_config.get_active_size_configs()
        
        if not size_configs:
            print(f"Warning: No active size configs found for {design_name}")
            return []
        
        # Loại bỏ extension từ design name để làm handle
        design_base = os.path.splitext(design_name)[0]
        
        # Sử dụng handle từ mapping nếu có, nếu không thì tạo mới
        if design_handle_mapping and design_name in design_handle_mapping:
            handle = design_handle_mapping[design_name]
            print(f"Using existing handle for {design_name}: {handle}")
            # Extract random string từ handle để dùng cho SKU
            # Handle format: "design-name-randomstring"
            handle_parts = handle.split('-')
            if len(handle_parts) >= 2:
                product_random_string = handle_parts[-1]  # Lấy phần cuối
            else:
                # Fallback nếu format không đúng
                product_random_string = self.shopify_config.generate_random_string(10)
        else:
            # Fallback: tạo random string mới
            product_random_string = self.shopify_config.generate_random_string(10)
            handle = f"{design_base.lower().replace(' ', '-').replace('_', '-')}-{product_random_string}"
            print(f"Generated new handle for {design_name}: {handle}")
        
        # Tìm đúng images tương ứng với mockup templates cho design này
        image_domain = self.shopify_config.get_image_domain()
        matching_images = []
        
        if mockup_templates:
            # Lấy đúng 1 image cho mỗi mockup template
            for template in mockup_templates:
                template_base = os.path.splitext(template)[0]  # Tên template không có extension
                
                # Tìm image file tương ứng trong output (có thể ở subfolder)
                for mockup_file in mockup_files:
                    # mockup_file có thể là "subfolder/filename.jpg" hoặc "filename.jpg"
                    filename = os.path.basename(mockup_file)
                    filename_base = os.path.splitext(filename)[0]
                    
                    # Check if this file name matches template name (since file name is now just mockup name)
                    if template_base.lower() == filename_base.lower():
                        
                        # Tạo link ảnh với domain nếu có
                        if image_domain:
                            # URL format: domain/handle/filename
                            image_url = f"{image_domain.rstrip('/')}/{handle}/{filename}"
                        else:
                            # Giữ full path cho local files
                            if "/" in mockup_file:
                                # File trong subfolder
                                image_url = os.path.join(output_folder, mockup_file).replace("\\", "/")
                            else:
                                # File ở root
                                image_url = os.path.join(output_folder, mockup_file).replace("\\", "/")
                        
                        matching_images.append(image_url)
                        break  # Chỉ lấy 1 image đầu tiên match cho template này
        
        if matching_images:
            print(f"Found {len(matching_images)} images for design '{design_base}' (expected: {len(mockup_templates) if mockup_templates else 'unknown'})")
        
        rows = []
        variant_position = 1
        
        for color in colors:
            for size in size_configs.keys():
                # Tạo SKU với random string chung của product này
                sku = self.generate_sku_with_fixed_random(design_base, color, size, product_random_string)
                
                # Tạo description
                description = self.shopify_config.generate_description(design_base, color, size)
                
                # Lấy giá
                price, compare_price = self.shopify_config.get_price_for_size(size)
                
                # Tạo product title
                product_title = f"{design_base} - {business_info.get('product_type', 'T-Shirt')}"
                
                # Xác định image cho dòng này (độc lập với variation)
                # Dòng 1 -> Image 1, Dòng 2 -> Image 2, etc.
                row_image_index = variant_position - 1  # 0-based index
                image_src = ""
                image_position = ""
                # image_alt = ""
                
                if row_image_index < len(matching_images):
                    image_src = matching_images[row_image_index]
                    image_position = str(row_image_index + 1)  # 1-based position
                    # image_alt = f"Image {row_image_index + 1} for {design_base}"
                
                # Tạo row data theo format mẫu
                row = {
                    "Handle": handle,
                    "Title": product_title if variant_position == 1 else "",
                    "Body (HTML)": f'<p>{description}</p>' if variant_position == 1 else "",
                    "Vendor": business_info.get("vendor", "") if variant_position == 1 else "",
                    "Product Category": "",
                    "Type": business_info.get("product_type", "") if variant_position == 1 else "",
                    "Tags": business_info.get("tags", "") if variant_position == 1 else "",
                    "Published": "TRUE" if variant_position == 1 else "",
                    "Option1 Name": "Size" if variant_position == 1 else "",
                    "Option1 Value": size,
                    "Option1 Linked To": "",
                    "Option2 Name": "Color" if variant_position == 1 else "",
                    "Option2 Value": color,
                    "Option2 Linked To": "",
                    "Option3 Name": "",
                    "Option3 Value": "",
                    "Option3 Linked To": "",
                    "Variant SKU": sku,
                    "Variant Grams": "100",  # Default weight
                    "Variant Inventory Tracker": "",
                    "Variant Inventory Policy": "continue",
                    "Variant Fulfillment Service": "printify",
                    "Variant Price": price,
                    "Variant Compare At Price": compare_price if compare_price else "",
                    "Variant Requires Shipping": "TRUE",
                    "Variant Taxable": "TRUE",
                    "Variant Barcode": "",
                    "Image Src": image_src,
                    "Image Position": image_position,
                    # "Image Alt Text": image_alt,
                    "Gift Card": "FALSE",
                    "SEO Title": "",
                    "SEO Description": "",
                    "Google Shopping / Google Product Category": "",
                    "Google Shopping / Gender": "",
                    "Google Shopping / Age Group": "",
                    "Google Shopping / MPN": "",
                    "Google Shopping / Condition": "new",
                    "Google Shopping / Custom Product": "",
                    "Google Shopping / Custom Label 0": "",
                    "Google Shopping / Custom Label 1": "",
                    "Google Shopping / Custom Label 2": "",
                    "Google Shopping / Custom Label 3": "",
                    "Google Shopping / Custom Label 4": "",
                    "Case type (product.metafields.custom.case_type)": "",
                    "Google: Custom Product (product.metafields.custom.google_custom_product)": "",
                    "Product rating count (product.metafields.custom.product_rating_count)": "",
                    "Mobile phone case features (product.metafields.shopify.mobile-phone-case-features)": "",
                    "Variant Image": "",
                    "Variant Weight Unit": "lb",
                    "Variant Tax Code": "",
                    "Cost per item": "",
                    "Status": "active" if variant_position == 1 else ""
                }
                
                rows.append(row)
                variant_position += 1
        
        return rows

    def generate_sku_with_fixed_random(self, design_name: str, color: str, size: str, random_string: str) -> str:
        """Tạo SKU với random string đã cho trước"""
        pattern = self.shopify_config.get_sku_pattern()
        size_config = self.shopify_config.get_size_configs().get(size, {})
        sku_suffix = size_config.get("sku_suffix", size)
        
        return pattern.format(
            randomstring=random_string,
            design=design_name.lower().replace(" ", "-"),
            color=color.replace(" ", ""),
            size=sku_suffix
        )

    def export_csv(self, design_names: List[str], mockup_files: List[str], 
                   output_folder: str, csv_filename: str = "shopify_products.csv",
                   mockup_templates: List[str] = None, design_handle_mapping: dict = None) -> str:
        """Xuất CSV cho tất cả designs"""
        csv_path = os.path.join(output_folder, csv_filename)
        
        try:
            with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                headers = self.get_shopify_headers()
                writer = csv.DictWriter(csvfile, fieldnames=headers)
                writer.writeheader()
                
                for design_name in design_names:
                    product_rows = self.generate_product_data(
                        design_name, mockup_files, output_folder, 
                        mockup_templates, design_handle_mapping
                    )
                    for row in product_rows:
                        writer.writerow(row)
            
            print(f"Shopify CSV exported successfully to: {csv_path}")
            return csv_path
            
        except Exception as e:
            print(f"Error exporting CSV: {e}")
            raise e

    def preview_csv_data(self, design_names: List[str], mockup_files: List[str], 
                        output_folder: str, max_rows: int = 10,
                        mockup_templates: List[str] = None, design_handle_mapping: dict = None) -> List[Dict[str, Any]]:
        """Xem trước dữ liệu CSV (để hiển thị trong UI)"""
        preview_data = []
        row_count = 0
        
        for design_name in design_names:
            if row_count >= max_rows:
                break
                
            product_rows = self.generate_product_data(
                design_name, mockup_files, output_folder, 
                mockup_templates, design_handle_mapping
            )
            for row in product_rows:
                if row_count >= max_rows:
                    break
                preview_data.append(row)
                row_count += 1
        
        return preview_data

    def get_export_summary(self, design_names: List[str]) -> Dict[str, int]:
        """Lấy thống kê về số lượng sản phẩm sẽ được tạo"""
        colors = self.shopify_config.get_colors()
        # Chỉ đếm sizes có price
        active_sizes = list(self.shopify_config.get_active_size_configs().keys())
        
        total_variants = len(design_names) * len(colors) * len(active_sizes)
        
        return {
            "total_designs": len(design_names),
            "total_colors": len(colors),
            "total_sizes": len(active_sizes),
            "total_variants": total_variants,
            "total_products": len(design_names)
        } 