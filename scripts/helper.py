import os
import pdf2image
from PIL import Image
import pytesseract
import difflib
import re
import pandas as pd

def pdf_to_img(pdf_file_path, output_images_path,dpi=200,page=None) :

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

    def rename_filename(output_image_path,idx):
        path, filename = os.path.split(output_image_path)
        os.rename(output_image_path,path+"/"+str(idx)+".jpg")

    def delete_existing_images():
        images = os.listdir(output_images_path)
        for image in images:
            os.remove(output_images_path+"/"+image)



    def pdftopil():

        pil_images = pdf2image.convert_from_path(PDF_PATH,
                                                 dpi=DPI,
                                                 output_folder=OUTPUT_FOLDER,
                                                 first_page=FIRST_PAGE,
                                                 last_page=LAST_PAGE,
                                                 fmt=FORMAT,
                                                 thread_count=THREAD_COUNT,
                                                 userpw=USERPWD,
                                                 use_cropbox=USE_CROPBOX,
                                                 strict=STRICT)

        for idx,image in enumerate(pil_images,1):
            rename_filename(image.filename,idx)

        return pil_images


    delete_existing_images()
    pil_images = pdftopil()

    return pil_images

def tryint(s):
    try:
        return int(s)
    except ValueError:
        return s

def alphanum_key(s):
    return [ tryint(c) for c in re.split('([0-9]+)', s) ]

def sort_nicely(l):
    l.sort(key=alphanum_key)

def crop_section(intial_width,intial_height,crop_width,crop_height,img):
    area = (intial_width, intial_height, intial_width+crop_width, intial_height+crop_height)
    cropped_img = img.crop(area)
    return cropped_img

def create_path(path):
    if not os.path.exists(path):
        os.makedirs(path)

def save_to_csv(dataframe, full_filepath):

    if dataframe.empty:
        return
    else :
        dataframe.to_csv(full_filepath,index=False)

def combine_all_csvs(combine_full_filepath,csvs_path):

    all_filenames = os.listdir(csvs_path)
    csvs_list = []

    for file in all_filenames:
        if file.endswith('csv'):
            csvs_list.append(pd.read_csv(csvs_path+file))

    combined_csv = pd.concat(csvs_list)
    combined_csv.to_csv( combine_full_filepath, encoding='utf-8-sig')
