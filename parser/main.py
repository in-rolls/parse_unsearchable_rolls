import os
import pandas as pd
from helpers import get_boxes, pdf_to_img
import logging
import pytesseract

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(message)s',
                    handlers=[logging.FileHandler("parser/debug.log"),
                              logging.StreamHandler()])

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
            logging.info(f'Converting {pdf_file_path} ...')
            logging.info('Converting pdf to imgs ...')
            images_list = self.pdf_to_img(pdf_file_path, dpi=500)

            for page in images_list[2:]:
                logging.info('Getting boxes..')
                breakpoint()
                boxes = get_boxes(page)
                for box in boxes:
                    text = (pytesseract.image_to_string(box, lang=self.lang, config='--psm 6'))
                    print(text)



if __name__ == '__main__':
    columns = ["number","id", "elector_name", "father_or_husband_name", "relationship", "house_no", "age", "sex", "ac_name", "parl_constituency", "part_no", "year", "state", "filename", "main_town", "police_station", "mandal", "revenue_division", "district", "pin_code", "polling_station_name", "polling_station_address", "net_electors_male", "net_electors_female", "net_electors_third_gender", "net_electors_total"]
    lang = 'eng'
    Parser('delhi', columns, lang).run()

