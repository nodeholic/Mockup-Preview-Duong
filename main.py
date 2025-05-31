import tkinter as tk
from app.views.main_view import MainView
from app.models.config_manager import ConfigManager
from app.controllers.main_controller import MainController

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Mockup Preview Tool")
        # Đặt kích thước cửa sổ ban đầu, có thể điều chỉnh sau
        self.geometry("1024x768") 

        # 1. Create Model
        config_manager = ConfigManager(config_path="data/config.json")

        # 2. Create View
        # MainView bây giờ là một Frame, nó cần một parent là root window (self)
        main_view = MainView(self) 
        # main_view.grid(sticky=(tk.W, tk.E, tk.N, tk.S))
        # self.columnconfigure(0, weight=1)
        # self.rowconfigure(0, weight=1)

        # 3. Create Controller
        controller = MainController(main_view, config_manager)

        # Thiết lập để view có thể truy cập controller nếu cần (ít phổ biến hơn)
        # main_view.set_controller(controller)

if __name__ == "__main__":
    app = App()
    app.mainloop() 