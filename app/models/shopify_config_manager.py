import json
import os
import string
import random
from typing import Dict, List, Any

class ShopifyConfigManager:
    def __init__(self, config_path="data/shopify_config.json"):
        self.config_path = config_path
        self.config_data = {}
        # Đảm bảo thư mục data tồn tại
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        self.load_config()

    def load_config(self):
        """Load Shopify configuration từ file"""
        print(f"Loading Shopify config from {self.config_path}")
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config_data = json.load(f)
        except FileNotFoundError:
            print(f"Shopify config file {self.config_path} not found. Creating default config.")
            self.config_data = self.get_default_config()
            self.save_config()
        except json.JSONDecodeError:
            print(f"Error decoding JSON from {self.config_path}. Using default config.")
            self.config_data = self.get_default_config()
        except Exception as e:
            print(f"An unexpected error occurred while loading Shopify config: {e}")
            self.config_data = self.get_default_config()

    def save_config(self):
        """Lưu Shopify configuration vào file"""
        print(f"Saving Shopify config to {self.config_path}")
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config_data, f, indent=4, ensure_ascii=False)
            print("Shopify config saved successfully.")
        except IOError as e:
            print(f"Error writing to Shopify config file {self.config_path}: {e}")
        except Exception as e:
            print(f"An unexpected error occurred while saving Shopify config: {e}")

    def generate_random_string(self, length=10):
        """Tạo random string gồm chữ và số"""
        characters = string.ascii_lowercase + string.digits
        return ''.join(random.choice(characters) for _ in range(length))

    def get_default_config(self) -> Dict[str, Any]:
        """Trả về cấu hình Shopify mặc định với 9 sizes"""
        return {
            "business_info": {
                "vendor": "Your Business Name",
                "product_type": "T-Shirt",
                "tags": "custom, print, design"
            },
            "size_configs": {
                "XS": {"price": "19.99", "compare_price": "", "sku_suffix": "XS"},
                "S": {"price": "19.99", "compare_price": "", "sku_suffix": "S"},
                "M": {"price": "19.99", "compare_price": "", "sku_suffix": "M"},
                "L": {"price": "19.99", "compare_price": "", "sku_suffix": "L"},
                "XL": {"price": "19.99", "compare_price": "", "sku_suffix": "XL"},
                "2XL": {"price": "20.99", "compare_price": "", "sku_suffix": "2XL"},
                "3XL": {"price": "21.99", "compare_price": "", "sku_suffix": "3XL"},
                "4XL": {"price": "22.99", "compare_price": "", "sku_suffix": "4XL"},
                "5XL": {"price": "23.99", "compare_price": "", "sku_suffix": "5XL"}
            },
            "colors": ["Charcoal", "Dark Heather", "Navy", "Red", "Royal", "Sport Grey", "Black", "Forest Green", "Purple", "Maroon", "Sand"],
            "sku_pattern": "{randomstring}-{color}-{size}",
            "description_template": """High-quality {product_type} with custom {design} design.

Features:
- Premium material
- Comfortable fit
- Durable print
- Available in multiple sizes and colors

Size: {size}
Color: {color}"""
        }

    def get_business_info(self) -> Dict[str, str]:
        """Lấy thông tin business"""
        return self.config_data.get("business_info", {})

    def update_business_info(self, vendor: str, product_type: str, tags: str):
        """Cập nhật thông tin business"""
        if "business_info" not in self.config_data:
            self.config_data["business_info"] = {}
        
        self.config_data["business_info"]["vendor"] = vendor
        self.config_data["business_info"]["product_type"] = product_type
        self.config_data["business_info"]["tags"] = tags
        print(f"Updated business info: vendor={vendor}, type={product_type}, tags={tags}")

    def get_size_configs(self) -> Dict[str, Dict[str, str]]:
        """Lấy cấu hình size và giá"""
        return self.config_data.get("size_configs", {})

    def get_active_size_configs(self) -> Dict[str, Dict[str, str]]:
        """Lấy chỉ những size configs có price khác rỗng"""
        all_configs = self.get_size_configs()
        active_configs = {}
        for size, config in all_configs.items():
            if config.get("price", "").strip():  # Chỉ lấy những size có price
                active_configs[size] = config
        return active_configs

    def update_size_config(self, size: str, price: str, compare_price: str, sku_suffix: str):
        """Cập nhật cấu hình cho một size"""
        if "size_configs" not in self.config_data:
            self.config_data["size_configs"] = {}
        
        self.config_data["size_configs"][size] = {
            "price": price,
            "compare_price": compare_price,
            "sku_suffix": sku_suffix
        }
        print(f"Updated size config for {size}: price={price}, compare_price={compare_price}, sku_suffix={sku_suffix}")

    def get_colors(self) -> List[str]:
        """Lấy danh sách màu sắc"""
        return self.config_data.get("colors", [])

    def update_colors(self, colors: List[str]):
        """Cập nhật danh sách màu sắc"""
        self.config_data["colors"] = colors
        print(f"Updated colors: {colors}")

    def get_sku_pattern(self) -> str:
        """Lấy pattern cho SKU"""
        return self.config_data.get("sku_pattern", "{randomstring}-{color}-{size}")

    def update_sku_pattern(self, pattern: str):
        """Cập nhật SKU pattern"""
        self.config_data["sku_pattern"] = pattern
        print(f"Updated SKU pattern: {pattern}")

    def get_description_template(self) -> str:
        """Lấy template mô tả sản phẩm"""
        return self.config_data.get("description_template", "")

    def update_description_template(self, template: str):
        """Cập nhật template mô tả sản phẩm"""
        self.config_data["description_template"] = template
        print("Updated description template")

    def generate_sku(self, design_name: str, color: str, size: str) -> str:
        """Tạo SKU dựa trên pattern với random string"""
        pattern = self.get_sku_pattern()
        size_config = self.get_size_configs().get(size, {})
        sku_suffix = size_config.get("sku_suffix", size)
        
        # Tạo random string cho SKU
        random_string = self.generate_random_string(10)
        
        return pattern.format(
            randomstring=random_string,
            design=design_name.lower().replace(" ", "-"),
            color=color.replace(" ", ""),
            size=sku_suffix
        )

    def generate_description(self, design_name: str, color: str, size: str) -> str:
        """Tạo mô tả sản phẩm dựa trên template"""
        template = self.get_description_template()
        business_info = self.get_business_info()
        
        return template.format(
            design=design_name,
            color=color,
            size=size,
            product_type=business_info.get("product_type", "Product")
        )

    def get_price_for_size(self, size: str) -> tuple:
        """Lấy giá và giá so sánh cho size"""
        size_config = self.get_size_configs().get(size, {})
        price = size_config.get("price", "19.99")
        compare_price = size_config.get("compare_price", "")
        return price, compare_price

    def reset_to_default(self):
        """Reset về cấu hình mặc định"""
        self.config_data = self.get_default_config()
        print("Reset Shopify config to default") 