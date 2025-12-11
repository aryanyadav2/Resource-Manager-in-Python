import customtkinter as ctk
import tkinter as tk
import psutil
import time
import threading

# --- CONFIGURATION ---
COLOR_BG = "#020202"       # Almost pure black (OLED vibe)
COLOR_ACCENT_1 = "#00f2ea" # Cyan (CPU)
COLOR_ACCENT_2 = "#ff0055" # Pink (RAM)
COLOR_ACCENT_3 = "#00ff41" # Matrix Green (Disk)
COLOR_TEXT_DIM = "#444444" # For subtle labels

# AESTHETIC FONTS
FONT_BIG = ("Consolas", 48, "bold")    # The "Digital" looking font for numbers
FONT_TITLE = ("Consolas", 14, "bold")  # Techy headers
FONT_LOGS = ("Consolas", 10)           # Terminal text

ctk.set_appearance_mode("Dark")

class RealSnakeBorder(tk.Canvas):
    """
    Renders a glowing line that physically wraps around the corners of the box.
    """
    def __init__(self, parent, width, height, color, **kwargs):
        super().__init__(parent, width=width, height=height, bg=COLOR_BG, highlightthickness=0, **kwargs)
        
        self.w = width
        self.h = height
        self.color = color
        self.snake_len = 150
        self.pos = 0 
        self.speed = 8
        self.perimeter = 2 * (self.w + self.h)
        
        # Inner content frame
        self.inner_frame = ctk.CTkFrame(self, width=self.w-4, height=self.h-4, fg_color="#0a0a0a", corner_radius=0)
        self.inner_frame.place(x=2, y=2)
        
        self.animate()

    def get_coords_at_distance(self, d):
        d = d % self.perimeter
        if d < self.w: return d, 0                        # Top
        elif d < self.w + self.h: return self.w, d - self.w  # Right
        elif d < self.w + self.h + self.w: return self.w - (d - (self.w + self.h)), self.h # Bottom
        else: return 0, self.h - (d - (2 * self.w + self.h)) # Left

    def animate(self):
        self.delete("snake") 
        
        points = []
        # Calculate snake body points to handle corners perfectly
        for i in range(int(self.pos - self.snake_len), int(self.pos), 5):
            x, y = self.get_coords_at_distance(i)
            points.append(x)
            points.append(y)
            
        # Add head
        hx, hy = self.get_coords_at_distance(self.pos)
        points.append(hx)
        points.append(hy)

        if len(points) >= 4:
            self.create_line(points, fill=self.color, width=3, tags="snake", capstyle=tk.ROUND, joinstyle=tk.ROUND)

        self.pos += self.speed
        if self.pos > self.perimeter: self.pos = 0
        self.after(20, self.animate)


class QuartzMonitor(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("QUARTZ_CODE // SYSTEM_MONITOR")
        self.geometry("900x650")
        self.configure(fg_color=COLOR_BG)
        self.resizable(False, False)

        self.grid_columnconfigure((0, 1, 2), weight=1)
        self.grid_rowconfigure(2, weight=1)

        # --- HEADER ---
        # We use a subtle title at the top
        ctk.CTkLabel(self, text="/// SYSTEM_OVERWATCH_V2 ///", font=FONT_TITLE, text_color="#333333").grid(row=0, column=0, columnspan=3, pady=(20, 10))

        # --- WIDGETS ---
        # 1. CPU
        self.cpu_border = RealSnakeBorder(self, width=260, height=200, color=COLOR_ACCENT_1)
        self.cpu_border.grid(row=1, column=0, padx=10)
        self.cpu_lbl, self.cpu_bar = self.build_card(self.cpu_border, "CPU_THREAD_0", "⚡", COLOR_ACCENT_1)

        # 2. RAM
        self.ram_border = RealSnakeBorder(self, width=260, height=200, color=COLOR_ACCENT_2)
        self.ram_border.grid(row=1, column=1, padx=10)
        self.ram_lbl, self.ram_bar = self.build_card(self.ram_border, "MEMORY_ALLOC", "💾", COLOR_ACCENT_2)

        # 3. DISK
        self.disk_border = RealSnakeBorder(self, width=260, height=200, color=COLOR_ACCENT_3)
        self.disk_border.grid(row=1, column=2, padx=10)
        self.disk_lbl, self.disk_bar = self.build_card(self.disk_border, "DATA_VOLUME", "💿", COLOR_ACCENT_3)

        # --- LOG TERMINAL ---
        self.log_frame = ctk.CTkFrame(self, fg_color="#080808", border_width=1, border_color="#222")
        self.log_frame.grid(row=2, column=0, columnspan=3, padx=20, pady=20, sticky="nsew")

        # Terminal Header
        ctk.CTkLabel(self.log_frame, text=">> LIVE_PROCESS_FEED", font=("Consolas", 10, "bold"), text_color="#666", anchor="w").pack(fill="x", padx=10, pady=5)
        
        self.log_box = ctk.CTkTextbox(self.log_frame, font=FONT_LOGS, text_color=COLOR_ACCENT_3, fg_color="transparent", height=150)
        self.log_box.pack(fill="both", expand=True, padx=5, pady=5)

        # --- CREDIT / WATERMARK (Bottom Right) ---
        # This is where we put your channel name
        self.credit_label = ctk.CTkLabel(
            self, 
            text="DEV_BUILD: QUARTZ_CODE © 2025", 
            font=("Consolas", 10), 
            text_color="#333333"
        )
        self.credit_label.place(relx=0.97, rely=0.98, anchor="se")

        # --- LOGIC THREADS ---
        self.update_stats()
        self.log_thread = threading.Thread(target=self.stream_real_logs, daemon=True)
        self.log_thread.start()

    def build_card(self, border_obj, title, icon, color):
        parent = border_obj.inner_frame
        
        # Icon & Title
        ctk.CTkLabel(parent, text=f"{icon} {title}", font=FONT_TITLE, text_color=color).pack(pady=(25, 5))
        
        # THE BIG AESTHETIC NUMBER
        val_lbl = ctk.CTkLabel(parent, text="00%", font=FONT_BIG, text_color="white")
        val_lbl.pack(pady=5)
        
        # Styled Progress Bar
        bar = ctk.CTkProgressBar(parent, width=200, height=6, progress_color=color, border_width=0, fg_color="#222")
        bar.set(0)
        bar.pack(pady=20)
        
        return val_lbl, bar

    def update_stats(self):
        # We format it to 00% to keep the width of the text stable (looks better)
        c = int(psutil.cpu_percent())
        self.cpu_lbl.configure(text=f"{c:02d}%") # Forces 2 digits like 05%
        self.cpu_bar.set(c/100)
        
        r = int(psutil.virtual_memory().percent)
        self.ram_lbl.configure(text=f"{r:02d}%")
        self.ram_bar.set(r/100)
        
        d = int(psutil.disk_usage('/').percent)
        self.disk_lbl.configure(text=f"{d:02d}%")
        self.disk_bar.set(d/100)
        
        self.after(1000, self.update_stats)

    def stream_real_logs(self):
        for proc in psutil.process_iter(['pid', 'name', 'status']):
            try:
                if proc.info['status'] == 'running':
                    p = proc.info
                    # Fake 'Scanning' text formatting
                    self.log_box.insert("end", f"[{p['pid']}] SCANNING >> {p['name']}... OK\n")
                    self.log_box.see("end")
                    time.sleep(0.05) # Fast typing effect
            except: pass
            
        # Keep loop alive with just visual noise if list ends
        while True:
            time.sleep(1)

if __name__ == "__main__":
    app = QuartzMonitor()
    app.mainloop()
