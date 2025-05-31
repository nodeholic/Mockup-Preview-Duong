# app/views/main_view.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk # Thêm import cho Pillow

class MainView(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding="10")
        self.parent = parent
        self.grid(sticky=(tk.W, tk.E, tk.N, tk.S))
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=1)

        self.current_mockup_image = None # Để giữ tham chiếu đến ảnh mockup
        self.current_design_image = None # Để giữ tham chiếu đến ảnh design

        # Placeholder cho các thành phần UI
        # Ví dụ: danh sách mockup, danh sách design, thanh trượt, canvas preview

        # --- Mockup Selection ---
        mockup_frame = ttk.LabelFrame(self, text="Mockups", padding="10")
        mockup_frame.grid(row=0, column=0, padx=5, pady=5, sticky=(tk.W, tk.E, tk.N))
        self.mockup_list_var = tk.StringVar()
        self.mockup_list = ttk.Combobox(mockup_frame, textvariable=self.mockup_list_var, state="readonly")
        self.mockup_list["values"] = ["All Mockups"]
        self.mockup_list.current(0)
        self.mockup_list.pack(fill=tk.X)

        # --- Design Selection ---
        design_frame = ttk.LabelFrame(self, text="Designs", padding="10")
        design_frame.grid(row=1, column=0, padx=5, pady=5, sticky=(tk.W, tk.E, tk.N))
        self.design_list_var = tk.StringVar()
        self.design_list = ttk.Combobox(design_frame, textvariable=self.design_list_var, state="readonly")
        self.design_list.pack(fill=tk.X)

        # --- Controls (X, Y, Size) ---
        controls_frame = ttk.LabelFrame(self, text="Controls", padding="10")
        controls_frame.grid(row=2, column=0, padx=5, pady=5, sticky=(tk.W, tk.E, tk.N))

        vcmd = (self.register(self._validate_input), '%P', '%W') # %P: new value, %W: widget name

        ttk.Label(controls_frame, text="X:").grid(row=0, column=0, sticky=tk.W, padx=2, pady=2)
        self.x_var = tk.IntVar()
        self.x_scale = ttk.Scale(controls_frame, from_=0, to=100, orient=tk.HORIZONTAL, variable=self.x_var)
        self.x_scale.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=2, pady=2)
        self.x_entry = ttk.Entry(controls_frame, textvariable=self.x_var, width=5, name="x_entry", validate='key', validatecommand=vcmd)
        self.x_entry.grid(row=0, column=2, sticky=tk.E, padx=2, pady=2)

        ttk.Label(controls_frame, text="Y:").grid(row=1, column=0, sticky=tk.W, padx=2, pady=2)
        self.y_var = tk.IntVar()
        self.y_scale = ttk.Scale(controls_frame, from_=0, to=100, orient=tk.HORIZONTAL, variable=self.y_var)
        self.y_scale.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=2, pady=2)
        self.y_entry = ttk.Entry(controls_frame, textvariable=self.y_var, width=5, name="y_entry", validate='key', validatecommand=vcmd)
        self.y_entry.grid(row=1, column=2, sticky=tk.E, padx=2, pady=2)

        ttk.Label(controls_frame, text="Size (Width):").grid(row=2, column=0, sticky=tk.W, padx=2, pady=2)
        self.size_var = tk.IntVar(value=50)
        self.size_scale = ttk.Scale(controls_frame, from_=10, to=100, orient=tk.HORIZONTAL, variable=self.size_var)
        self.size_scale.grid(row=2, column=1, sticky=(tk.W, tk.E), padx=2, pady=2)
        self.size_entry = ttk.Entry(controls_frame, textvariable=self.size_var, width=5, name="size_entry", validate='key', validatecommand=vcmd)
        self.size_entry.grid(row=2, column=2, sticky=tk.E, padx=2, pady=2)

        controls_frame.columnconfigure(1, weight=1)

        # --- Preview Canvas ---
        preview_frame = ttk.LabelFrame(self, text="Preview", padding="10")
        preview_frame.grid(row=0, column=1, rowspan=3, padx=5, pady=5, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.preview_canvas = tk.Canvas(preview_frame, bg="lightgrey", width=450, height=540)
        self.preview_canvas.pack(expand=True, fill=tk.BOTH)

        # --- Config Buttons ---
        config_button_frame = ttk.Frame(self, padding="5")
        config_button_frame.grid(row=3, column=0, columnspan=2, padx=5, pady=5, sticky=(tk.W, tk.E))

        self.save_config_button = ttk.Button(config_button_frame, text="Save Config")
        self.save_config_button.pack(side=tk.LEFT, padx=5)

        self.load_config_button = ttk.Button(config_button_frame, text="Load Config")
        self.load_config_button.pack(side=tk.LEFT, padx=5)

        self.columnconfigure(1, weight=1)
        self.rowconfigure(2, weight=1) # Để preview canvas có thể mở rộng

    def _validate_input(self, P, W_name):
        # P is the value of the entry if the edit is allowed
        # W_name is the widget name
        if P == "":  # Allow empty string for intermediate editing
            return True
        try:
            val = int(P)
            widget = self.nametowidget(W_name)
            if widget.winfo_name() == "x_entry" or widget.winfo_name() == "y_entry":
                if 0 <= val <= 100:
                    return True
                self.bell() # Sound a bell for invalid input
                return False
            elif widget.winfo_name() == "size_entry":
                if 10 <= val <= 100: # Assuming size has a different range
                    return True
                self.bell()
                return False
        except ValueError:
            self.bell()
            return False # Not an integer
        return False # Should not reach here

    # Methods để update UI sẽ được thêm ở đây
    def update_mockup_dropdown(self, mockup_files):
        self.mockup_list["values"] = ["All Mockups"] + mockup_files
        if mockup_files:
            self.mockup_list.current(0) # Mặc định chọn "All Mockups"

    def update_design_dropdown(self, design_files):
        self.design_list["values"] = design_files
        if design_files:
            self.design_list.current(0)

    def update_controls(self, x, y, size):
        self.x_var.set(int(x))
        self.y_var.set(int(y))
        self.size_var.set(int(size))

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
        self.preview_canvas.delete("mockup_image") # Xóa ảnh mockup cũ
        if image_path:
            try:
                img = Image.open(image_path)
                # Scale ảnh để vừa với canvas preview mà vẫn giữ tỷ lệ
                canvas_width = self.preview_canvas.winfo_width()
                canvas_height = self.preview_canvas.winfo_height()

                if canvas_width <= 1 or canvas_height <= 1: # Canvas chưa sẵn sàng
                    self.parent.after(100, lambda: self.draw_mockup_on_canvas(image_path))
                    return

                img.thumbnail((canvas_width, canvas_height), Image.Resampling.LANCZOS)
                
                self.current_mockup_image = ImageTk.PhotoImage(img)
                self.preview_canvas.create_image(0, 0, anchor=tk.NW, image=self.current_mockup_image, tags="mockup_image")
                print(f"Drawing mockup: {image_path} with size {img.width}x{img.height}")
            except FileNotFoundError:
                self.show_error("Image Error", f"Mockup image not found: {image_path}")
                self.current_mockup_image = None
            except Exception as e:
                self.show_error("Image Error", f"Could not load mockup image {image_path}: {e}")
                self.current_mockup_image = None
        else:
            self.current_mockup_image = None # Xóa tham chiếu
            print("Cleared mockup image from canvas")

    def draw_design_frame_on_canvas(self, x, y, width, height, design_image_path=None):
        self.preview_canvas.delete("design_frame")
        self.preview_canvas.delete("design_image") # Xóa ảnh design cũ
        self.current_design_image = None

        if width > 0 and height > 0:
            self.preview_canvas.create_rectangle(x, y, x + width, y + height, outline="red", width=2, tags="design_frame")
            print(f"Drawing design frame at ({x},{y}) with size ({width}x{height})")

            if design_image_path:
                try:
                    img = Image.open(design_image_path)
                    # Resize ảnh design để vừa khít với khung (width, height)
                    # Cẩn thận, việc này có thể làm méo ảnh nếu tỷ lệ khung khác tỷ lệ ảnh design
                    # Nếu muốn giữ tỷ lệ design, cần logic phức tạp hơn (ví dụ: letterboxing/cropping)
                    img_resized = img.resize((int(width), int(height)), Image.Resampling.LANCZOS)
                    
                    self.current_design_image = ImageTk.PhotoImage(img_resized)
                    self.preview_canvas.create_image(x, y, anchor=tk.NW, image=self.current_design_image, tags="design_image")
                    print(f"Overlaying design: {design_image_path}")
                except FileNotFoundError:
                    self.show_error("Image Error", f"Design image not found: {design_image_path}")
                except Exception as e:
                    self.show_error("Image Error", f"Could not load design image {design_image_path}: {e}")
        else:
            print("Skipped drawing design frame due to zero width/height.") 