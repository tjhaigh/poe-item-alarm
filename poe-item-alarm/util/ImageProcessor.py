import cv2
import numpy as np
import os

class ImageProcessor():
    def __init__(self, item_manager, resource_dir, scale_factor=1):
        self.item_manager = item_manager
        self.scale_factor = scale_factor
        self.resource_dir = resource_dir
        self.templates = []

        for item in self.item_manager.get_items():
            item.template,item.shape = self.make_template(os.path.join(self.resource_dir, "images", "items", item.image))

    
    
    def process_frame(self,frame,threshold,return_processed=False):

        frame = cv2.UMat(frame)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (3,3), 0)
        scaled_canny = cv2.Canny(blurred, 50, 150)

        if return_processed:
            final = scaled_canny
        else:
            final = frame

        matched = False
        for item in self.item_manager.enabled_items():
            template = item.template
            h,w,_ = item.shape
            res = cv2.matchTemplate(scaled_canny, template, cv2.TM_CCORR_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
            top_left = max_loc
            bottom_right = (top_left[0] + w, top_left[1] + h)        
            
            if max_val > threshold:       
                cv2.rectangle(final, top_left, bottom_right, 255, 2)
                matched = True
                break

        return final.get(), matched

    # returns the gpu cannied template and its dimensions
    def make_template(self, image):
        template = cv2.imread(image, cv2.IMREAD_UNCHANGED)
        scaled_template = cv2.resize(template, None, fx=self.scale_factor,fy=self.scale_factor,interpolation=cv2.INTER_LINEAR)
        shape = scaled_template.shape
        scaled_template = cv2.UMat(scaled_template)
        template_gray = cv2.cvtColor(scaled_template, cv2.COLOR_BGR2GRAY)
        template_gray = cv2.GaussianBlur(template_gray, (3,3), 0)
        template_canny = cv2.Canny(template_gray, 50, 150)
        
        return template_canny,shape

    def auto_canny(self, image, sigma=0.33):
        v = np.median(image)
        lower = int(max(0, (1.0 - sigma) * v))
        upper = int(min(255, (1.0 + sigma) * v))

        canny = cv2.Canny(image, 50, 150)

        return canny
