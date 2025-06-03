# app/controllers/main_controller.py
import os
import datetime # For timestamp in filename (Task 12.5)
import threading # For progress bar updates during batch (Task 9.2)
from tkinter import filedialog
import tkinter as tk # <--- Thêm dòng này
from PIL import Image, ImageOps, ImageEnhance # Thêm ImageEnhance
# Giả sử các lớp này đã được định nghĩa trong các tệp tương ứng
# from app.views.main_view import MainView (Sẽ import trong App)
# from app.models.config_manager import ConfigManager (Sẽ import trong App)

# Import Shopify models
from app.models.shopify_config_manager import ShopifyConfigManager
from app.models.csv_exporter import ShopifyCSVExporter

# Define fixed output size (Task: Fixed output size)
OUTPUT_WIDTH = 1200
OUTPUT_HEIGHT = 1200
OUTPUT_BACKGROUND_COLOR = (255, 255, 255, 255) # White background for letterboxing, RGBA
# OUTPUT_JPG_QUALITY = 90 # Xóa hằng số này

class MainController:
    def __init__(self, view, config_manager, resource_path_func):
        self.view = view
        self.config_manager = config_manager
        self.resource_path = resource_path_func # Lưu hàm resource_path

        # Sử dụng resource_path cho các thư mục này
        self.mockups_dir = self.resource_path("mockups/")
        self.designs_dir = self.resource_path("designs/")
        # output_dir có thể vẫn là tương đối hoặc bạn cũng có thể dùng resource_path nếu muốn nó nằm trong bundle
        # Tuy nhiên, thường thì output người dùng muốn chọn tự do bên ngoài.
        # Chúng ta sẽ giữ nguyên cách output_dir được xử lý qua filedialog, nhưng thư mục mặc định ban đầu có thể điều chỉnh.
        default_output_parent_dir = self.resource_path(".") # Thư mục gốc của bundle/script
        self.output_dir = os.path.join(default_output_parent_dir, "output/")
        
        self.view.output_folder_var.set(self.output_dir) # Đặt giá trị mặc định cho UI

        # Dictionary để lưu mapping design -> handle cho session hiện tại
        self.design_handle_mapping = {}

        self._setup_event_handlers()
        # Đảm bảo các thư mục này tồn tại khi khởi động
        os.makedirs(self.mockups_dir, exist_ok=True)
        os.makedirs(self.designs_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)
        self.load_initial_data()

    def _setup_event_handlers(self):
        # Gắn các hàm xử lý sự kiện từ view vào controller
        self.view.mockup_list.bind("<<ComboboxSelected>>", self.on_mockup_selected)
        self.view.design_list.bind("<<ComboboxSelected>>", self.on_design_selected)
        
        # Scale events
        self.view.x_scale.config(command=self.on_controls_changed)
        self.view.y_scale.config(command=self.on_controls_changed)
        self.view.size_scale.config(command=self.on_controls_changed_size)
        self.view.opacity_scale.config(command=self.on_controls_changed) # Opacity scale cũng gọi on_controls_changed

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

        # New event handlers for Generate and Output Folder (Task 9.1, 9.4)
        self.view.generate_button.config(command=self.on_generate_button_pressed)
        self.view.browse_output_button.config(command=self.browse_output_folder)

    def handle_xy_entry_change(self):
        """Được gọi khi nội dung của X hoặc Y Entry thay đổi (KeyRelease)."""
        # Đảm bảo rằng giá trị DoubleVar đã được cập nhật (sau validate)
        # Sau đó gọi on_controls_changed để xử lý như khi Scale thay đổi.
        # print("XY Entry changed, calling on_controls_changed")
        self.on_controls_changed()

    def handle_size_entry_change(self):
        """Được gọi khi nội dung của Size Entry thay đổi (KeyRelease)."""
        # print("Size Entry changed, calling on_controls_changed_size")
        self.on_controls_changed_size()

    def handle_opacity_entry_change(self): # Hàm mới
        self.on_controls_changed() 

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
        else: # Nếu không có mockup nào, vẫn cần đảm bảo control opacity được đặt giá trị mặc định
             self.view.update_controls(0, 0, 50, 100.0)
        self.update_preview()

    def on_mockup_selected(self, event=None):
        selected_mockup = self.view.get_selected_mockup()
        print(f"Mockup selected: {selected_mockup}")
        if selected_mockup and selected_mockup != "All Mockups":
            self.load_mockup_config(selected_mockup)
            mockup_image_path = os.path.join(self.mockups_dir, selected_mockup)
            self.view.draw_mockup_on_canvas(mockup_image_path)
        elif selected_mockup == "All Mockups":
            self.view.draw_mockup_on_canvas(None)
            self.view.update_controls(0,0,50,100.0) # Reset cả opacity
        self.update_preview() # Luôn gọi update_preview để cập nhật khung design

    def on_design_selected(self, event=None):
        selected_design = self.view.get_selected_design()
        print(f"Design selected: {selected_design}")
        # Không cần làm gì đặc biệt ở đây nếu là "All Designs"
        # vì update_preview sẽ xử lý việc hiển thị hoặc không hiển thị design.
        self.update_preview()

    def on_controls_changed(self, value=None): # value là giá trị từ Scale hoặc IntVar
        # Task 6.3: Validation có thể thêm ở đây
        x = self.view.x_var.get()
        y = self.view.y_var.get()
        size_w = self.view.size_var.get()
        opacity = self.view.opacity_var.get() # Lấy opacity
        
        # Validate inputs (Task 6.3)
        # Giữ lại comment về validation, sẽ làm ở Task 6.3
        # if not (0 <= x <= 100 and 0 <= y <= 100 and 10 <= size_w <= 100):
            # print("Invalid input detected, but not actively blocking for now.")

        current_mockup = self.view.get_selected_mockup()
        if current_mockup and current_mockup != "All Mockups":
            self.config_manager.update_mockup_config(current_mockup, x, y, size_w, opacity) # Lưu cả opacity
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
        x_pos_percent = self.view.x_var.get()
        y_pos_percent = self.view.y_var.get()
        frame_width_percent = self.view.size_var.get()
        opacity = self.view.opacity_var.get() # Lấy opacity

        # Lấy kích thước và offset của ảnh mockup thực tế đang hiển thị trên canvas
        displayed_mockup_w = self.view.displayed_mockup_width
        displayed_mockup_h = self.view.displayed_mockup_height
        displayed_mockup_offset_x = self.view.displayed_mockup_offset_x
        displayed_mockup_offset_y = self.view.displayed_mockup_offset_y

        if displayed_mockup_w <= 0 or displayed_mockup_h <= 0: # Nếu chưa có mockup nào được vẽ (hoặc đã clear)
            # Xóa khung design nếu có
            self.view.draw_design_frame_on_canvas(0,0,0,0, None)
            # Không cần gọi after(100, self.update_preview) ở đây nữa vì không phụ thuộc canvas_width/height nữa
            return

        # Tính toán X, Y, Width của khung design dựa trên kích thước của *ảnh mockup hiển thị*
        actual_x_on_mockup = (x_pos_percent / 100) * displayed_mockup_w
        actual_y_on_mockup = (y_pos_percent / 100) * displayed_mockup_h
        frame_actual_width_on_mockup = (frame_width_percent / 100) * displayed_mockup_w
        
        aspect_ratio = self.config_manager.get_aspect_ratio()
        frame_actual_height_on_mockup = frame_actual_width_on_mockup / aspect_ratio

        # Giữ logic clamp (nếu cần) so với displayed_mockup_w/h, nhưng có thể không cần thiết nếu X,Y,Size luôn là 0-100%
        # Ví dụ, nếu X=100% và Size=10%, khung sẽ bắt đầu ở cạnh phải và rộng 10% mockup.
        # Clamp đơn giản nếu vượt quá:
        if actual_y_on_mockup + frame_actual_height_on_mockup > displayed_mockup_h:
            frame_actual_height_on_mockup = displayed_mockup_h - actual_y_on_mockup
            frame_actual_width_on_mockup = frame_actual_height_on_mockup * aspect_ratio
        
        if actual_x_on_mockup + frame_actual_width_on_mockup > displayed_mockup_w:
            frame_actual_width_on_mockup = displayed_mockup_w - actual_x_on_mockup
            frame_actual_height_on_mockup = frame_actual_width_on_mockup / aspect_ratio

        # Tọa độ cuối cùng trên canvas = offset của mockup + tọa độ trên mockup
        final_x_on_canvas = displayed_mockup_offset_x + actual_x_on_mockup
        final_y_on_canvas = displayed_mockup_offset_y + actual_y_on_mockup

        selected_design_name = self.view.get_selected_design()
        design_image_path = None
        if selected_design_name and selected_design_name != "All Designs":
            design_image_path = os.path.join(self.designs_dir, selected_design_name)

        current_mockup = self.view.get_selected_mockup()
        if current_mockup and current_mockup != "All Mockups":
            self.view.draw_design_frame_on_canvas(
                final_x_on_canvas, 
                final_y_on_canvas, 
                frame_actual_width_on_mockup, 
                frame_actual_height_on_mockup, 
                design_image_path
            )
        else:
            self.view.draw_design_frame_on_canvas(0, 0, 0, 0, None)

    def load_mockup_config(self, mockup_name):
        config = self.config_manager.get_mockup_config(mockup_name)
        if config:
            self.view.update_controls(
                config.get('x', 0),
                config.get('y', 0),
                config.get('size', 50),
                config.get('opacity', 100.0) # Lấy opacity, mặc định 100
            )
        else:
            self.view.update_controls(0, 0, 50, 100.0) # Giá trị mặc định bao gồm opacity
        self.update_preview()

    def save_configuration(self):
        # Task 1.3 & 3.4
        current_mockup = self.view.get_selected_mockup()
        config_was_updated = False
        if current_mockup and current_mockup != "All Mockups":
            x = self.view.x_var.get()
            y = self.view.y_var.get()
            size = self.view.size_var.get()
            opacity = self.view.opacity_var.get() # Lấy opacity
            self.config_manager.update_mockup_config(current_mockup, x, y, size, opacity) # Lưu cả opacity
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
            self.view.update_controls(0,0,50,100.0) # Reset cả opacity
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

    def browse_output_folder(self):
        directory = filedialog.askdirectory()
        if directory: # If a directory is selected
            self.output_dir = directory
            self.view.output_folder_var.set(self.output_dir)
            print(f"Output directory set to: {self.output_dir}")

    def on_generate_button_pressed(self):
        print("Generate button pressed!")
        selected_mockup = self.view.get_selected_mockup()
        selected_design = self.view.get_selected_design()
        output_folder = self.view.output_folder_var.get()

        if not os.path.isdir(output_folder):
            self.view.show_error("Output Error", f"Output folder does not exist: {output_folder}\nPlease create it or select a valid folder.")
            return
        
        # Kiểm tra nếu "All Designs" được chọn mà không có design nào thực tế
        if selected_design == "All Designs" and not self.scan_directory(self.designs_dir):
            self.view.show_error("Generate Error", "No design files found to process with \"All Designs\".")
            return
            
        # Kiểm tra tương tự cho "All Mockups"
        if selected_mockup == "All Mockups" and not self.scan_directory(self.mockups_dir):
            self.view.show_error("Generate Error", "No mockup files found to process with \"All Mockups\".")
            return

        if not selected_design and selected_design != "All Designs": # Nếu không chọn gì và cũng không phải là "All Designs"
            self.view.show_error("Generate Error", "Please select a design image or \"All Designs\".")
            return

        if not selected_mockup and selected_mockup != "All Mockups":
            self.view.show_error("Generate Error", "Please select a mockup image or \"All Mockups\".")
            return

        self.view.generate_button.config(state=tk.DISABLED)
        self.view.reset_progress()

        thread_args = (output_folder, True) # Common args for threading
        target_function = None

        if selected_mockup == "All Mockups":
            if selected_design == "All Designs":
                print("Batch: All Mockups x All Designs")
                target_function = self.generate_batch_all_combinations
                # generate_batch_all_combinations sẽ không cần selected_design/mockup cụ thể
            else: # All Mockups, Single Design
                print(f"Batch: All Mockups x Design: {selected_design}")
                target_function = self.generate_batch_all_mockups_one_design
                thread_args = (selected_design, output_folder, True)
        elif selected_design == "All Designs": # Single Mockup, All Designs
            print(f"Batch: Mockup: {selected_mockup} x All Designs")
            target_function = self.generate_batch_one_mockup_all_designs
            thread_args = (selected_mockup, output_folder, True)
        else: # Single Mockup, Single Design
            print(f"Single: Mockup: {selected_mockup} x Design: {selected_design}")
            target_function = self.generate_single_image_threaded_wrapper
            thread_args = (selected_mockup, selected_design, output_folder)
        
        if target_function:
            thread = threading.Thread(target=target_function, args=thread_args)
            thread.start()
        else:
            # Should not happen if logic is correct, but as a fallback:
            self.view.show_error("Generate Error", "Invalid selection combination.")
            self.view.generate_button.config(state=tk.NORMAL)

    def generate_single_image_threaded_wrapper(self, mockup_name, design_name, output_folder):
        try:
            self.view.update_progress(0) # Show some activity
            self.generate_single_image(mockup_name, design_name, output_folder)
            self.view.update_progress(100) # Mark as complete
        finally:
            # Ensure button is re-enabled from the main thread via `after`
            self.view.after(0, lambda: self.view.generate_button.config(state=tk.NORMAL))
            self.view.after(100, self.view.reset_progress) # Reset progress after a short delay

    # --- Start of Image Processing and Generation Logic (Phase 2) ---
    def _get_design_target_rect_on_full_mockup(self, mockup_image_path, config_x_percent, config_y_percent, config_size_w_percent, aspect_ratio_wh):
        """Calculates the design's target rectangle (x, y, w, h) on the full-resolution mockup image."""
        try:
            with Image.open(mockup_image_path) as full_mockup_img:
                mockup_w, mockup_h = full_mockup_img.size

            # Convert percentages from config (relative to preview canvas) to be relative to full mockup dimensions
            # For simplicity, assume preview canvas (450x540) represents the whole mockup image for placement percentages.
            # A more accurate way might involve knowing the actual sub-region of the mockup that the preview canvas displays.
            
            # X, Y are percentages of the mockup's dimensions
            target_x = (config_x_percent / 100) * mockup_w
            target_y = (config_y_percent / 100) * mockup_h

            # Size (width percent) is also a percentage of the mockup's width
            target_w = (config_size_w_percent / 100) * mockup_w
            target_h = target_w / aspect_ratio_wh # height = width / (width/height)
            
            # Ensure the design frame does not exceed mockup boundaries (simple clamp)
            if target_x + target_w > mockup_w:
                target_w = mockup_w - target_x
                target_h = target_w / aspect_ratio_wh 
            if target_y + target_h > mockup_h:
                target_h = mockup_h - target_y
                target_w = target_h * aspect_ratio_wh
            
            # Ensure x, y are not negative after adjustment (can happen if initial size is too large)
            target_x = max(0, target_x)
            target_y = max(0, target_y)

            return int(target_x), int(target_y), int(target_w), int(target_h)

        except FileNotFoundError:
            self.view.show_error("Image Error", f"Mockup image not found: {mockup_image_path}")
            return None
        except Exception as e:
            self.view.show_error("Image Processing Error", f"Error processing mockup {mockup_image_path}: {e}")
            return None

    def _fit_design_to_target(self, design_image_path, target_w, target_h):
        """ Task 7.2, 7.3: Resizes design to fit target_w, target_h, preserving aspect ratio (letterbox/pillarbox). """
        try:
            with Image.open(design_image_path) as design_img:
                original_design_w, original_design_h = design_img.size
                original_aspect_ratio = original_design_w / original_design_h
                target_aspect_ratio = target_w / target_h

                if original_aspect_ratio > target_aspect_ratio: # Design is wider than target area (fit by width)
                    new_w = target_w
                    new_h = int(new_w / original_aspect_ratio)
                else: # Design is taller or same aspect_ratio (fit by height)
                    new_h = target_h
                    new_w = int(new_h * original_aspect_ratio)
                
                resized_design = design_img.resize((new_w, new_h), Image.Resampling.LANCZOS)

                # Create a new image with target dimensions and paste the resized_design centered
                # Task 10.4: Handle transparent/white background for letterbox
                # Assuming design might have alpha, use RGBA. Background is transparent.
                final_fitted_design = Image.new('RGBA', (target_w, target_h), (0,0,0,0)) 
                
                paste_x = (target_w - new_w) // 2
                # Điều chỉnh vị trí dán Y để align top nếu design được letterbox theo chiều dọc
                if original_aspect_ratio > target_aspect_ratio: # Design rộng hơn/vuông (letterbox dọc)
                    paste_y = 0 # Align top
                else: # Design cao hơn (pillarbox ngang) hoặc vừa khít
                    paste_y = (target_h - new_h) // 2 # Align center theo chiều Y
                
                final_fitted_design.paste(resized_design, (paste_x, paste_y))
                
                return final_fitted_design

        except FileNotFoundError:
            self.view.show_error("Image Error", f"Design image not found: {design_image_path}")
            return None
        except Exception as e:
            self.view.show_error("Image Processing Error", f"Error fitting design {design_image_path}: {e}")
            return None

    def generate_design_handle(self, design_name):
        """Tạo handle cho design giống như trong CSV exporter - consistent trong session"""
        design_base = os.path.splitext(design_name)[0]
        
        # Kiểm tra xem đã có handle cho design này chưa
        if design_name in self.design_handle_mapping:
            return self.design_handle_mapping[design_name], design_base
        
        # Tạo random string như trong CSV exporter để consistent
        if hasattr(self, 'shopify_config'):
            random_string = self.shopify_config.generate_random_string(10)
        else:
            # Fallback nếu chưa có shopify_config
            import random
            import string
            random_string = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
        
        handle = f"{design_base.lower().replace(' ', '-').replace('_', '-')}-{random_string}"
        
        # Lưu mapping để dùng lại
        self.design_handle_mapping[design_name] = handle
        
        return handle, design_base

    def generate_single_image(self, mockup_name, design_name, output_folder):
        print(f"Generating image for Mockup: {mockup_name}, Design: {design_name}")
        mockup_path = os.path.join(self.mockups_dir, mockup_name)
        design_path = os.path.join(self.designs_dir, design_name)

        # Tạo subfolder cho design
        handle, design_base = self.generate_design_handle(design_name)
        design_output_folder = os.path.join(output_folder, handle)
        os.makedirs(design_output_folder, exist_ok=True)

        config = self.config_manager.get_mockup_config(mockup_name)
        if not config:
            self.view.show_error("Config Error", f"No configuration found for mockup: {mockup_name}")
            return False 

        x_percent, y_percent, size_w_percent = config.get('x',0), config.get('y',0), config.get('size',50)
        opacity_percent = config.get('opacity', 100.0) # Lấy opacity từ config
        design_area_aspect_ratio_wh = self.config_manager.get_aspect_ratio()

        target_rect = self._get_design_target_rect_on_full_mockup(
            mockup_path, x_percent, y_percent, size_w_percent, design_area_aspect_ratio_wh
        )
        if not target_rect: return False
        target_x, target_y, target_w, target_h = target_rect
        if target_w <= 0 or target_h <= 0:
            # self.view.show_error("Generate Error", f"Calculated design area for {mockup_name} has zero or negative size.") # Có thể gây nhiều popup khi batch
            print(f"Error: Calculated design area for {mockup_name} has zero or negative size.")
            return False

        fitted_design_img = self._fit_design_to_target(design_path, target_w, target_h)
        if not fitted_design_img: return False

        # Áp dụng opacity cho fitted_design_img (ảnh RGBA)
        if fitted_design_img.mode != 'RGBA':
            fitted_design_img = fitted_design_img.convert('RGBA')
        
        datas = fitted_design_img.getdata()
        newData = []
        for item in datas:
            new_alpha = int(item[3] * (opacity_percent / 100.0))
            newData.append((item[0], item[1], item[2], new_alpha))
        fitted_design_img.putdata(newData)
        # Kết thúc áp dụng opacity

        try:
            full_mockup_img = Image.open(mockup_path).convert("RGBA")
            composite_img = full_mockup_img.copy()
            # Dùng fitted_design_img đã có alpha để ghép
            composite_img.paste(fitted_design_img, (target_x, target_y), fitted_design_img) 

            image_to_save = composite_img
            # Chuyển đổi sang RGB để lưu JPEG
            if image_to_save.mode == 'RGBA':
                # Tạo nền trắng RGB với kích thước của image_to_save
                background_rgb = OUTPUT_BACKGROUND_COLOR[:3] 
                final_image_rgb = Image.new("RGB", image_to_save.size, background_rgb)
                # Dán image_to_save (có alpha) lên nền trắng này
                final_image_rgb.paste(image_to_save, (0,0), image_to_save) 
                image_to_save = final_image_rgb
            elif image_to_save.mode != 'RGB':
                image_to_save = image_to_save.convert("RGB")

            # Sử dụng tên mockup gốc (giữ extension gốc)
            mockup_base = os.path.splitext(mockup_name)[0]
            mockup_ext = os.path.splitext(mockup_name)[1]
            
            # Tên file = tên mockup gốc với extension JPG
            output_filename = f"{mockup_base}.jpg"
            # Lưu vào subfolder của design
            output_path = os.path.join(design_output_folder, output_filename)
            
            # Lưu ảnh JPEG, không còn tham số quality từ view
            image_to_save.save(output_path, "JPEG") 
            
            saved_width, saved_height = image_to_save.size
            print(f"Saved as {output_path} (Size: {saved_width}x{saved_height})")
            return True
        except FileNotFoundError:
            self.view.show_error("Image Error", f"File not found: {mockup_path} or {design_path}")
            return False
        except Exception as e:
            # Ghi log lỗi chi tiết hơn ra console để debug
            import traceback
            print(f"--- ERROR in generate_single_image for {mockup_name} & {design_name} ---")
            print(traceback.format_exc())
            print(f"--- END ERROR ---")
            self.view.show_error("Generation Error", f"Failed to generate image for {mockup_name}: {e}")
            return False

    # --- End of Phase 2 Logic ---

    # --- Start of Batch Processing Logic (Phase 3) ---
    def generate_batch_all_mockups_one_design(self, design_name, output_folder, threaded=False, silent=False):
        """ Task 12.2: Generate all mockups for one specific design. """
        mockup_files = self.scan_directory(self.mockups_dir)
        if not mockup_files:
            self.view.show_error("Batch Generate Error", "No mockup files found.")
            if threaded: self.view.after(0, lambda: self.view.generate_button.config(state=tk.NORMAL))
            return
        
        total_mockups = len(mockup_files)
        print(f"Starting batch generation for ALL {total_mockups} mockups with design '{design_name}'...")
        if threaded: self.view.update_progress(0)
        
        success_count = 0
        processed_count = 0
        for i, mockup_name in enumerate(mockup_files):
            processed_count += 1
            current_progress = (processed_count / total_mockups) * 100
            print(f"Processing mockup {processed_count}/{total_mockups}: {mockup_name} ({current_progress:.2f}%)")
            
            if self.generate_single_image(mockup_name, design_name, output_folder):
                success_count += 1
            
            if threaded:
                self.view.after(0, self.view.update_progress, current_progress)
            
        final_message = f"Batch generation finished. Successfully generated {success_count}/{processed_count} images."
        print(final_message)
        
        # Chỉ hiện alert nếu không phải silent mode
        if not silent:
            if threaded:
                self.view.after(0, lambda: self.view.show_info("Batch Complete", final_message))
                self.view.after(0, lambda: self.view.generate_button.config(state=tk.NORMAL))
                self.view.after(100, self.view.reset_progress) 
            else:
                self.view.show_info("Batch Complete", final_message)

    def generate_batch_one_mockup_all_designs(self, mockup_name, output_folder, threaded=False, silent=False):
        """ Task 12.3: Generate the selected mockup with all available designs. """
        design_files = self.scan_directory(self.designs_dir)
        if not design_files:
            self.view.show_error("Batch Generate Error", "No design files found.")
            if threaded: self.view.after(0, lambda: self.view.generate_button.config(state=tk.NORMAL))
            return

        total_designs = len(design_files)
        print(f"Starting batch generation for mockup '{mockup_name}' with {total_designs} designs...")
        if threaded: self.view.update_progress(0)

        success_count = 0
        processed_count = 0
        for i, design_name in enumerate(design_files):
            processed_count += 1
            current_progress = (processed_count / total_designs) * 100
            print(f"Processing design {processed_count}/{total_designs}: {design_name} ({current_progress:.2f}%)")

            if self.generate_single_image(mockup_name, design_name, output_folder):
                success_count += 1
            
            if threaded:
                self.view.after(0, self.view.update_progress, current_progress)

        final_message = f"Batch generation finished for mockup '{mockup_name}'.\nSuccessfully generated {success_count}/{processed_count} images."
        print(final_message)
        
        # Chỉ hiện alert nếu không phải silent mode
        if not silent:
            if threaded:
                self.view.after(0, lambda: self.view.show_info("Batch Complete", final_message))
                self.view.after(0, lambda: self.view.generate_button.config(state=tk.NORMAL))
                self.view.after(100, self.view.reset_progress)
            else:
                self.view.show_info("Batch Complete", final_message)

    def generate_batch_all_combinations(self, output_folder, threaded=False, silent=False):
        """ Task 12.4: Generate all mockups with all available designs. """
        mockup_files = self.scan_directory(self.mockups_dir)
        design_files = self.scan_directory(self.designs_dir)

        if not mockup_files or not design_files:
            self.view.show_error("Batch Generate Error", "No mockup or design files found for all x all combination.")
            if threaded: self.view.after(0, lambda: self.view.generate_button.config(state=tk.NORMAL))
            return

        total_combinations = len(mockup_files) * len(design_files)
        if total_combinations == 0:
            self.view.show_error("Batch Generate Error", "No combinations to generate.")
            if threaded: self.view.after(0, lambda: self.view.generate_button.config(state=tk.NORMAL))
            return
            
        print(f"Starting batch generation for ALL {len(mockup_files)} mockups with ALL {len(design_files)} designs ({total_combinations} total images)...")
        if threaded: self.view.update_progress(0)

        success_count = 0
        processed_count = 0
        for mockup_name in mockup_files:
            for design_name in design_files:
                processed_count += 1
                current_progress = (processed_count / total_combinations) * 100
                print(f"Processing combination {processed_count}/{total_combinations}: Mockup '{mockup_name}', Design '{design_name}' ({current_progress:.2f}%)")

                if self.generate_single_image(mockup_name, design_name, output_folder):
                    success_count += 1
                
                if threaded:
                    self.view.after(0, self.view.update_progress, current_progress)
        
        final_message = f"ALL x ALL Batch generation finished.\nSuccessfully generated {success_count}/{processed_count} images."
        print(final_message)
        
        # Chỉ hiện alert nếu không phải silent mode
        if not silent:
            if threaded:
                self.view.after(0, lambda: self.view.show_info("Batch Complete", final_message))
                self.view.after(0, lambda: self.view.generate_button.config(state=tk.NORMAL))
                self.view.after(100, self.view.reset_progress)
            else:
                self.view.show_info("Batch Complete", final_message)

    def generate_and_export_all(self):
        """Generate mockups và export CSV trong một workflow (không alert)"""
        try:
            output_folder = self.view.output_folder_var.get()
            if not output_folder:
                self.view.show_error("Export Error", "Vui lòng chọn output folder.")
                return

            design_names = self.get_selected_designs_for_export()
            if not design_names:
                self.view.show_error("Export Error", "Vui lòng chọn design để process.")
                return

            # Disable buttons (không hiện alert bắt đầu)
            self.view.generate_and_export_button.config(state=tk.DISABLED)
            
            # Chạy trong thread để không block UI
            def process_thread():
                try:
                    # Step 1: Generate mockups (silent mode - không alert)
                    self.view.after(0, lambda: self.view.progress_bar.config(mode='indeterminate'))
                    self.view.after(0, self.view.progress_bar.start)
                    
                    # Generate tất cả combinations (silent mode)
                    self.generate_batch_all_combinations(output_folder, threaded=False, silent=True)
                    
                    # Step 2: Export CSV với handle mapping
                    mockup_files = self.get_generated_mockup_files(output_folder)
                    mockup_templates = self.get_mockup_templates()
                    
                    # Truyền design handle mapping cho CSV exporter để consistent
                    csv_path = self.csv_exporter.export_csv(
                        design_names, mockup_files, output_folder, 
                        mockup_templates=mockup_templates,
                        design_handle_mapping=self.design_handle_mapping
                    )
                    
                    # Show final success message
                    summary = self.csv_exporter.get_export_summary(design_names)
                    message = f"✅ Hoàn thành!\n\nMockups và CSV đã được tạo:\n{output_folder}\n\n📊 Thống kê:\n- {summary['total_designs']} designs\n- {summary['total_variants']} variants\n- {summary['total_products']} products\n\n📄 CSV file: {os.path.basename(csv_path)}"
                    
                    self.view.after(0, lambda: self.view.show_info("Process Complete", message))
                    
                except Exception as e:
                    self.view.after(0, lambda: self.view.show_error("Process Error", f"Lỗi trong quá trình xử lý: {e}"))
                finally:
                    # Re-enable buttons
                    self.view.after(0, lambda: self.view.generate_and_export_button.config(state=tk.NORMAL))
                    self.view.after(0, self.view.progress_bar.stop)
                    self.view.after(0, lambda: self.view.progress_bar.config(mode='determinate'))
                    self.view.after(0, self.view.reset_progress)
            
            # Start thread
            thread = threading.Thread(target=process_thread, daemon=True)
            thread.start()
            
        except Exception as e:
            self.view.show_error("Process Error", f"Lỗi khi bắt đầu process: {e}")

    # --- Shopify Integration Methods ---
    def setup_shopify_integration(self, shopify_config_manager):
        """Thiết lập tích hợp Shopify"""
        self.shopify_config = shopify_config_manager
        self.csv_exporter = ShopifyCSVExporter(self.shopify_config)
        self._setup_shopify_event_handlers()

    def _setup_shopify_event_handlers(self):
        """Thiết lập event handlers cho Shopify functionality"""
        # Tab 1 - Shopify Export buttons
        self.view.preview_csv_button.config(command=self.preview_csv)
        self.view.generate_only_button.config(command=self.generate_mockups_only)
        self.view.export_csv_only_button.config(command=self.export_csv_only)
        self.view.generate_and_export_button.config(command=self.generate_and_export_all)
        
        # Tab 2 - Config buttons
        self.view.save_shopify_config_button.config(command=self.save_shopify_config)
        self.view.load_shopify_config_button.config(command=self.load_shopify_config)
        self.view.reset_shopify_config_button.config(command=self.reset_shopify_config)

    def get_selected_designs_for_export(self):
        """Lấy danh sách designs được chọn để export"""
        selected_design = self.view.get_selected_design()
        if selected_design == "All Designs":
            return self.scan_directory(self.designs_dir)
        else:
            return [selected_design] if selected_design else []

    def get_generated_mockup_files(self, output_folder):
        """Lấy danh sách file mockup đã generate trong output folder (scan subfolders)"""
        try:
            files = []
            
            # Ưu tiên scan theo design handle mapping nếu có
            if self.design_handle_mapping:
                for design_name, handle in self.design_handle_mapping.items():
                    design_folder = os.path.join(output_folder, handle)
                    if os.path.isdir(design_folder):
                        for file in os.listdir(design_folder):
                            if file.lower().endswith(('.jpg', '.png')):
                                # Tạo relative path: subfolder/filename
                                files.append(f"{handle}/{file}")
            else:
                # Fallback: scan tất cả subfolders nếu không có mapping
                for item in os.listdir(output_folder):
                    item_path = os.path.join(output_folder, item)
                    if os.path.isdir(item_path):
                        # Scan files trong design subfolder
                        for file in os.listdir(item_path):
                            if file.lower().endswith(('.jpg', '.png')):
                                # Tạo relative path: subfolder/filename
                                files.append(f"{item}/{file}")
                    elif item.lower().endswith(('.jpg', '.png')):
                        # File ở root level (backward compatibility)
                        files.append(item)
            
            return files
        except:
            return []

    def get_mockup_templates(self):
        """Lấy danh sách mockup templates từ thư mục mockups"""
        try:
            mockup_files = self.scan_directory(self.mockups_dir)
            return mockup_files
        except:
            return []

    def preview_csv(self):
        """Xem trước CSV data"""
        try:
            design_names = self.get_selected_designs_for_export()
            if not design_names:
                self.view.show_error("Preview Error", "Vui lòng chọn design để preview.")
                return

            output_folder = self.view.output_folder_var.get()
            if not output_folder:
                self.view.show_error("Preview Error", "Vui lòng chọn output folder.")
                return

            # Lấy mockup files có sẵn (giả sử đã generate)
            mockup_files = self.get_generated_mockup_files(output_folder)
            
            # Lấy mockup templates
            mockup_templates = self.get_mockup_templates()
            
            # Preview data với handle mapping
            preview_data = self.csv_exporter.preview_csv_data(
                design_names, mockup_files, output_folder, max_rows=5, 
                mockup_templates=mockup_templates, design_handle_mapping=self.design_handle_mapping
            )
            
            # Hiển thị preview window
            self.show_csv_preview_window(preview_data)
            
        except Exception as e:
            self.view.show_error("Preview Error", f"Lỗi khi preview CSV: {e}")

    def show_csv_preview_window(self, preview_data):
        """Hiển thị window preview CSV data"""
        preview_window = tk.Toplevel(self.view.parent)
        preview_window.title("CSV Preview")
        preview_window.geometry("800x400")
        
        # Create text widget with scrollbar
        text_frame = tk.Frame(preview_window)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        text_widget = tk.Text(text_frame, wrap=tk.NONE)
        v_scrollbar = tk.Scrollbar(text_frame, orient=tk.VERTICAL, command=text_widget.yview)
        h_scrollbar = tk.Scrollbar(text_frame, orient=tk.HORIZONTAL, command=text_widget.xview)
        
        text_widget.config(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        text_widget.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        v_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        h_scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        text_frame.columnconfigure(0, weight=1)
        text_frame.rowconfigure(0, weight=1)
        
        # Format and display data
        if preview_data:
            # Headers
            headers = list(preview_data[0].keys())
            header_line = "\t".join(headers) + "\n"
            text_widget.insert(tk.END, header_line)
            
            # Data rows
            for row in preview_data:
                data_line = "\t".join(str(row.get(header, "")) for header in headers) + "\n"
                text_widget.insert(tk.END, data_line)
        else:
            text_widget.insert(tk.END, "Không có dữ liệu để hiển thị.")
        
        text_widget.config(state=tk.DISABLED)

    def generate_mockups_only(self):
        """Generate mockups only (không export CSV)"""
        self.on_generate_button_pressed()

    def export_csv_only(self):
        """Export CSV only (không generate mockups)"""
        try:
            design_names = self.get_selected_designs_for_export()
            if not design_names:
                self.view.show_error("Export Error", "Vui lòng chọn design để export.")
                return

            output_folder = self.view.output_folder_var.get()
            if not output_folder:
                self.view.show_error("Export Error", "Vui lòng chọn output folder.")
                return

            # Lấy mockup files có sẵn
            mockup_files = self.get_generated_mockup_files(output_folder)
            
            if not mockup_files:
                self.view.show_error("Export Error", "Không tìm thấy mockup files trong output folder.\nVui lòng generate mockups trước.")
                return

            # Lấy mockup templates
            mockup_templates = self.get_mockup_templates()

            # Export CSV với handle mapping
            csv_path = self.csv_exporter.export_csv(
                design_names, mockup_files, output_folder, 
                mockup_templates=mockup_templates, design_handle_mapping=self.design_handle_mapping
            )
            
            # Hiển thị thống kê
            summary = self.csv_exporter.get_export_summary(design_names)
            message = f"CSV đã được export thành công!\n\nFile: {csv_path}\n\nThống kê:\n- {summary['total_designs']} designs\n- {summary['total_variants']} variants\n- {summary['total_products']} products"
            self.view.show_info("Export Success", message)
            
        except Exception as e:
            self.view.show_error("Export Error", f"Lỗi khi export CSV: {e}")

    def save_shopify_config(self):
        """Lưu Shopify configuration từ UI"""
        try:
            # Business info
            vendor = self.view.vendor_var.get()
            product_type = self.view.product_type_var.get()
            tags = self.view.tags_var.get()
            image_domain = self.view.image_domain_var.get()
            self.shopify_config.update_business_info(vendor, product_type, tags, image_domain)
            
            # Size configs
            for size, config_vars in self.view.size_configs.items():
                price = config_vars['price'].get()
                compare_price = config_vars['compare_price'].get()
                sku_suffix = config_vars['sku_suffix'].get()
                self.shopify_config.update_size_config(size, price, compare_price, sku_suffix)
            
            # Colors
            colors_text = self.view.colors_text.get("1.0", tk.END).strip()
            colors = [color.strip() for color in colors_text.split(",") if color.strip()]
            self.shopify_config.update_colors(colors)
            
            # SKU pattern
            sku_pattern = self.view.sku_pattern_var.get()
            self.shopify_config.update_sku_pattern(sku_pattern)
            
            # Description template
            description = self.view.description_text.get("1.0", tk.END).strip()
            self.shopify_config.update_description_template(description)
            
            # Save to file
            self.shopify_config.save_config()
            
            self.view.show_info("Config Saved", "Shopify configuration đã được lưu thành công!")
            
        except Exception as e:
            self.view.show_error("Save Error", f"Lỗi khi lưu Shopify config: {e}")

    def load_shopify_config(self):
        """Load Shopify configuration vào UI"""
        try:
            self.shopify_config.load_config()
            
            # Business info
            business_info = self.shopify_config.get_business_info()
            self.view.vendor_var.set(business_info.get("vendor", ""))
            self.view.product_type_var.set(business_info.get("product_type", ""))
            self.view.tags_var.set(business_info.get("tags", ""))
            self.view.image_domain_var.set(business_info.get("image_domain", "https://yourdomain.com/images"))
            
            # Size configs
            size_configs = self.shopify_config.get_size_configs()
            for size, config_vars in self.view.size_configs.items():
                if size in size_configs:
                    config_vars['price'].set(size_configs[size].get("price", ""))
                    config_vars['compare_price'].set(size_configs[size].get("compare_price", ""))
                    config_vars['sku_suffix'].set(size_configs[size].get("sku_suffix", ""))
            
            # Colors
            colors = self.shopify_config.get_colors()
            colors_text = ", ".join(colors)
            self.view.colors_text.delete("1.0", tk.END)
            self.view.colors_text.insert("1.0", colors_text)
            
            # SKU pattern
            sku_pattern = self.shopify_config.get_sku_pattern()
            self.view.sku_pattern_var.set(sku_pattern)
            
            # Description template
            description = self.shopify_config.get_description_template()
            self.view.description_text.delete("1.0", tk.END)
            self.view.description_text.insert("1.0", description)
            
            self.view.show_info("Config Loaded", "Shopify configuration đã được load thành công!")
            
        except Exception as e:
            self.view.show_error("Load Error", f"Lỗi khi load Shopify config: {e}")

    def reset_shopify_config(self):
        """Reset Shopify config về mặc định"""
        try:
            self.shopify_config.reset_to_default()
            self.load_shopify_config()  # Reload UI với config mặc định
            self.view.show_info("Config Reset", "Shopify configuration đã được reset về mặc định!")
            
        except Exception as e:
            self.view.show_error("Reset Error", f"Lỗi khi reset Shopify config: {e}") 