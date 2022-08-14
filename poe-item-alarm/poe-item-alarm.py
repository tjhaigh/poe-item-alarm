
import os
from playsound import playsound
import tkinter as tk
from tkinter import ttk
import sv_ttk
import dxcam
import threading
from imageprocessor import ImageProcessor
from util.ItemManager import ItemManager
from PIL import ImageTk,Image,ImageOps
from concurrent.futures import ThreadPoolExecutor
import timeit
import cv2

scale_factor = 1.12

resource_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources")

class MainApplication(ttk.Frame):
    _alarm_file = os.path.join(resource_dir, "sounds", "Alarm.wav")
    _camera = dxcam.create()
    region = None

    def __init__(self, parent, *args, **kwargs):
        ttk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent
        self.item_manager = ItemManager(item_file="util/items.json")
        self.image_processor = ImageProcessor(self.item_manager, 1.12)
        
        self.columnconfigure(index=0,weight=1)

        self.setup_widgets()

    def setup_widgets(self):
        # Capture Preview Frame
        self.preview_frame = ttk.LabelFrame(self, text="Capture Preview", padding=(20,10))
        self.preview_frame.grid(row=0, column=0, padx=(20,10), pady=(20,10), sticky="nsew")
        self.preview_frame.columnconfigure(index=0,weight=1)
        self.preview_frame.rowconfigure(index=1,weight=1)

        self.filler1 = ttk.Label(self.preview_frame)
        self.filler1.grid(row=0,column=0,sticky="ew")

        self.select_area_button = ttk.Button(self.preview_frame,text="Select Capture Area",command=lambda: self.area_select())
        self.select_area_button.grid(row=0, column=1,padx=5,pady=5,sticky="ew")

        self.capture_button = ttk.Button(self.preview_frame,text="Start Capture",command=lambda: self.start_capture() )
        self.capture_button.grid(row=0,column=2,padx=5,pady=5,sticky="ew")

        self.show_cv_cbutton = ttk.Checkbutton(self.preview_frame,text="Show Processed Frames")
        self.show_cv_cbutton.grid(row=0,column=3,padx=5,pady=5,sticky="ew")
        self.show_cv_cbutton.state(["!alternate"])

        self.image_preview = ttk.Label(self.preview_frame)
        self.image_preview.grid(row=1,column=0,columnspan=4,padx=5,pady=5, sticky="nsew")
        self.parent.bind("<<frame-update>>", self.update_preview)
        self.curr_frame = None

        # Item list frame
        self.item_frame = ttk.LabelFrame(self, text="Items", padding=(20,10))
        self.item_frame.grid(row=0,column=1,rowspan=2,padx=(20,10),pady=(20,10),sticky="nsew")

        # self.scrollbar = ttk.Scrollbar(self.item_frame)
        # self.scrollbar.grid(row=)

        self.item_checkboxes = dict()
        for x,item in enumerate(self.item_manager.get_items()):
            self.item_checkboxes[item] = tk.IntVar()
            self.item_checkboxes[item].set(item.enabled)
            cb = ttk.Checkbutton(self.item_frame,text=item.name,variable=self.item_checkboxes[item],command=lambda key=item: self.item_clicked(key))
            cb.grid(row=x,column=0,sticky="ew")
        

    def stream_frames(self):
        while self._camera.is_capturing:
            frame = self._camera.get_latest_frame()
            start = timeit.default_timer()
            self.process_frame(frame)
            end = timeit.default_timer()
            print("Frame took " + str(end-start) + " seconds")
            
        print("recording stopped")

    def process_frame(self,frame):
        res = self.image_processor.process_frame(frame,self.show_cv_cbutton.instate(['selected']))
        if res is not None:
            frame = res
            #playsound(self._alarm_file, block=False)
        self.curr_frame = frame
        self.parent.event_generate("<<frame-update>>")

            
    def update_preview(self,event):
        frame = Image.fromarray(self.curr_frame)
        w = max(100,self.image_preview.winfo_width()-5)
        h = max(100,self.image_preview.winfo_height()-5)
        frame = ImageOps.contain(frame, (w,h))
        frame = ImageTk.PhotoImage(frame)
        self.image_preview.configure(image=frame)
        self.image_preview.image = frame

    # for future me:
    # this might be confusing, but we keep a dict of items and their respective checkbox vars
    # since objs are references, we just update the value of it here and it propagates through the rest of the app
    # call save items here to make sure changes are saved
    def item_clicked(self, item):
        v = self.item_checkboxes.get(item)
        item.enabled = bool(v.get())
        self.item_manager.save_items()


    def start_capture(self):
        if not self._camera.is_capturing:
            self._camera.start(target_fps=30,region=self.region)
            self.capture_button.configure(text="Stop Capture")
            t = threading.Thread(target=self.stream_frames)
            t.daemon = True
            t.start()
        else:
            self._camera.stop()
            self.capture_button.configure(text="Start Capture")

    def area_select(self):
        screenshot = self._camera.grab()
        screenshot = cv2.cvtColor(screenshot, cv2.COLOR_RGB2GRAY)
        screenshot = Image.fromarray(screenshot)
        screenshot = ImageTk.PhotoImage(screenshot)
        area_frame = AreaSelection(self, screenshot)
        area_frame.wm_attributes('-fullscreen', 'True')


    def set_capture_area(self, left, top, right, bottom):
        self.region = (left,top,right,bottom)
        self.curr_frame = self._camera.grab(region=self.region)
        self.parent.event_generate("<<frame-update>>")


class AreaSelection(tk.Toplevel):
    def __init__(self, parent, screenshot, *args, **kwargs):
        tk.Toplevel.__init__(self, parent, *args, **kwargs)
        self.parent = parent
        self.bg = tk.Canvas(self, width=self.winfo_screenwidth(), height=self.winfo_screenheight(), cursor="cross")
        self.bg.pack()
        self.bg.create_image((0,0),anchor=tk.NW,image=screenshot)
        self.screenshot = screenshot

        self.bind("<Escape>", self.close)

        self.bind("<ButtonPress-1>", self.click)
        self.bind("<B1-Motion>", self.drag)
        self.bind("<ButtonRelease-1>", self.release)

    def close(self, event):
        self.destroy()

    def click(self, event):
        self.start_x = event.x
        self.start_y = event.y
        self.rect = self.bg.create_rectangle(event.x,event.y,1,1,outline='red')

    def drag(self, event):
        self.end_x = event.x
        self.end_y = event.y
        self.bg.coords(self.rect, self.start_x, self.start_y, event.x, event.y)

    def release(self, event):
        self.end_x = event.x 
        self.end_y = event.y
        # we calc min and max so that the box doesn't have to always be top left -> bottom right
        top = min(self.start_y, self.end_y)
        left = min(self.start_x, self.end_x)
        bottom = max(self.start_y, self.end_y)
        right = max(self.start_x, self.end_x)
        
        self.parent.set_capture_area(left+1, top+1, right, bottom)
        self.destroy()
    

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