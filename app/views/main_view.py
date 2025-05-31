# app/views/main_view.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk, ImageEnhance # Thêm ImageEnhance

class MainView(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding="10")
        self.parent = parent
        self.controller = None # Thêm tham chiếu đến controller
        self.grid(sticky=(tk.W, tk.E, tk.N, tk.S))
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=1)

        self.current_mockup_image = None # Để giữ tham chiếu đến ảnh mockup
        self.current_design_image = None # Để giữ tham chiếu đến ảnh design
        # Thuộc tính mới để lưu thông tin mockup trên canvas
        self.displayed_mockup_width = 0
        self.displayed_mockup_height = 0
        self.displayed_mockup_offset_x = 0
        self.displayed_mockup_offset_y = 0

        # --- Left Panel (Controls) ---
        left_panel = ttk.Frame(self, padding="5")
        left_panel.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        left_panel.rowconfigure(3, weight=1) # Allow controls_frame to expand if needed

        # --- Mockup Selection ---
        mockup_frame = ttk.LabelFrame(left_panel, text="Mockups", padding="10")
        mockup_frame.grid(row=0, column=0, padx=5, pady=5, sticky=(tk.W, tk.E, tk.N))
        self.mockup_list_var = tk.StringVar()
        self.mockup_list = ttk.Combobox(mockup_frame, textvariable=self.mockup_list_var, state="readonly")
        self.mockup_list["values"] = ["All Mockups"]
        self.mockup_list.current(0)
        self.mockup_list.pack(fill=tk.X)

        # --- Design Selection ---
        design_frame = ttk.LabelFrame(left_panel, text="Designs", padding="10")
        design_frame.grid(row=1, column=0, padx=5, pady=5, sticky=(tk.W, tk.E, tk.N))
        self.design_list_var = tk.StringVar()
        self.design_list = ttk.Combobox(design_frame, textvariable=self.design_list_var, state="readonly")
        self.design_list["values"] = ["All Designs"]
        self.design_list.current(0)
        self.design_list.pack(fill=tk.X)

        # --- Controls (X, Y, Size, Opacity) ---
        controls_frame = ttk.LabelFrame(left_panel, text="Controls", padding="10")
        controls_frame.grid(row=2, column=0, padx=5, pady=5, sticky=(tk.W, tk.E, tk.N))

        # Đăng ký các hàm validate mới
        vcmd_xy = (self.register(self._validate_xy_input), '%P')
        vcmd_size = (self.register(self._validate_size_input), '%P')
        vcmd_opacity = (self.register(self._validate_opacity_input), '%P') # Validate cho opacity

        ttk.Label(controls_frame, text="X:").grid(row=0, column=0, sticky=tk.W, padx=2, pady=2)
        self.x_var = tk.DoubleVar()
        self.x_scale = ttk.Scale(controls_frame, from_=0, to=100, orient=tk.HORIZONTAL, variable=self.x_var)
        self.x_scale.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=2, pady=2)
        self.x_entry = ttk.Entry(controls_frame, textvariable=self.x_var, width=5, name="x_entry", validate='key', validatecommand=vcmd_xy)
        self.x_entry.grid(row=0, column=2, sticky=tk.E, padx=2, pady=2)
        self.x_entry.bind("<KeyRelease>", self._on_xy_entry_changed) # Binding mới

        ttk.Label(controls_frame, text="Y:").grid(row=1, column=0, sticky=tk.W, padx=2, pady=2)
        self.y_var = tk.DoubleVar()
        self.y_scale = ttk.Scale(controls_frame, from_=0, to=100, orient=tk.HORIZONTAL, variable=self.y_var)
        self.y_scale.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=2, pady=2)
        self.y_entry = ttk.Entry(controls_frame, textvariable=self.y_var, width=5, name="y_entry", validate='key', validatecommand=vcmd_xy)
        self.y_entry.grid(row=1, column=2, sticky=tk.E, padx=2, pady=2)
        self.y_entry.bind("<KeyRelease>", self._on_xy_entry_changed) # Binding mới

        ttk.Label(controls_frame, text="Size (Width):").grid(row=2, column=0, sticky=tk.W, padx=2, pady=2)
        self.size_var = tk.DoubleVar(value=50.0)
        self.size_scale = ttk.Scale(controls_frame, from_=10, to=100, orient=tk.HORIZONTAL, variable=self.size_var)
        self.size_scale.grid(row=2, column=1, sticky=(tk.W, tk.E), padx=2, pady=2)
        self.size_entry = ttk.Entry(controls_frame, textvariable=self.size_var, width=5, name="size_entry", validate='key', validatecommand=vcmd_size)
        self.size_entry.grid(row=2, column=2, sticky=tk.E, padx=2, pady=2)
        self.size_entry.bind("<KeyRelease>", self._on_size_entry_changed) # Binding mới

        # Thêm điều khiển Opacity
        ttk.Label(controls_frame, text="Opacity:").grid(row=3, column=0, sticky=tk.W, padx=2, pady=2)
        self.opacity_var = tk.DoubleVar(value=100.0)
        self.opacity_scale = ttk.Scale(controls_frame, from_=0, to=100, orient=tk.HORIZONTAL, variable=self.opacity_var)
        self.opacity_scale.grid(row=3, column=1, sticky=(tk.W, tk.E), padx=2, pady=2)
        self.opacity_entry = ttk.Entry(controls_frame, textvariable=self.opacity_var, width=5, name="opacity_entry", validate='key', validatecommand=vcmd_opacity)
        self.opacity_entry.grid(row=3, column=2, sticky=tk.E, padx=2, pady=2)
        self.opacity_entry.bind("<KeyRelease>", self._on_opacity_entry_changed) # Binding mới

        controls_frame.columnconfigure(1, weight=1)
        
        # --- Output Folder Selection (Task 9.4) ---
        output_frame = ttk.LabelFrame(left_panel, text="Output Settings", padding="10")
        output_frame.grid(row=4, column=0, padx=5, pady=5, sticky=(tk.W, tk.E, tk.N))
        
        ttk.Label(output_frame, text="Output Folder:").grid(row=0, column=0, sticky=tk.W, padx=2, pady=2)
        self.output_folder_var = tk.StringVar()
        self.output_folder_entry = ttk.Entry(output_frame, textvariable=self.output_folder_var, width=30)
        self.output_folder_entry.grid(row=1, column=0, sticky=(tk.W, tk.E), padx=2, pady=2)
        self.browse_output_button = ttk.Button(output_frame, text="Browse...")
        self.browse_output_button.grid(row=1, column=1, sticky=tk.E, padx=2, pady=2)

        output_frame.columnconfigure(0, weight=1)

        # --- Config Buttons & Generate Button ---
        action_buttons_frame = ttk.Frame(left_panel, padding="5")
        action_buttons_frame.grid(row=5, column=0, padx=5, pady=5, sticky=(tk.W, tk.E, tk.S))

        self.save_config_button = ttk.Button(action_buttons_frame, text="Save Config")
        self.save_config_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.load_config_button = ttk.Button(action_buttons_frame, text="Load Config")
        self.load_config_button.pack(side=tk.LEFT, padx=5, pady=5)

        # Task 9.1: Generate Button
        self.generate_button = ttk.Button(action_buttons_frame, text="Generate Image", style="Accent.TButton") # Added style
        self.generate_button.pack(side=tk.LEFT, padx=10, pady=5, expand=True, fill=tk.X)

        # Task 9.2: Progress Bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(left_panel, variable=self.progress_var, maximum=100)
        self.progress_bar.grid(row=6, column=0, padx=5, pady=(10,5), sticky=(tk.W, tk.E, tk.S))

        # --- Right Panel (Preview) ---
        preview_frame = ttk.LabelFrame(self, text="Preview", padding="10")
        preview_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.preview_canvas = tk.Canvas(preview_frame, bg="lightgrey", width=450, height=540)
        self.preview_canvas.pack(expand=True, fill=tk.BOTH)
        
        # Configure main frame columns/rows to resize
        self.columnconfigure(0, weight=0) # Left panel fixed width (or based on content)
        self.columnconfigure(1, weight=1) # Preview panel expands
        self.rowconfigure(0, weight=1)

        # Style for the Generate button (Accent.TButton might need a theme like 'azure')
        style = ttk.Style(self.parent) # Get style from parent (root window)
        
        available_themes = style.theme_names()
        # print(f"Available themes: {available_themes}")
        # print(f"Current theme: {style.theme_use()}")

        if 'clam' in available_themes:
            try:
                style.theme_use('clam')
                # print("Using 'clam' theme.")
            except tk.TclError:
                print("Failed to apply 'clam' theme, using default.")
        
        # Configure the Accent.TButton style
        # Some themes define Accent.TButton, others don't. This provides a fallback.
        style.configure("Accent.TButton", font=("TkDefaultFont", 10, "bold"), 
                        foreground="white", background="#28a745", 
                        padding=(10, 5)) # Added padding (left/right, top/bottom)
        
        # Ensure the button uses this style. The style name was already set during button creation.
        # self.generate_button.configure(style="Accent.TButton") # Re-apply if needed, but usually not

    def set_controller(self, controller):
        self.controller = controller

    def _on_xy_entry_changed(self, event=None): # event được truyền bởi bind
        if self.controller:
            # Gọi hàm trong controller để xử lý thay đổi X hoặc Y từ Entry
            # Controller sẽ đọc giá trị từ x_var hoặc y_var và gọi on_controls_changed
            self.controller.handle_xy_entry_change()

    def _on_size_entry_changed(self, event=None):
        if self.controller:
            # Gọi hàm trong controller để xử lý thay đổi Size từ Entry
            self.controller.handle_size_entry_change()

    def _on_opacity_entry_changed(self, event=None): # Hàm mới cho opacity entry
        if self.controller:
            self.controller.handle_opacity_entry_change()

    def _validate_xy_input(self, P_value):
        if P_value == "": 
            return True
        try:
            val = float(P_value)
            if 0.0 <= val <= 100.0:
                return True
        except ValueError:
            pass # Sẽ return False bên dưới nếu không hợp lệ
        self.bell()
        return False

    def _validate_size_input(self, P_value):
        if P_value == "": 
            return True
        try:
            val = float(P_value)
            if 10.0 <= val <= 100.0: 
                return True
        except ValueError:
            pass # Sẽ return False bên dưới nếu không hợp lệ
        self.bell()
        return False

    def _validate_opacity_input(self, P_value): # Hàm validate mới cho opacity
        if P_value == "": 
            return True
        try:
            val = float(P_value)
            if 0.0 <= val <= 100.0: 
                return True
        except ValueError:
            pass
        self.bell()
        return False

    # Methods để update UI sẽ được thêm ở đây
    def update_mockup_dropdown(self, mockup_files):
        self.mockup_list["values"] = ["All Mockups"] + mockup_files
        if mockup_files:
            self.mockup_list.current(0) # Mặc định chọn "All Mockups"

    def update_design_dropdown(self, design_files):
        self.design_list["values"] = ["All Designs"] + design_files
        if not design_files:
            self.design_list.current(0)
        elif self.design_list_var.get() not in self.design_list["values"]:
            self.design_list.current(0)
        current_selection = self.design_list_var.get()
        new_values = self.design_list["values"]
        if current_selection in new_values:
            self.design_list.current(new_values.index(current_selection))
        else:
            self.design_list.current(0)

    def update_controls(self, x, y, size, opacity): # Thêm opacity
        self.x_var.set(float(x))
        self.y_var.set(float(y))
        self.size_var.set(float(size))
        self.opacity_var.set(float(opacity)) # Đặt giá trị opacity

    def get_selected_mockup(self):
        return self.mockup_list_var.get()

    def get_selected_design(self):
        return self.design_list_var.get()

    def show_error(self, title, message):
        messagebox.showerror(title, message)

    def show_info(self, title, message):
        messagebox.showinfo(title, message)

    # Placeholder cho các hàm vẽ lên canvas
    def draw_mockup_on_canvas(self, image_path):
        self.preview_canvas.delete("mockup_image")
        # Reset thông tin mockup hiển thị
        self.displayed_mockup_width = 0
        self.displayed_mockup_height = 0
        self.displayed_mockup_offset_x = 0
        self.displayed_mockup_offset_y = 0

        if image_path:
            try:
                img = Image.open(image_path)
                canvas_width = self.preview_canvas.winfo_width()
                canvas_height = self.preview_canvas.winfo_height()

                if canvas_width <= 1 or canvas_height <= 1: # Canvas chưa sẵn sàng
                    self.parent.after(100, lambda: self.draw_mockup_on_canvas(image_path))
                    return

                # Tạo bản sao để thumbnail không ảnh hưởng đến img gốc nếu cần sau này
                img_for_thumb = img.copy()
                img_for_thumb.thumbnail((canvas_width, canvas_height), Image.Resampling.LANCZOS)
                
                # Lưu kích thước thực của ảnh mockup sau khi thumbnail
                self.displayed_mockup_width = img_for_thumb.width
                self.displayed_mockup_height = img_for_thumb.height

                # Tính toán offset để căn giữa ảnh trên canvas
                self.displayed_mockup_offset_x = (canvas_width - self.displayed_mockup_width) // 2
                self.displayed_mockup_offset_y = (canvas_height - self.displayed_mockup_height) // 2
                
                self.current_mockup_image = ImageTk.PhotoImage(img_for_thumb)
                # Vẽ ảnh tại offset đã tính, không phải (0,0)
                self.preview_canvas.create_image(
                    self.displayed_mockup_offset_x, 
                    self.displayed_mockup_offset_y, 
                    anchor=tk.NW, 
                    image=self.current_mockup_image, 
                    tags="mockup_image"
                )
                # print(f"Drawing mockup: {image_path} at ({self.displayed_mockup_offset_x},{self.displayed_mockup_offset_y}) size {self.displayed_mockup_width}x{self.displayed_mockup_height}")
            except FileNotFoundError:
                self.show_error("Image Error", f"Mockup image not found: {image_path}")
                self.current_mockup_image = None
            except Exception as e:
                self.show_error("Image Error", f"Could not load mockup image {image_path}: {e}")
                self.current_mockup_image = None
        else:
            self.current_mockup_image = None # Xóa tham chiếu
            # Các giá trị displayed_mockup_* đã được reset ở đầu hàm
            print("Cleared mockup image from canvas")

    def draw_design_frame_on_canvas(self, x, y, width, height, design_image_path=None):
        self.preview_canvas.delete("design_frame")
        self.preview_canvas.delete("design_image") # Xóa ảnh design cũ
        self.current_design_image = None

        if width > 0 and height > 0:
            # Vẽ khung đỏ (design area boundary)
            self.preview_canvas.create_rectangle(x, y, x + width, y + height, outline="red", width=2, tags="design_frame")
            # print(f"Drawing design frame at ({x},{y}) with size ({width}x{height})")

            if design_image_path:
                try:
                    with Image.open(design_image_path) as design_img_original:
                        original_w, original_h = design_img_original.size
                        if original_w == 0 or original_h == 0: return # Skip if image is invalid

                        # --- Logic Smart Fitting cho Preview Canvas (tương tự MainController._fit_design_to_target) ---
                        target_preview_w = int(width)
                        target_preview_h = int(height)
                        
                        original_aspect_ratio = original_w / original_h
                        target_preview_aspect_ratio = target_preview_w / target_preview_h

                        if original_aspect_ratio > target_preview_aspect_ratio: # Design rộng hơn khung -> fit theo chiều rộng khung
                            new_preview_w = target_preview_w
                            new_preview_h = int(new_preview_w / original_aspect_ratio)
                        else: # Design cao hơn hoặc bằng tỷ lệ khung -> fit theo chiều cao khung
                            new_preview_h = target_preview_h
                            new_preview_w = int(new_preview_h * original_aspect_ratio)
                        
                        # Đảm bảo kích thước mới không phải là zero
                        if new_preview_w <= 0 or new_preview_h <= 0:
                             return

                        resized_design_for_preview = design_img_original.resize((new_preview_w, new_preview_h), Image.Resampling.LANCZOS)

                        # Tạo ảnh tạm RGBA với kích thước của khung preview để đặt design đã resize vào
                        # Nền trong suốt để thấy mockup phía sau phần letterbox/pillarbox
                        final_fitted_preview_design = Image.new('RGBA', (target_preview_w, target_preview_h), (0,0,0,0)) 
                        
                        paste_preview_x = (target_preview_w - new_preview_w) // 2
                        # Điều chỉnh vị trí dán Y để align top nếu design được letterbox theo chiều dọc
                        if original_aspect_ratio > target_preview_aspect_ratio: # Design rộng hơn/vuông (letterbox dọc)
                            paste_preview_y = 0 # Align top
                        else: # Design cao hơn (pillarbox ngang) hoặc vừa khít
                            paste_preview_y = (target_preview_h - new_preview_h) // 2 # Align center theo chiều Y
                        
                        final_fitted_preview_design.paste(resized_design_for_preview, (paste_preview_x, paste_preview_y))
                        # --- Kết thúc logic Smart Fitting cho Preview ---

                        # Áp dụng Opacity
                        opacity_percent = self.opacity_var.get() # Lấy % từ 0-100
                        alpha_value = int((opacity_percent / 100.0) * 255) # Chuyển sang 0-255

                        if final_fitted_preview_design.mode != 'RGBA':
                             final_fitted_preview_design = final_fitted_preview_design.convert('RGBA')
                        
                        alpha = final_fitted_preview_design.split()[3]
                        # Điều chỉnh kênh alpha của ảnh design đã fit.
                        # Các pixel hoàn toàn trong suốt (alpha=0) sẽ vẫn trong suốt.
                        # Các pixel không trong suốt (alpha > 0) sẽ có alpha mới = original_alpha * (opacity_percent / 100)
                        datas = final_fitted_preview_design.getdata()
                        newData = []
                        for item in datas:
                            # item[3] is the alpha channel
                            new_alpha = int(item[3] * (opacity_percent / 100.0))
                            newData.append((item[0], item[1], item[2], new_alpha))
                        final_fitted_preview_design.putdata(newData)

                        self.current_design_image = ImageTk.PhotoImage(final_fitted_preview_design)
                        # Vẽ ảnh design đã được fit (với letterbox/pillarbox nếu cần) lên canvas tại tọa độ của khung đỏ
                        self.preview_canvas.create_image(x, y, anchor=tk.NW, image=self.current_design_image, tags="design_image")
                        # print(f"Overlaying design: {design_image_path} with smart fit")

                except FileNotFoundError:
                    self.show_error("Image Error", f"Design image not found: {design_image_path}")
                except Exception as e:
                    self.show_error("Image Error", f"Could not load/process design image {design_image_path} for preview: {e}")
        # else:
            # print("Skipped drawing design frame due to zero width/height.")

    def update_progress(self, value):
        self.progress_var.set(value)
        self.parent.update_idletasks() # Force UI update

    def reset_progress(self):
        self.progress_var.set(0)
        self.parent.update_idletasks() 