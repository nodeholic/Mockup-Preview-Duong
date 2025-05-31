 TÓM TẮT CHỨC NĂNG:
🎯 Core Features:

Auto-load mockups từ thư mục → hiển thị danh sách, mặc định chọn "All"
Auto-load designs từ thư mục → cho phép chọn design
Config system cho từng mockup (X, Y, Size) → lưu/load từ JSON
Dynamic preview hiển thị khung design theo đúng vị trí của mockup được chọn
Aspect ratio cho size theo tỷ lệ 4500:5400


📝 DANH SÁCH TASKS CẦN THỰC HIỆN:
🗂️ 1. File System Tasks:
✅ Task 1.1: Tạo function scan thư mục mockups (.jpg, .png)
✅ Task 1.2: Tạo function scan thư mục designs (.jpg, .png) 
✅ Task 1.3: Tạo function load/save JSON config
✅ Task 1.4: Tạo cấu trúc JSON config cho từng mockup
🎨 2. UI Components Tasks:
✅ Task 2.1: Modify danh sách mockup (thêm option "All Mockups")
✅ Task 2.2: Tạo dropdown/listbox cho designs
✅ Task 2.3: Modify slider Size theo tỷ lệ 4500:5400
✅ Task 2.4: Thêm buttons "Save Config" và "Load Config"
✅ Task 2.5: Update preview canvas hiển thị khung design
⚙️ 3. Logic & Event Handling Tasks:
✅ Task 3.1: Event handler khi chọn mockup → load config X,Y,Size
✅ Task 3.2: Event handler khi chọn design → update preview
✅ Task 3.3: Event handler khi thay đổi X,Y,Size → update preview + config
✅ Task 3.4: Function save current config to JSON
✅ Task 3.5: Function load config from JSON → update UI
🖼️ 4. Preview System Tasks:
✅ Task 4.1: Function hiển thị mockup image trên canvas
✅ Task 4.2: Function vẽ khung design theo X,Y,Size
✅ Task 4.3: Function update preview khi config thay đổi
✅ Task 4.4: Function scale image phù hợp với canvas
🔧 5. Data Management Tasks:
✅ Task 5.1: Tạo class/dict lưu trữ config cho từng mockup
✅ Task 5.2: Function validate config data
✅ Task 5.3: Function merge/update config khi có thay đổi
✅ Task 5.4: Function reset config về mặc định
🎛️ 6. Advanced Features Tasks:
✅ Task 6.1: Implement tỷ lệ 4500:5400 cho size slider
✅ Task 6.2: Auto-save config khi thay đổi
✅ Task 6.3: Validation input X,Y,Size hợp lệ
✅ Task 6.4: Error handling cho file operations

🔄 THỨ TỰ THỰC HIỆN ƯU TIÊN:
Phase 1 - Foundation:

Task 1.1, 1.2, 1.4 (File system & config structure)
Task 2.1, 2.2 (Basic UI components)

Phase 2 - Core Logic:

Task 3.1, 3.2 (Selection handlers)
Task 4.1, 4.2 (Preview system)

Phase 3 - Configuration:

Task 1.3, 3.4, 3.5 (Config save/load)
Task 5.1, 5.2 (Data management)

Phase 4 - Polish:

Task 6.1, 6.2, 6.3, 6.4 (Advanced features & validation)