import cv2
from util.item import Item
import numpy as np

class ImageProcessor():
    def __init__(self, item_list, scale_factor=1):
        self.items = item_list
        self.scale_factor = scale_factor

    def process_frame(self, frame,return_processed=False):
        template = cv2.imread(self.items[0], cv2.IMREAD_UNCHANGED)
        template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
        template_gray = cv2.GaussianBlur(template_gray, (3,3), 0)
        template_canny = self.auto_canny(template_gray)
        
        h,w = template_gray.shape
        print(template.shape)

        print(frame.shape)
        scaled = cv2.resize(frame, None, fx=self.scale_factor,fy=self.scale_factor,interpolation=cv2.INTER_LINEAR)
        gray = cv2.cvtColor(scaled, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (3,3), 0)
        scaled_canny = self.auto_canny(blurred)
        print(scaled_canny.shape)

        res = cv2.matchTemplate(scaled_canny, template_canny, cv2.TM_CCORR_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        top_left = max_loc
        bottom_right = (top_left[0] + w, top_left[1] + h)
        print(max_val)

        if return_processed:
            final = scaled_canny
        else:
            final = scaled
        
        if max_val > .5:       
            cv2.rectangle(final, top_left, bottom_right, 255, 2)
        
        return final

    def auto_canny(self, image, sigma=0.33):
        v = np.median(image)
        lower = int(max(0, (1.0 - sigma) * v))
        upper = int(min(255, (1.0 + sigma) * v))

        canny = cv2.Canny(image, lower, upper)

        return canny
