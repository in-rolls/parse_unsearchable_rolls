import cv2
import numpy as np
import pdf2image

import pandas as pd
import matplotlib.pyplot as plt 


class Helpers:
    def show(self, im):
        plotting = plt.imshow(im,cmap='gray')
        plt.show()

    def crop_section(self, intial_width,intial_height,crop_width,crop_height,im):
        #return im[intial_height:intial_height+crop_height, intial_width:intial_width+crop_width]
        area = (intial_width, intial_height, intial_width+crop_width, intial_height+crop_height)
        return im.crop(area)

    def strip_lower(self, text):
        try:
            return text.strip().lower()
        except:
            return text

    def items_to_csv(self, items, output_path, columns):
        # Convert dictionary to csv file trough pandas df
        item = {}
        for c in columns:
            item[c] = ''
        items.append(item)
        df = pd.DataFrame.from_dict(items)
        if columns:
            df.to_csv(output_path, index = False, header=True, columns=columns)
        else:
            df.to_csv(output_path, index = False, header=True)

    def pdf_to_img(self, pdf_file_path, dpi=200,page=(None,None)) :
        PDF_PATH = pdf_file_path
        DPI = dpi
        #OUTPUT_FOLDER = output_images_path
        FIRST_PAGE = page[0]
        LAST_PAGE = page[1]
        FORMAT = 'jpg'
        THREAD_COUNT = 1
        USERPWD = None
        USE_CROPBOX = False
        STRICT = False

        return pdf2image.convert_from_path(
                PDF_PATH,
                dpi=DPI,
                #output_folder=OUTPUT_FOLDER,
                first_page=FIRST_PAGE,
                last_page=LAST_PAGE,
                fmt=FORMAT,
                thread_count=THREAD_COUNT,
                userpw=USERPWD,
                use_cropbox=USE_CROPBOX,
                strict=STRICT
            )


    def get_countours(self, im):
        ret,thresh = cv2.threshold(im,180,255,cv2.THRESH_BINARY_INV)# + cv2.THRESH_OTSU)
        kernel = np.ones((3,3),np.uint8)
        dilated = cv2.dilate(thresh,kernel,iterations = 1)
        contours, hierarchy = cv2.findContours(dilated,cv2.RETR_TREE ,cv2.CHAIN_APPROX_SIMPLE)
        return contours

    def crop(self, im, contours, hh, ww):
        processed = []
        for cnt in contours:
            x,y,w,h = cv2.boundingRect(cnt)

            if h > hh[0] and h < hh[1] and w > ww[0] and w< ww[1]:
                cropped_img = im[y+1:y+h, x:x+w]
                processed.append(cropped_img)

        return processed

    # def resize_img(img, scale):
    #     width = int(img.shape[1] * scale)
    #     height = int(img.shape[0] * scale)
    #     dim = (width, height)
        
    #     return cv2.resize(img, dim, interpolation = cv2.INTER_AREA)

    def remove_contours(self, im, contours, hh):
        ret,thresh = cv2.threshold(im,180,255,cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        processed = thresh
        #processed = im

        for cnt in contours:
            x,y,w,h = cv2.boundingRect(cnt)
            
            if h > hh[0] and h < hh[1]:
                z = 6 
                processed = cv2.line(processed,(x,y),(x+w,y),(0,0,0),10)
                processed = cv2.line(processed,(x+w-z,y),(x+w-z,y+h),(0,0,0),12)
                processed = cv2.line(processed,(x+z,y),(x+z,y+h),(0,0,0),12)
                processed = cv2.line(processed,(x,y+h-z),(x+w,y+h-z),(0,0,0),10)

        # cv2.imshow("cropped", processed)
        # cv2.waitKey()
        # self.show(processed)
        return processed

    def get_boxes(self, pil_image, contours):
        limits_h = contours[0]
        limits_w = contours[1]
        contour_limits = contours[2]

        im = np.array(pil_image) 
        im = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
        contours = self.get_countours(im)
        boxes = self.crop(im, contours, limits_h, limits_w) #(500,800), (300,1500)) 

        boxes_processed = []
        for b in boxes:
            contours = self.get_countours(b)
            boxes_processed.append(
                self.remove_contours(b, contours, contour_limits)# (60, 400))
            )

        return boxes_processed

