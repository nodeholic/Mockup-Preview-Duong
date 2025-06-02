import tkinter as tk
import sys # For resource_path
import os  # For resource_path
from app.views.main_view import MainView
from app.models.config_manager import ConfigManager
from app.models.shopify_config_manager import ShopifyConfigManager
from app.controllers.main_controller import MainController

def resource_path(relative_path):
    """ Lấy đường dẫn tuyệt đối đến tài nguyên. """
    # print(f"DEBUG: resource_path called for: {relative_path}")
    # print(f"DEBUG: sys.frozen: {getattr(sys, 'frozen', 'Not set')}")
    # print(f"DEBUG: sys._MEIPASS: {getattr(sys, '_MEIPASS', 'Not set')}")
    # print(f"DEBUG: sys.executable: {sys.executable}")
    # print(f"DEBUG: sys.argv[0]: {sys.argv[0]}")
    # print(f"DEBUG: os.path.dirname(sys.executable): {os.path.dirname(sys.executable)}")
    # print(f"DEBUG: os.path.dirname(os.path.abspath(sys.argv[0])): {os.path.dirname(os.path.abspath(sys.argv[0]))}")

    if getattr(sys, 'frozen', False):
        # Đang chạy dưới dạng bundle (đã đóng gói bởi PyInstaller)
        # Đối với dữ liệu nằm ngoài (không dùng --add-data), chúng ta muốn thư mục của file .exe gốc.
        # sys.argv[0] thường trỏ đến file .exe gốc ngay cả khi sys.executable ở trong _MEIPASS.
        base_path = os.path.dirname(os.path.abspath(sys.argv[0]))
        # print(f"DEBUG: Frozen mode. Base path from sys.argv[0]: {base_path}")
    else:
        # Không 'frozen', đang chạy dưới dạng script .py (chế độ dev)
        # Tài nguyên nằm tương đối so với thư mục script.
        base_path = os.path.abspath(".")
        # print(f"DEBUG: Not frozen (dev mode). Base path from os.path.abspath('.'): {base_path}")

    final_path = os.path.join(base_path, relative_path)
    # print(f"DEBUG: Final path for '{relative_path}': {final_path}, Exists: {os.path.exists(final_path)}")
    return final_path

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Mockup Preview Tool with Shopify Export")
        # Đặt kích thước cửa sổ ban đầu, có thể điều chỉnh sau
        self.geometry("1200x800") 

        # Sử dụng resource_path cho config files
        config_file_path = resource_path("data/config.json")
        shopify_config_file_path = resource_path("data/shopify_config.json")
        
        # Initialize managers
        config_manager = ConfigManager(config_path=config_file_path)
        shopify_config_manager = ShopifyConfigManager(config_path=shopify_config_file_path)

        # 2. Create View
        # MainView bây giờ là một Frame, nó cần một parent là root window (self)
        main_view = MainView(self) 
        # main_view.grid(sticky=(tk.W, tk.E, tk.N, tk.S))
        # self.columnconfigure(0, weight=1)
        # self.rowconfigure(0, weight=1)

        # 3. Create Controller
        controller = MainController(main_view, config_manager, resource_path)
        main_view.set_controller(controller)
        
        # 4. Setup Shopify Integration
        controller.setup_shopify_integration(shopify_config_manager)
        
        # 5. Load Shopify config vào UI
        controller.load_shopify_config()

if __name__ == "__main__":
    app = App()
    app.mainloop() 