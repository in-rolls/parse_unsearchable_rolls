import os
#import pandas as pd
from helpers import get_boxes, pdf_to_img, items_to_csv, strip_lower
import logging
import pytesseract
#import re
import cv2

# import matplotlib.pyplot as plt
# import keras_ocr 
  
# pipeline = keras_ocr.pipeline.Pipeline()
  
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(message)s',
                    handlers=[logging.FileHandler("parser/debug.log"),
                              logging.StreamHandler()])

class Parser:
    BASE_DATA_PATH = 'data/'
    BASE_PARSED_DATA_PATH = 'parsed_data/'
    IMAGES_PATH = BASE_PARSED_DATA_PATH + 'images/'
    OUTPUT_CSV = ''

    def __init__(self, state, lang, separator= ':', separators = [], ommit = None):
        self.state = state
        #self.columns = columns
        self.lang = lang
        self.separator = separator
        self.ommit = ommit
        self.separators = separators

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

    def ommit_sentences(self, text):
        if self.ommit:
            for o in self.ommit:
                text = text.replace(o, '')
            
        return text

    def custom_split(self, r, separator, result):
        is_splitted = False
        separated = r.split(separator)

        if len(separated) == 2:
            key, value = self.custom_split(separated)
            key = strip_lower(separated[0])
            value = separated[1].strip()
            result[key] = value
            last_key = key
            is_splitted = True


        elif len(separated) == 3:
            try:
                key = strip_lower(separated[0])
                value_1, key_2 = separated[1].split()
                result[key] = value_1.strip()
                result[strip_lower(key_2)] = separated[2].strip()
                last_key = key
                is_splitted = True
            except Exception as e:
                logging.error(f'2 separators error: {e} : {r}')

        else:
            logging.error(f'More than 2 separators {r}')
            return result, None
        
        return result, last_key, is_splitted


        

    def process_boxes_text(self, text):
        raw = self.ommit_sentences(text)
        raw = raw.replace('\n\n', '\n').split('\n')
        result = {}
        
        # TODO not abtracted
        result['id'] = raw.pop(0).strip()

        # To add data to previous column
        last_key = None

        # Iter over results and split with separators
        for r in raw:

            is_splitted = False
            for sep in self.separators:
                if sep in r.lower():
                    result, last_key, is_splitted = self.custom_split(r, sep, result)

            if r and not is_splitted:
                try:
                    result[last_key] = result[last_key] + ' ' + r.strip()
                except Exception as e:
                    logging.error(f'Exception: {e}: {raw}') 

        return result
        

    def run(self):
        pdf_files_paths = self.get_this_state_files()
        if not pdf_files_paths:
            logging.info(f'No files found for {self.state}')

        for pdf_file_path in pdf_files_paths:
            logging.info(f'Converting {pdf_file_path} ...')
            logging.info('Converting pdf to imgs ...')
            images_list = pdf_to_img(pdf_file_path, dpi=600, page=(1,3))
            items = []


            for page in images_list[2:]:
                #page.show()
                logging.info('Getting boxes..')

                boxes = get_boxes(page)
                for box in boxes:
                    # todo get number and id separated
                    # cv2.imshow("cropped", box)
                    # cv2.waitKey(10) 
                    text = pytesseract.image_to_string(box, lang=self.lang, config='--psm 6 digit')
                    # img = keras_ocr.tools.read(box)
                    # prediction_groups = pipeline.recognize([img])
                    # keras_ocr.tools.drawAnnotations(image=img, predictions=prediction_groups[0])

                    item = self.process_boxes_text(text)
                    items.append(item)
                
                #page.show()

            # TODO path
            output_path = self.OUTPUT_CSV + self.state + '.csv'
            items_to_csv(items, output_path)

            logging.info(f'Converted to csv: {output_path}')

if __name__ == '__main__':
    lang = 'eng'
    Parser('delhi', lang, separators =  [' : ', ' - ', '='], ommit = ['Photo is', '\nAvailable']).run()

    #lang = 'eng+guj'
    #Parser('gujarat', lang, separator = 'ન : ', separator_alt = ':-').run()
