import tkinter as tk
import sys # For resource_path
import os  # For resource_path
from app.views.main_view import MainView
from app.models.config_manager import ConfigManager
from app.controllers.main_controller import MainController

def resource_path(relative_path):
    """ Lấy đường dẫn tuyệt đối đến tài nguyên, hoạt động cho dev và cho PyInstaller """
    try:
        # PyInstaller tạo thư mục tạm và lưu đường dẫn trong _MEIPASS
        base_path = sys._MEIPASS
    except AttributeError: # Sửa lỗi AttributeError nếu _MEIPASS không tồn tại
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Mockup Preview Tool")
        # Đặt kích thước cửa sổ ban đầu, có thể điều chỉnh sau
        self.geometry("1024x768") 

        # Sử dụng resource_path cho config file
        config_file_path = resource_path("data/config.json")
        config_manager = ConfigManager(config_path=config_file_path)

        # 2. Create View
        # MainView bây giờ là một Frame, nó cần một parent là root window (self)
        main_view = MainView(self) 
        # main_view.grid(sticky=(tk.W, tk.E, tk.N, tk.S))
        # self.columnconfigure(0, weight=1)
        # self.rowconfigure(0, weight=1)

        # 3. Create Controller
        controller = MainController(main_view, config_manager, resource_path)
        main_view.set_controller(controller)

if __name__ == "__main__":
    app = App()
    app.mainloop() 