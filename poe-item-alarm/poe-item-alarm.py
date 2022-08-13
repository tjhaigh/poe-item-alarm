from difflib import IS_CHARACTER_JUNK
import os
from sqlite3 import TimestampFromTicks
from playsound import playsound
import tkinter as tk
from tkinter import ttk
import sv_ttk
import dxcam
import threading
from imageprocessor import ImageProcessor
from PIL import ImageTk,Image
import cv2

scale_factor = 1.12

resource_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources")

class MainApplication(ttk.Frame):
    _alarm_file = os.path.join(resource_dir, "sounds", "Alarm.wav")
    _camera = dxcam.create()

    def __init__(self, parent, *args, **kwargs):
        ttk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent
        self.image_processor = ImageProcessor([os.path.join(resource_dir, "images", "items", "mageblood.png")], 1.12)
        
        for index in (0, 1, 2):
            self.columnconfigure(index=index, weight=1)
            self.rowconfigure(index=index, weight=1)

        self.setup_widgets()

    def setup_widgets(self):
        top_bar = ttk.Frame(self.parent)
        top_bar.pack(side=tk.TOP, fill=tk.X)

        button_bar = ttk.Frame(top_bar)
        button_bar.pack(side=tk.TOP,fill=tk.X)
        sound_test_button = ttk.Button(button_bar,text="test sound",command=lambda: playsound(self._alarm_file, block=False))
        sound_test_button.grid(row=0,column=0,padx=2,pady=2)

        self.capture_button = ttk.Button(button_bar,text="start capture",command=lambda: self.start_capture() )
        self.capture_button.grid(row=0,column=1,padx=2,pady=2)

        self.show_cv_cbutton = ttk.Checkbutton(button_bar,text="Show Processed Frames")
        self.show_cv_cbutton.grid(row=0,column=2,padx=2,pady=2)

        self.preview_frame = ttk.Frame(self.parent, height=200, width=200)
        self.preview_frame.pack(fill=tk.BOTH, expand=True)
        self.image_preview = ttk.Label(self.preview_frame)
        self.image_preview.pack()
        self.parent.bind("<<frame-update>>", self.update_preview)

    def stream_frames(self):
        while self._camera.is_capturing:
            frame = self._camera.get_latest_frame()
            res = self.image_processor.process_frame(frame,self.show_cv_cbutton.instate(['selected']))
            if res is not None:
                frame = res
                #playsound(self._alarm_file, block=False)
            frame = Image.fromarray(frame)
            w = self.preview_frame.winfo_width()-5    # subtract a few pixels to ensure it doesn't grow every frame
            h = self.preview_frame.winfo_height()-5
            frame.thumbnail((w,h), Image.LANCZOS)
            self.curr_frame = ImageTk.PhotoImage(frame)
            self.parent.event_generate("<<frame-update>>")
        
        print("recording stopped")
            
    def update_preview(self, frame):
        self.image_preview.configure(image=self.curr_frame)
        self.image_preview.image = self.curr_frame

    def start_capture(self):
        if not self._camera.is_capturing:
            self._camera.start()
            self.capture_button.configure(text="stop capture")
            t = threading.Thread(target=self.stream_frames)
            t.daemon = True
            t.start()
        else:
            self._camera.stop()
            self.capture_button.configure(text="start capture")

    def check_image(self, image, reference):
        template = cv2.imread(reference, cv2.IMREAD_UNCHANGED)
        template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
        template_gray = cv2.GaussianBlur(template_gray, (3,3), 0)
        template_canny = cv2.Canny(template_gray, 100, 200)
        
        h,w = template_gray.shape

        scaled = cv2.resize(image, None, fx=scale_factor,fy=scale_factor,interpolation=cv2.INTER_LINEAR)
        gray = cv2.cvtColor(scaled, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (3,3), 0)
        scaled_canny = cv2.Canny(blurred, 100, 200)

        res = cv2.matchTemplate(scaled_canny, template_canny, cv2.TM_CCORR_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        top_left = max_loc
        bottom_right = (top_left[0] + w, top_left[1] + h)
        print(max_val, reference)
        
        if max_val > .5:       
            cv2.rectangle(scaled_canny, top_left, bottom_right, 255, 2)
            return scaled_canny
        else:
            return None

    

if __name__ == "__main__":
    window = tk.Tk()
    window.title("PoE Item Alarm")

    sv_ttk.set_theme("dark")

    app = MainApplication(window)
    app.pack(fill="both", expand=True)

    window.update_idletasks()

    w, h = window.winfo_width(), window.winfo_height()
    x = int((window.winfo_screenwidth() / 2) - (w / 2))
    y = int((window.winfo_screenheight() / 2) - (h / 2))

    # Set a minsize for the window, and place it in the middle
    window.minsize(w, h)
    window.geometry(f"+{x}+{y}")

    window.mainloop()