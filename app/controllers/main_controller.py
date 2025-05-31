# app/controllers/main_controller.py
import os
import datetime # For timestamp in filename (Task 12.5)
import threading # For progress bar updates during batch (Task 9.2)
from tkinter import filedialog
import tkinter as tk # <--- Thêm dòng này
from PIL import Image, ImageOps # ImageOps for letterboxing/pillarboxing (Task 7.3)
# Giả sử các lớp này đã được định nghĩa trong các tệp tương ứng
# from app.views.main_view import MainView (Sẽ import trong App)
# from app.models.config_manager import ConfigManager (Sẽ import trong App)

# Define fixed output size (Task: Fixed output size)
OUTPUT_WIDTH = 1200
OUTPUT_HEIGHT = 1200
OUTPUT_BACKGROUND_COLOR = (255, 255, 255, 255) # White background for letterboxing, RGBA

class MainController:
    def __init__(self, view, config_manager):
        self.view = view
        self.config_manager = config_manager
        self.mockups_dir = "mockups/"
        self.designs_dir = "designs/"
        self.output_dir = "output/" # Default output directory
        self.view.output_folder_var.set(self.output_dir)

        self._setup_event_handlers()
        self.load_initial_data()
        os.makedirs(self.output_dir, exist_ok=True) # Ensure default output dir exists

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

        # New event handlers for Generate and Output Folder (Task 9.1, 9.4)
        self.view.generate_button.config(command=self.on_generate_button_pressed)
        self.view.browse_output_button.config(command=self.browse_output_folder)

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
            mockup_image_path = os.path.join(self.mockups_dir, selected_mockup)
            self.view.draw_mockup_on_canvas(mockup_image_path)
        elif selected_mockup == "All Mockups":
            self.view.draw_mockup_on_canvas(None) # Xóa mockup khỏi canvas
            self.view.update_controls(0,0,50) # Reset controls, hoặc giá trị mặc định khác
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
        x_pos = self.view.x_var.get()
        y_pos = self.view.y_var.get()
        frame_width_percent = self.view.size_var.get()

        canvas_width = self.view.preview_canvas.winfo_width()
        canvas_height = self.view.preview_canvas.winfo_height()

        if canvas_width <= 1 or canvas_height <= 1: 
            self.view.after(100, self.update_preview)
            return

        actual_x = (x_pos / 100) * canvas_width
        actual_y = (y_pos / 100) * canvas_height
        frame_actual_width = (frame_width_percent / 100) * canvas_width
        
        aspect_ratio = self.config_manager.get_aspect_ratio()
        frame_actual_height = frame_actual_width / aspect_ratio 

        if actual_y + frame_actual_height > canvas_height:
            frame_actual_height = canvas_height - actual_y
            frame_actual_width = frame_actual_height * aspect_ratio
        
        if actual_x + frame_actual_width > canvas_width:
            frame_actual_width = canvas_width - actual_x
            frame_actual_height = frame_actual_width / aspect_ratio

        selected_design_name = self.view.get_selected_design()
        design_image_path = None
        # Chỉ tạo đường dẫn design nếu một design cụ thể được chọn
        if selected_design_name and selected_design_name != "All Designs":
            design_image_path = os.path.join(self.designs_dir, selected_design_name)

        # Kiểm tra xem có mockup nào được chọn không (trừ "All Mockups")
        # Chỉ vẽ khung design nếu có mockup đang hiển thị (không phải "All Mockups")
        current_mockup = self.view.get_selected_mockup()
        if current_mockup and current_mockup != "All Mockups":
            self.view.draw_design_frame_on_canvas(actual_x, actual_y, frame_actual_width, frame_actual_height, design_image_path)
        else:
            # Nếu "All Mockups" được chọn hoặc không có mockup nào, xóa khung design/design
            self.view.draw_design_frame_on_canvas(0, 0, 0, 0, None) # Hoặc một cách clear khác

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

    def generate_single_image(self, mockup_name, design_name, output_folder):
        """ Task 12.1: Generates a single composite image. """
        print(f"Generating image for Mockup: {mockup_name}, Design: {design_name}")

        mockup_path = os.path.join(self.mockups_dir, mockup_name)
        design_path = os.path.join(self.designs_dir, design_name)

        config = self.config_manager.get_mockup_config(mockup_name)
        if not config:
            self.view.show_error("Config Error", f"No configuration found for mockup: {mockup_name}")
            return False # Indicate failure

        x_percent, y_percent, size_w_percent = config.get('x',0), config.get('y',0), config.get('size',50)
        design_area_aspect_ratio_wh = self.config_manager.get_aspect_ratio() 

        target_rect = self._get_design_target_rect_on_full_mockup(
            mockup_path, x_percent, y_percent, size_w_percent, design_area_aspect_ratio_wh
        )
        if not target_rect:
            return False
        
        target_x, target_y, target_w, target_h = target_rect
        if target_w <= 0 or target_h <= 0:
            self.view.show_error("Generate Error", f"Calculated design area for {mockup_name} has zero or negative size.")
            return False

        fitted_design_img = self._fit_design_to_target(design_path, target_w, target_h)
        if not fitted_design_img:
            return False

        try:
            full_mockup_img = Image.open(mockup_path).convert("RGBA")
            
            # Create a working copy for compositing to keep original full_mockup_img if needed elsewhere
            composite_img = full_mockup_img.copy()
            composite_img.paste(fitted_design_img, (target_x, target_y), fitted_design_img)

            # --- Resize composite image to fixed output size (e.g., 1200x1200) with letterboxing ---
            final_output_image = Image.new('RGBA', (OUTPUT_WIDTH, OUTPUT_HEIGHT), OUTPUT_BACKGROUND_COLOR)
            img_copy = composite_img.copy()
            img_copy.thumbnail((OUTPUT_WIDTH, OUTPUT_HEIGHT), Image.Resampling.LANCZOS)
            
            # Calculate position to paste the thumbnail onto the background (centered)
            paste_pos_x = (OUTPUT_WIDTH - img_copy.width) // 2
            paste_pos_y = (OUTPUT_HEIGHT - img_copy.height) // 2
            final_output_image.paste(img_copy, (paste_pos_x, paste_pos_y), img_copy if img_copy.mode == 'RGBA' else None)
            # --- End of resize logic ---

            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            mockup_base = os.path.splitext(mockup_name)[0]
            design_base = os.path.splitext(design_name)[0]
            output_filename = f"{mockup_base}_{design_base}_{timestamp}.png"
            output_path = os.path.join(output_folder, output_filename)

            final_output_image.save(output_path, "PNG")
            print(f"Saved as {output_path} (Size: {OUTPUT_WIDTH}x{OUTPUT_HEIGHT})") # Print to console instead of alert
            # self.view.show_info("Image Generated", f"Saved as {output_path}") # Removed as per request
            return True # Indicate success

        except FileNotFoundError:
            self.view.show_error("Image Error", f"File not found during final composition: {mockup_path} or {design_path}")
            return False
        except Exception as e:
            self.view.show_error("Generation Error", f"Failed to generate image for {mockup_name}: {e}")
            return False

    # --- End of Phase 2 Logic ---

    # --- Start of Batch Processing Logic (Phase 3) ---
    def generate_batch_all_mockups_one_design(self, design_name, output_folder, threaded=False):
        """ Task 8.5 / 12.2: Generate all mockups with the selected design. """
        mockup_files = self.scan_directory(self.mockups_dir)
        if not mockup_files:
            self.view.show_error("Batch Generate Error", "No mockup files found.")
            if threaded: self.view.after(0, lambda: self.view.generate_button.config(state=tk.NORMAL))
            return
        
        total_mockups = len(mockup_files)
        print(f"Starting batch generation for {total_mockups} mockups with design {design_name}...")
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
        if threaded:
            self.view.after(0, lambda: self.view.show_info("Batch Complete", final_message))
            self.view.after(0, lambda: self.view.generate_button.config(state=tk.NORMAL))
            self.view.after(100, self.view.reset_progress) 
        else:
            self.view.show_info("Batch Complete", final_message)

    def generate_batch_one_mockup_all_designs(self, mockup_name, output_folder, threaded=False):
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
        if threaded:
            self.view.after(0, lambda: self.view.show_info("Batch Complete", final_message))
            self.view.after(0, lambda: self.view.generate_button.config(state=tk.NORMAL))
            self.view.after(100, self.view.reset_progress)
        else:
            self.view.show_info("Batch Complete", final_message)

    def generate_batch_all_combinations(self, output_folder, threaded=False):
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
        if threaded:
            self.view.after(0, lambda: self.view.show_info("Batch Complete", final_message))
            self.view.after(0, lambda: self.view.generate_button.config(state=tk.NORMAL))
            self.view.after(100, self.view.reset_progress)
        else:
            self.view.show_info("Batch Complete", final_message)

    # --- Other batch functions (12.3, 12.4) can be added here ---
    # def generate_batch_one_mockup_all_designs(...)
    # def generate_batch_all_combinations(...) 