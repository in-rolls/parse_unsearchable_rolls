import cv2
import numpy as np
import pdf2image
import os 
import logging

import pandas as pd
import matplotlib.pyplot as plt 
import concurrent.futures


logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(message)s',
                    handlers=[logging.FileHandler("parser/debug.log"),
                              logging.StreamHandler()])

class Helpers:

    # File methods
    def get_file_paths(self):
        pdf_files_paths = self.get_this_state_files()
        if not pdf_files_paths:
            logging.info(f'No files found')

        return pdf_files_paths

    def get_full_path_files(self, path):
        return [os.path.join(path, f) for f in os.listdir(path)]

    def filter_and_sort(self, objs, ext):
        result = list(filter(lambda x: x.endswith(ext), objs))
        result.sort()
        return result

    def get_this_state_files(self):
        path = f'{self.BASE_DATA_PATH}in/{self.state}'
        if self.year:
            path += '/' + self.year
        files_path_list = self.get_full_path_files(path)
        return self.filter_and_sort(files_path_list, '.pdf')


    # testing methods

    def show(self, im):
        plotting = plt.imshow(im,cmap='gray')
        plt.show()
    
    def nshow(self, im):
        cv2.imshow('image',im)
        cv2.waitKey(10)

    def check_cropped(self, im, cropped):
        self.show(im)
        self.show(cropped)

    # text manipulation methods

    def split_2(self, separated):
        key = self.strip_lower(separated[0])
        value = separated[1].strip()
        return key, value

    def separator_split(self, r, separator, result, last_key):
        is_splitted = False

        # for exceptions
        #if any([re.findall(f"^[\w]{x}^[\w]", r.lower()) for x in self.handle]):
        if any([x in r.lower() for x in self.handle]):
            return self.handle_separation(r, separator, result)

        # split without column names
        else:
            separated = r.split(separator)

            if len(separated) == 2:
                key, value = self.split_2(separated)
                result[key] = value
                last_key = key
                is_splitted = True
            # else:
            #     return self.handle_custom_split_not_found(r, separator, result)
        
        return result, last_key, is_splitted 

    def strip_lower(self, text):
        try:
            return text.strip().lower()
        except:
            return text


    # convertion methods

    def items_to_csv(self, items, output_path, columns):
        # Convert dictionary to csv file trough pandas df
        item = {}
        for c in columns:
            item[c] = ''
        items.append(item)
        df = pd.DataFrame.from_dict(items)

        if columns:
            if self.translate_columns:
                df.rename(columns=self.translate_columns, inplace=True)
                columns = self.translate_input_columns()
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


    # array methods

    def crop_section(self, intial_width,intial_height,crop_width,crop_height,im):
        #return im[intial_height:intial_height+crop_height, intial_width:intial_width+crop_width]
        area = (intial_width, intial_height, intial_width+crop_width, intial_height+crop_height)
        return im.crop(area) 

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

    def remove_contours(self, im, contours, hh):
        ret,thresh = cv2.threshold(im,180,255,cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        processed = thresh

        for cnt in contours:
            x,y,w,h = cv2.boundingRect(cnt)
            if h > hh[0] and h < hh[1]:
                z = 6 
                processed = cv2.line(processed,(x,y),(x+w,y),(0,0,0),10)
                processed = cv2.line(processed,(x+w-z,y),(x+w-z,y+h),(0,0,0),12)
                processed = cv2.line(processed,(x+z,y),(x+z,y+h),(0,0,0),12)
                processed = cv2.line(processed,(x,y+h-z),(x+w,y+h-z),(0,0,0),10)
        
        return processed

    def remove_photo(self, box, contours):
        start_point = None

        for c in contours:
            x,y,w,h = cv2.boundingRect(c)
            if x > box.shape[1]/2 and w > 300:
                start_point = (x,y) 
                break
        
        end_point = box.shape[1], box.shape[0]
        if not start_point:
            start_point = end_point

        return cv2.rectangle(box, start_point, end_point, (0, 0, 0), -1)

    def get_boxes(self, pil_image, contours):
        limits_h = contours[0]
        limits_w = contours[1]
        contour_limits = contours[2]

        im = np.array(pil_image) 
        im = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
        contours = self.get_countours(im)
        boxes = self.crop(im, contours, limits_h, limits_w)

        boxes_processed = []

        def get_box(b):
            contours = self.get_countours(b)
            box = self.remove_contours(b, contours, contour_limits)
            box = self.remove_photo(box, contours)
            boxes_processed.append(box)

        # concurrent
        with concurrent.futures.ProcessPoolExecutor(max_workers=self.cv2_workers) as executor:
            future = executor.map(get_box, boxes, chunksize=self.chunksize)
            try:
                future.result()
            except:
                pass

        return boxes_processed

    # def resize_img(img, scale):
    #     width = int(img.shape[1] * scale)
    #     height = int(img.shape[0] * scale)
    #     dim = (width, height)
        
    #     return cv2.resize(img, dim, interpolation = cv2.INTER_AREA)

    # Deprectaed removing photos
    # def ommit_sentences(self, text):
    #     if self.ommit:
    #         for o in self.ommit:
    #             text = text.replace(o, '')
            
    #     return text
