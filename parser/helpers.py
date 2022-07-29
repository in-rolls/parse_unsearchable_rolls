import cv2
import numpy as np
import pdf2image
import pandas as pd



def items_to_csv(items, output_csv_path):
    # Convert dictionary to csv file trough pandas df
    df = pd.DataFrame.from_dict(items)
    df.to_csv (output_csv_path, index = False, header=True) 

def pdf_to_img(pdf_file_path, dpi=200,page=None) :

    PDF_PATH = pdf_file_path
    DPI = dpi
    OUTPUT_FOLDER = output_images_path
    FIRST_PAGE = page
    LAST_PAGE = page
    FORMAT = 'jpg'
    THREAD_COUNT = 1
    USERPWD = None
    USE_CROPBOX = False
    STRICT = False

    def pdftopil():

        pil_images = pdf2image.convert_from_path(PDF_PATH,
                                                 dpi=DPI,
                                                 #output_folder=OUTPUT_FOLDER,
                                                 first_page=FIRST_PAGE,
                                                 last_page=LAST_PAGE,
                                                 fmt=FORMAT,
                                                 thread_count=THREAD_COUNT,
                                                 userpw=USERPWD,
                                                 use_cropbox=USE_CROPBOX,
                                                 strict=STRICT)

        return pil_images

    pil_images = pdftopil()

    return pil_images

def get_boxes(pil_image):
    im = np.array(pil_image) 
    im = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    ret,thresh_value = cv2.threshold(im,180,255,cv2.THRESH_BINARY_INV)

    kernel = np.ones((5,5),np.uint8)
    dilated_value = cv2.dilate(thresh_value,kernel,iterations = 1)

    contours, hierarchy = cv2.findContours(dilated_value,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)

    cropped = []
    cordinates = []
    for cnt in contours:
        x,y,w,h = cv2.boundingRect(cnt)
        cordinates.append((x,y,w,h))
        if h > 400 and h < 1000:
            crop_img = im[y:y+h, x:x+w]
            cropped.append(crop_img)
    
    return cropped

