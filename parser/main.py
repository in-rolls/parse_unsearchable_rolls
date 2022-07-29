import os
import pandas as pd
from helpers import get_boxes, pdf_to_img, items_to_csv, strip_lower
import logging
import pytesseract
import re

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(message)s',
                    handlers=[logging.FileHandler("parser/debug.log"),
                              logging.StreamHandler()])

class Parser:
    BASE_DATA_PATH = 'data/'
    BASE_PARSED_DATA_PATH = 'parsed_data/'
    IMAGES_PATH = BASE_PARSED_DATA_PATH + 'images/'
    OUTPUT_CSV = ''

    def __init__(self, state, lang, separator= ':', separator_alt = None, ommit = None):
        self.state = state
        #self.columns = columns
        self.lang = lang
        self.separator = separator
        self.ommit = ommit
        self.separator_alt = separator_alt

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

    def process_boxes_text(self, text):
        raw = self.ommit_sentences(text)
        raw = raw.replace('\n\n', '\n').split('\n')
        result = {}
        
        # TODO not abtracted
        result['id'] = raw.pop(0).strip()

        # To add data to previous column
        last_key = None

        # Iter over results
        for r in raw:
            if self.separator in r.lower():
                separated = r.split(self.separator)

                if len(separated) == 2:
                    key = strip_lower(separated[0])
                    value = separated[1].strip()
                    result[key] = value
                    last_key = key

                elif len(separated) == 3:
                    try:
                        key = strip_lower(separated[0])
                        value_1, key_2 = separated[1].split()
                        result[key] = value_1.strip()
                        result[strip_lower(key_2)] = separated[2].strip()
                        last_key = key
                    except Exception as e:
                        logging.error(f'2 separators error: {e} : {raw}')

                else:
                    logging.error(f'More than 2 separators {raw}')

            elif r and not self.separator in r:
                separated = r.split(self.separator_alt)

                # TODO REPEATED CODE :63
                if len(separated) == 2:
                    key = strip_lower(separated[0])
                    value = separated[1].strip()
                    result[key] = value
                    last_key = key

                else:
                    try:
                        result[last_key] = result[last_key] + ' ' + r.strip()
                    except Exception as e:
                        logging.error(f'Exception: {e}: {raw}') 

        return result
        

    def run(self):
        pdf_files_paths = self.get_this_state_files()

        for pdf_file_path in pdf_files_paths:
            logging.info(f'Converting {pdf_file_path} ...')
            logging.info('Converting pdf to imgs ...')
            images_list = pdf_to_img(pdf_file_path, dpi=500)
            items = []

            for page in images_list[2:]:
                #page.show()
                logging.info('Getting boxes..')

                boxes = get_boxes(page)
                for box in boxes:
                    # todo get number and id separated
                    text = pytesseract.image_to_string(box, lang=self.lang, config='--psm 6')
                    item = self.process_boxes_text(text)
                    items.append(item)

            # TODO path
            output_path = self.OUTPUT_CSV + self.state + '.csv'
            items_to_csv(items, output_path)

            logging.info(f'Converted to csv: {output_path}')

if __name__ == '__main__':
    lang = 'eng'
    Parser('delhi', lang, separator_alt = ' - ', ommit = ['Photo is', '\nAvailable']).run()

