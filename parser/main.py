import sys
import os
from tkinter import W
import pandas as pd

sys.path.append('../')
from parse_unsearchable_rolls.scripts.helper import *


class Parser:
    BASE_DATA_PATH = 'data/'
    BASE_PARSED_DATA_PATH = 'parsed_data/'
    IMAGES_PATH = BASE_PARSED_DATA_PATH + 'images/'

    def __init__(self, state, columns, lang):
        self.state = state
        self.columns = columns
        self.lang = lang

    def pdf_to_img(self, pdf_file_path, output_images_path,dpi=200,page=None):
        return pdf_to_img(pdf_file_path, output_images_path,dpi=dpi,page=page) 

    def get_full_path_files(self, path):
        return [os.path.join(path, f) for f in os.listdir(path)]

    def filter_and_sort(self, objs, ext):
        result = list(filter(lambda x: x.endswith(ext), objs))
        result.sort()
        return result

    def get_this_state_files(self):
        path = f'{self.BASE_DATA_PATH}{self.state}'
        files_path_list = self.get_full_path_files(path)
        return self.filter_and_sort(files_path_list, '.pdf')


    def run(self):
        pdf_files_paths = self.get_this_state_files()

        for pdf_file_path in pdf_files_paths:
            images_path = self.IMAGES_PATH + self.state
            this_pdf_images = f'{images_path}/{pdf_file_path.rstrip(".pdf").split("/")[-1]}'
            create_path(this_pdf_images)

            images_list = self.pdf_to_img(pdf_file_path, this_pdf_images,dpi=500)
            df = pd.DataFrame(columns = self.columns)
            images_files_paths = self.get_full_path_files(this_pdf_images)
            images_files_paths = self.filter_and_sort(images_files_paths, '.jpg')

            
            for page in images_files_paths:
                if page.endswith('1.jpg'):
                    ...
                elif page.endswith('2.jpg'):
                    ...
                else:
                    text = (pytesseract.image_to_string(page, lang=self.lang, config='--psm 6')) #config='--psm 4' config='-c preserve_interword_spaces=1'))
                    breakpoint()




if __name__ == '__main__':
    
    columns = ["number","id", "elector_name", "father_or_husband_name", "relationship", "house_no", "age", "sex", "ac_name", "parl_constituency", "part_no", "year", "state", "filename", "main_town", "police_station", "mandal", "revenue_division", "district", "pin_code", "polling_station_name", "polling_station_address", "net_electors_male", "net_electors_female", "net_electors_third_gender", "net_electors_total"]
    lang = 'eng'
    Parser('delhi', columns, lang).run()

