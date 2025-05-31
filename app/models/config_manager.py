# app/models/config_manager.py
import json
import os

class ConfigManager:
    def __init__(self, config_path="data/config.json"):
        self.config_path = config_path
        self.config_data = {}
        # Đảm bảo thư mục data tồn tại
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        self.load_config()

    def load_config(self):
        print(f"Loading config from {self.config_path}")
        try:
            with open(self.config_path, 'r') as f:
                self.config_data = json.load(f)
        except FileNotFoundError:
            print(f"Config file {self.config_path} not found. Creating a new one.")
            self.config_data = {}
            self.save_config() # Tạo tệp config mới nếu chưa có
        except json.JSONDecodeError:
            print(f"Error decoding JSON from {self.config_path}. Using empty config.")
            self.config_data = {} 
            # Có thể sao lưu tệp bị lỗi ở đây
        except Exception as e:
            print(f"An unexpected error occurred while loading config: {e}")
            self.config_data = {}

    def save_config(self):
        print(f"Saving config to {self.config_path}")
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config_data, f, indent=4)
            print("Config saved successfully.")
        except IOError as e:
            # Task 6.4: Error handling
            print(f"Error writing to config file {self.config_path}: {e}")
        except Exception as e:
            print(f"An unexpected error occurred while saving config: {e}")

    def get_mockup_config(self, mockup_name):
        return self.config_data.get(mockup_name, {})

    def update_mockup_config(self, mockup_name, x, y, size):
        if mockup_name not in self.config_data:
            self.config_data[mockup_name] = {}
        self.config_data[mockup_name]['x'] = x
        self.config_data[mockup_name]['y'] = y
        self.config_data[mockup_name]['size'] = size
        print(f"Updated config for {mockup_name}: X={x}, Y={y}, Size={size}")
        # Auto-save sẽ được gọi từ controller sau khi update này

    def get_aspect_ratio(self):
        return 4500 / 5400 