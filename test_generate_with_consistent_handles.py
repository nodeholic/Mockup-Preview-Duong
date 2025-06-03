#!/usr/bin/env python3
"""Test script để generate mockups và export CSV với consistent handles"""

import os
import sys
import tkinter as tk
from tkinter import ttk

# Import các module cần thiết
from app.controllers.main_controller import MainController
from app.models.config_manager import ConfigManager
from app.models.shopify_config_manager import ShopifyConfigManager

def resource_path(relative_path):
    """Hàm resource_path đơn giản cho test"""
    return os.path.join(os.getcwd(), relative_path)

def test_generate_and_export():
    """Test generate mockups và export CSV với consistent handles"""
    
    # Tạo mock view class
    class MockView:
        def __init__(self):
            self.output_folder_var = tk.StringVar()
            self.output_folder_var.set("output")
            self.generate_and_export_button = tk.Button()
            self.progress_bar = ttk.Progressbar()
            
        def show_error(self, title, message):
            print(f"ERROR: {title} - {message}")
            
        def show_info(self, title, message):
            print(f"INFO: {title} - {message}")
            
        def get_selected_design(self):
            return "All Designs"
            
        def after(self, delay, func, *args):
            # Immediately execute for testing
            if callable(func):
                func(*args)
            
        def reset_progress(self):
            pass
    
    # Tạo instances
    config_manager = ConfigManager()
    shopify_config = ShopifyConfigManager()
    view = MockView()
    
    # Tạo controller
    controller = MainController(view, config_manager, resource_path)
    controller.setup_shopify_integration(shopify_config)
    
    print("🚀 Bắt đầu test generate với consistent handles...")
    
    # Tạo output folder
    os.makedirs("output", exist_ok=True)
    
    # Test generate và export
    controller.generate_and_export_all()
    
    print("✅ Hoàn thành test!")

if __name__ == "__main__":
    test_generate_and_export() 