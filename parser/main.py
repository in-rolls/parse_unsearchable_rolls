import os
#import pandas as pd
from helpers import get_boxes, pdf_to_img, items_to_csv, strip_lower
import logging
import pytesseract
import re
#import numpy as np
import cv2

import matplotlib.pyplot as plt
import keras_ocr
pipeline = keras_ocr.pipeline.Pipeline()
 
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(message)s',
                    handlers=[logging.FileHandler("parser/debug.log"),
                              logging.StreamHandler()])

class Parser:
    BASE_DATA_PATH = 'data/'
    BASE_PARSED_DATA_PATH = 'parsed_data/'
    IMAGES_PATH = BASE_PARSED_DATA_PATH + 'images/'
    OUTPUT_CSV = 'data/'

    def __init__(self, state, lang, separator= ':', handle = [], separators = [], ommit = None):
        self.state = state
        #self.columns = columns
        self.lang = lang
        self.separator = separator
        self.ommit = ommit
        self.separators = separators
        self.handle = handle

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
    
    def handle_separation_error(self, r, separator, result):
        last_key = None
        is_splitted = False

        if '-' in r:
            rr = r.split('-')
            key = rr[0]
            value = '-'.join(rr[1:])
            result[key] = value
            last_key = key
            is_splitted = False

        else:
            logging.error(f'Separation error : {r}')

        return result, last_key, is_splitted

    def handle_separation(self, r, separator, result):

        if 'age' in r.lower():

            result['age'] = ''.join(re.findall('age[^\d]*(\d*)', r.lower()))
            result['sex'] = ''.join(re.findall('sex[^\w]*(\w*)', r.lower()))

            last_key = 'sex'
            is_splitted = True

        return result, last_key, is_splitted


    def custom_split(self, r, separator, result):
        is_splitted = False

        if any([x in r.lower() for x in self.handle]):
            return self.handle_separation(r, separator, result)

        else:
            separated = r.split(separator)

            if len(separated) == 2:
                key = strip_lower(separated[0])
                value = separated[1].strip()
                result[key] = value
                last_key = key
                is_splitted = True


        # elif len(separated) == 3:
        #     try:
        #         key = strip_lower(separated[0])
        #         value_1, key_2 = separated[1].split()
        #         result[key] = value_1.strip()
        #         result[strip_lower(key_2)] = separated[2].strip()
        #         last_key = key
        #         is_splitted = True
        #     except Exception as e:
        #         return self.handle_separator_error(r, separator, result)
        #         #logging.error(f'2 separators error: {e} : {r}')
        #         #return result, None, False

            else:
                return self.handle_separation_error(r, separator, result)
        
        return result, last_key, is_splitted

     
    def process_boxes_text(self, text):
        #logging.info('Processing boxes\' text..')
        raw = self.ommit_sentences(text)
        raw = raw.replace('\n\n', '\n').split('\n')
        result = {}
        
        # TODO not abstracted
        id_ = raw.pop(0).strip()
        first = id_.split(' ')

        
        if len(first) > 1:
            result['count'] = first[0]    
            result['id'] = first[1]
        else:
            result['count'] = ''
            result['id'] = first[0]

            logging.error(f"Not clear id: {raw}")

        # To add data to previous column
        last_key = None

        # Iter over results and split with separators
        for r in raw:
            is_splitted = False
            for sep in self.separators:
                if sep in r.lower():
                    result, last_key, is_splitted = self.custom_split(r, sep, result)

                    if is_splitted:
                        break

            if r and not is_splitted:
                try:
                    result[last_key] = result[last_key] + ' ' + r.strip()
                except Exception as e:
                    logging.error(f'Exception: {e}: {raw}') 
                    result, last_key, is_splitted = self.handle_separation_error(r, self.separators, result)
                    
        return result
        
    def run(self):
        pdf_files_paths = self.get_this_state_files()
        if not pdf_files_paths:
            logging.info(f'No files found for {self.state}')

        for pdf_file_path in pdf_files_paths:
            logging.info(f'Converting {pdf_file_path} ...')
            logging.info('Converting pdf to imgs ...')
            images_list = pdf_to_img(pdf_file_path, dpi=600)#, page=(1,3))
            items = []

            # page 1
            # text = pytesseract.image_to_string(images_list[0], lang=self.lang, config='--psm 6') 

            for page in images_list[2:]:
                logging.info('Getting boxes..')

                boxes = get_boxes(page)
                for box in boxes:
                    # todo get number and id separated
                    # cv2.imshow("cropped", box)
                    # cv2.waitKey(10)
                    # breakpoint()
                    text = pytesseract.image_to_string(box, lang=self.lang, config='--psm 6')
                    #img = keras_ocr.tools.read(box)
                    #breakpoint()
                    #prediction_groups = pipeline.recognize([box])
                    #keras_ocr.tools.drawAnnotations(image=img, predictions=prediction_groups[0])
                    # cv2.imshow("cropped", box)
                    # cv2.waitKey()
                    # breakpoint()

                    item = self.process_boxes_text(text)
                    items.append(item)
                
                #page.show()

            # TODO path
            output_path = self.OUTPUT_CSV + self.state + '.csv'
            items_to_csv(items, output_path)

            logging.info(f'Converted to csv: {output_path}')

if __name__ == '__main__':
    lang = 'eng'
    Parser('delhi', lang, separators =  [':', '|', '.', '=', '-'], handle=['age', 'sex'], ommit = ['Photo is', 'Available']).run()

    #lang = 'eng+guj'
    #Parser('gujarat', lang, separator = 'ન : ', separator_alt = ':-').run()
