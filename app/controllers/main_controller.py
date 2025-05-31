# app/controllers/main_controller.py
import os
from tkinter import filedialog
# Giả sử các lớp này đã được định nghĩa trong các tệp tương ứng
# from app.views.main_view import MainView (Sẽ import trong App)
# from app.models.config_manager import ConfigManager (Sẽ import trong App)

class MainController:
    def __init__(self, view, config_manager):
        self.view = view
        self.config_manager = config_manager
        self.mockups_dir = "mockups/"
        self.designs_dir = "designs/"

        self._setup_event_handlers()
        self.load_initial_data()

    def _setup_event_handlers(self):
        # Gắn các hàm xử lý sự kiện từ view vào controller
        self.view.mockup_list.bind("<<ComboboxSelected>>", self.on_mockup_selected)
        self.view.design_list.bind("<<ComboboxSelected>>", self.on_design_selected)
        
        # Scale events
        self.view.x_scale.config(command=self.on_controls_changed)
        self.view.y_scale.config(command=self.on_controls_changed)
        self.view.size_scale.config(command=self.on_controls_changed_size)

        # Entry events (để cập nhật khi nhấn Enter hoặc mất focus)
        # Vì Entry và Scale dùng chung IntVar, thay đổi hợp lệ trên Entry sẽ cập nhật IntVar,
        # và command của Scale sẽ tự động kích hoạt. Tuy nhiên, thêm bind rõ ràng 
        # cho Enter/FocusOut có thể cung cấp phản hồi ngay lập tức hơn trong một số trường hợp
        # hoặc nếu chúng ta muốn xử lý đặc biệt.

        # self.view.x_entry.bind("<Return>", self.on_controls_changed_from_entry)
        # self.view.x_entry.bind("<FocusOut>", self.on_controls_changed_from_entry)
        # self.view.y_entry.bind("<Return>", self.on_controls_changed_from_entry)
        # self.view.y_entry.bind("<FocusOut>", self.on_controls_changed_from_entry)
        # self.view.size_entry.bind("<Return>", self.on_controls_changed_from_entry_size)
        # self.view.size_entry.bind("<FocusOut>", self.on_controls_changed_from_entry_size)

        # Thực ra, khi IntVar thay đổi (sau khi validate thành công từ Entry),
        # command của Scale sẽ được kích hoạt. Nên có thể không cần bind thêm.
        # Chúng ta sẽ kiểm tra hành vi này.

        self.view.save_config_button.config(command=self.save_configuration)
        self.view.load_config_button.config(command=self.load_configuration)
        # Task 1.1: Scan thư mục mockups

    def scan_directory(self, directory, extensions=('.jpg', '.png')):
        files = []
        try:
            if not os.path.exists(directory):
                os.makedirs(directory)
                self.view.show_info("Info", f"Directory {directory} was created.")
                return files
            for f_name in os.listdir(directory):
                if f_name.lower().endswith(extensions):
                    files.append(f_name)
        except OSError as e:
            # Task 6.4: Error handling
            self.view.show_error("Directory Scan Error", f"Could not scan {directory}: {e}")
        return files

    def load_initial_data(self):
        mockup_files = self.scan_directory(self.mockups_dir)
        design_files = self.scan_directory(self.designs_dir)

        self.view.update_mockup_dropdown(mockup_files)
        self.view.update_design_dropdown(design_files)

        # Load config cho mockup đầu tiên (nếu có)
        if mockup_files:
            self.load_mockup_config(self.view.get_selected_mockup())
        self.update_preview()

    def on_mockup_selected(self, event=None):
        selected_mockup = self.view.get_selected_mockup()
        print(f"Mockup selected: {selected_mockup}")
        if selected_mockup and selected_mockup != "All Mockups":
            self.load_mockup_config(selected_mockup)
            # Hiển thị mockup image lên canvas
            mockup_image_path = os.path.join(self.mockups_dir, selected_mockup)
            self.view.draw_mockup_on_canvas(mockup_image_path)
        else:
            # Xóa mockup image khỏi canvas hoặc hiển thị trạng thái "All"
            self.view.draw_mockup_on_canvas(None) # Hoặc một ảnh mặc định
            self.view.update_controls(0,0,50) # Reset controls
        self.update_preview()

    def on_design_selected(self, event=None):
        selected_design = self.view.get_selected_design()
        print(f"Design selected: {selected_design}")
        self.update_preview()

    def on_controls_changed(self, value=None): # value là giá trị từ Scale hoặc IntVar
        # Task 6.3: Validation có thể thêm ở đây
        x = self.view.x_var.get()
        y = self.view.y_var.get()
        size_w = self.view.size_var.get()
        
        # Validate inputs (Task 6.3)
        # Giữ lại comment về validation, sẽ làm ở Task 6.3
        # if not (0 <= x <= 100 and 0 <= y <= 100 and 10 <= size_w <= 100):
            # print("Invalid input detected, but not actively blocking for now.")

        current_mockup = self.view.get_selected_mockup()
        if current_mockup and current_mockup != "All Mockups":
            self.config_manager.update_mockup_config(current_mockup, x, y, size_w)
            # Task 6.2: Auto-save config khi thay đổi
            self.config_manager.save_config() 
        self.update_preview()

    def on_controls_changed_size(self, value=None):
        # Task 6.1: Implement tỷ lệ 4500:5400 cho size slider
        # Khi thanh trượt Size (width) thay đổi, chiều cao cũng phải thay đổi theo tỷ lệ.
        # Tuy nhiên, preview canvas của chúng ta đã có tỷ lệ cố định (450x540).
        # Biến `size_var` sẽ đại diện cho chiều rộng của khung design trong preview.
        # Chiều cao sẽ được tính toán dựa trên chiều rộng này và tỷ lệ aspect ratio.
        self.on_controls_changed() # Gọi hàm chung để cập nhật và vẽ lại

    def update_preview(self):
        # Lấy giá trị X, Y, Size từ UI
        x_pos = self.view.x_var.get()
        y_pos = self.view.y_var.get()
        frame_width_percent = self.view.size_var.get()

        canvas_width = self.view.preview_canvas.winfo_width()
        canvas_height = self.view.preview_canvas.winfo_height()

        if canvas_width <= 1 or canvas_height <= 1: # Canvas chưa được vẽ
            # Đặt lịch chạy lại sau một khoảng thời gian ngắn
            self.view.after(100, self.update_preview)
            return

        # Tính toán kích thước pixel thực tế dựa trên phần trăm
        # Giả sử X, Y là % của kích thước canvas
        actual_x = (x_pos / 100) * canvas_width
        actual_y = (y_pos / 100) * canvas_height

        # Size (frame_width_percent) là % của chiều rộng canvas
        frame_actual_width = (frame_width_percent / 100) * canvas_width
        
        # Task 6.1: Tính chiều cao dựa trên tỷ lệ
        aspect_ratio = self.config_manager.get_aspect_ratio()
        frame_actual_height = frame_actual_width / aspect_ratio # width / (width/height) = height

        # Kiểm tra nếu chiều cao vượt quá canvas, thì scale lại dựa trên chiều cao
        if actual_y + frame_actual_height > canvas_height:
            frame_actual_height = canvas_height - actual_y
            frame_actual_width = frame_actual_height * aspect_ratio
        
        # Kiểm tra nếu chiều rộng vượt quá canvas (sau khi scale chiều cao)
        if actual_x + frame_actual_width > canvas_width:
            frame_actual_width = canvas_width - actual_x
            frame_actual_height = frame_actual_width / aspect_ratio

        selected_design = self.view.get_selected_design()
        design_image_path = None
        if selected_design:
            design_image_path = os.path.join(self.designs_dir, selected_design)

        self.view.draw_design_frame_on_canvas(actual_x, actual_y, frame_actual_width, frame_actual_height, design_image_path)

    def load_mockup_config(self, mockup_name):
        config = self.config_manager.get_mockup_config(mockup_name)
        if config:
            self.view.update_controls(config.get('x', 0), config.get('y', 0), config.get('size', 50))
        else:
            self.view.update_controls(0, 0, 50) # Giá trị mặc định
        self.update_preview()

    def save_configuration(self):
        # Task 1.3 & 3.4
        current_mockup = self.view.get_selected_mockup()
        config_was_updated = False
        if current_mockup and current_mockup != "All Mockups":
            x = self.view.x_var.get()
            y = self.view.y_var.get()
            size = self.view.size_var.get()
            self.config_manager.update_mockup_config(current_mockup, x, y, size)
            config_was_updated = True
            # Không cần gọi save_config() ở đây nữa nếu auto-save đã bật
            # Tuy nhiên, nút "Save Config" vẫn nên có chức năng lưu rõ ràng
            # self.config_manager.save_config()
            # self.view.show_info("Config Saved", f"Configuration for {current_mockup} saved.")

        # Nút Save Config sẽ lưu toàn bộ trạng thái hiện tại của self.config_manager.config_data
        if self.config_manager.config_data: # Chỉ lưu nếu có dữ liệu
            self.config_manager.save_config()
            if config_was_updated:
                 self.view.show_info("Config Saved", f"Configuration for {current_mockup} and all other changes saved.")
            else:
                 self.view.show_info("Config Saved", "All configurations saved.")
        elif config_was_updated: # Trường hợp chỉ có mockup hiện tại được update nhưng config_data ban đầu rỗng
            self.config_manager.save_config() # Lưu mockup hiện tại
            self.view.show_info("Config Saved", f"Configuration for {current_mockup} saved.")
        else:
             self.view.show_info("Config Not Saved", "No configuration data to save.")

    def load_configuration(self):
        # Task 1.3 & 3.5
        self.config_manager.load_config()
        # Cập nhật UI sau khi load
        selected_mockup = self.view.get_selected_mockup()
        if selected_mockup and selected_mockup != "All Mockups":
            self.load_mockup_config(selected_mockup)
        else: # Nếu "All Mockups" được chọn hoặc không có mockup nào, reset controls
            self.view.update_controls(0,0,50)
        self.update_preview()
        self.view.show_info("Config Loaded", "Configuration loaded from file.")

    # Task 6.3: Validation input X,Y,Size hợp lệ
    def validate_control_value(self, P, name):
        # P là giá trị mới của widget nếu thay đổi được chấp nhận
        # name là tên của widget (ví dụ: X, Y, Size)
        # This is a more robust way for validating Entry widgets, not directly for Scales
        # For scales, min/max are usually enough, but for direct input fields:
        if P == "": return True # Allow empty for intermediate input
        try:
            val = int(P)
            if name == "x_entry" or name == "y_entry":
                return 0 <= val <= 100
            elif name == "size_entry":
                return 10 <= val <= 100
        except ValueError:
            return False
        return True 