import os
from turtle import setx
from .helpers import Helpers
from .first_last_page import FirstLastPage 
import logging
import pytesseract
from collections import OrderedDict
import re
import time
import multiprocessing
import traceback

# import matplotlib.pyplot as plt
# import keras_ocr

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(message)s',
                    handlers=[logging.FileHandler("parser/debug.log"),
                              logging.StreamHandler()])

class Parser(Helpers, FirstLastPage):
    BASE_DATA_PATH = 'data/'
    DPI = 600
    SEPARATORS = [":-", ":", ">", "=", ';']

    def run(self, processors):
        # multiprocessing
        pdf_files = self.get_file_paths()

        if not self.test:
            pool = multiprocessing.Pool(processors)
            start_time = time.perf_counter()
            processes = [pool.apply_async(self.process_pdf, args=(pdf,)) for pdf in pdf_files]
            result = [p.get() for p in processes]
            finish_time = time.perf_counter()

            logging.info(f"Program finished in {finish_time-start_time} seconds")
            logging.info(result)
        else:
            for pdf in pdf_files:
                import pprofile
                profiler = pprofile.Profile()
                with profiler:
                    self.process_pdf(pdf)
                profiler.print_stats()

                #self.process_pdf(pdf)

    def __init__(self, state, lang, contours, ignore_last=False, translate_columns={} , first_page_coordinates={}, last_page_coordinates={}, rescale=1, columns=[], checks=[], handle=[], detect_columns=[]):

        self.test = os.getenv('TEST')
        self.state = state.lower()
        self.columns = columns
        self.lang = lang
        self.contours = contours
        self.handle = handle
        self.checks = checks
        self.rescale = rescale
        self.first_page_coordinates = first_page_coordinates
        self.last_page_coordinates = last_page_coordinates
        self.translate_columns = translate_columns
        self.ignore_last = ignore_last
        self.detect_columns = detect_columns

        # Column names one time convertion
        self.house_number = 'house number'
        self.age = 'age'
        self.gender = 'sex'

        for k,v in translate_columns.items():
            if v == 'house_number':
                self.house_number = k
            elif v == 'age':
                self.age = k
            elif v == 'sex':
                self.gender = k

        self.output_csv = self.BASE_DATA_PATH + 'out/' + self.state + '/'
        if not os.path.exists(self.output_csv):
            os.makedirs(self.output_csv)
  
    def process_boxes_text(self, text):
        result = OrderedDict()

        raw = text.replace('\n\n', '\n').split('\n')
            
        # clean raw
        try:
            raw = [x.strip() for x in raw]
            raw = list(filter(None, raw))
        except Exception as e:
            logging.error(f'Clean error: {e}: {raw}')

        try:
            raw = self.correct_alignment(raw)
        except:
            pass

        # TODO not abstracted
        id_ = raw.pop(0).strip()

        first = id_.split(' ')
   
        if len(first) > 1:
            result['count'] = first[0]    
            result['id'] = first[1]
        else:
            result['count'] = ''
            result['id'] = first[0]

        # To add data to previous column
        last_key = None

        if self.ignore_last:
            raw = list(filter(None, raw))
            raw = raw[:-1]

        # Iter over results and split with separators
        for r in raw:
            # split data depending on known columns
            if not self.detect_columns:
                result, last_key, is_splitted = self.columns_split(r, self.columns, result, last_key)

            # automatic split
            else:
                is_splitted = False
                for sep in self.detect_columns:
                    if sep in r.lower():
                        result, last_key, is_splitted = self.separator_split(r, sep, result, last_key)

                        if is_splitted:
                            break

            if r and not is_splitted:
                try:
                    # Add last line to previous key
                    result[last_key] = result[last_key] + ' ' + r.strip()
                except Exception as e:
                    logging.warning(f'Add extra last key: {r} \nException: {traceback.format_exc()}: \n{raw} \n{result}') 
        
        # Get accuracy score
        if self.checks:
            result['accuracy score'] = self.check_accuracy(result, raw)
        
        return result

    def male_or_female(self, r):
        if self.FEMALE in r:
            return self.FEMALE
        elif self.MALE in r:
            return self.MALE
        
        return ''

    def handle_separator_without_column(self, r, result, last_key):
        is_splitted = False
        r = r.replace(';', ':')

        sep = ':'
        count = r.count(sep)
        # accuracy_points = -1

        if count == 1:
            if not self.house_number in result.keys():
                # to house number
                result[self.house_number] = r.split(sep)[-1].strip()
                is_splitted, last_key = True, self.house_number

            else:
                # search age and gender
                result[self.age] = ''.join(re.findall('\d+', r)).strip()
                result[self.gender] = self.male_or_female(r)

                is_splitted, last_key = True, self.gender

        elif count == 2:    
            # gender
            if not self.age in result.keys():
                splitted = r.split(sep)
                result[self.age] = ''.join(re.findall('\d+', splitted[1])).strip()
                result[self.gender] = splitted[-1]
                is_splitted, last_key = True, self.gender
                      
        else:
            logging.warning(f'Split uncaught {r} {result}')

        return result, last_key, is_splitted
    
    def columns_split(self, r, columns, result, last_key):
        is_splitted = False
        low_r = r.lower().strip()

        for c in columns:
            cc = c.replace('_', ' ').replace('\'', '.?') 

            # find column name in line
            found = re.findall('^' + cc + '.*?([\w\d].*)', low_r)
            
            if found and any([x == c  for x in self.handle]):
                return self.handle_separation(r, result)

            elif found:
                v = ''.join(found)
                result[c] = v
                last_key = c
                is_splitted = True
                
                return result, last_key, is_splitted

        # Not found in columns but there's separators in it
        if any([x in r  for x in self.SEPARATORS]):
            result, last_key, is_splitted = self.handle_separator_without_column(r, result, last_key)
                
        return result, last_key, is_splitted
     
        
    def check_accuracy(self, d, raw_data):
        # Checks if data is correct and returns score

        accuracy = 0 
        for k,v in self.checks.items():
            extracted_value = d.get(k, '').lower().strip()

            if not extracted_value:
                accuracy -= 1
            else:
                for condition in v:
                    checked = ''.join(re.findall(condition['r'], extracted_value))
                    if checked != extracted_value:
                        accuracy += condition['s']

        return accuracy 
        


    def translate_input_columns(self):
        translated_columns = []
        for k in self.columns:
            if k in self.translate_columns.keys():
                translated_columns.append(self.translate_columns[k])
            else:
                translated_columns.append(k)

        return translated_columns        



    def process_pdf(self, pdf_file_path):
        logging.info(f'Converting {pdf_file_path} ...')
        logging.info('Converting pdf to imgs ...')
        pages = self.pdf_to_img(pdf_file_path, dpi=self.DPI)
        items = []
        filename = pdf_file_path.split('/')[-1].strip('.pdf')
        base_item = {
            'file_name' : filename
            }

        if not self.detect_columns:
            first_page_results, last_page_results = self.handle_extra_pages(pages)
        else:
            first_page_results, last_page_results = {}, {} 

        for page in pages[2:-1]:
            logging.info('Getting boxes..')

            base_item.update(self.get_header(page))

            boxes = self.get_boxes(page, self.contours)
            for box in boxes:
                # todo get number and id separated
                text = pytesseract.image_to_string(box, lang=self.lang, config='--psm 6')

                item = base_item.copy()
                processed_box = self.process_boxes_text(text)
                item.update(processed_box)
                items.append(item)

        
        #items = self.check_columns(items)
        formatted_items = self.format_items(items, first_page_results, last_page_results)
        output_path = self.output_csv + filename + '.csv'
        self.items_to_csv(formatted_items, output_path, self.columns)
        logging.info(f'Converted to csv: {output_path}')




    # def handle_extra_pages(self, pages):
    #     # Overwrite with particular scripts
    #     return {}, {}

    # def format_items(self, items, first_page_results, last_page_results):
    #     # Overwrite with particular scripts
    #     return items

    # def get_header(self, page):
    #     # Overwrite with particular scripts
    #     return {}

    # def get_ac(self, text):
    #     # Overwrite with particular scripts
    #     return {)

    # def check_data(self, d):
     # Overwrite with particular scripts

    # def export_to_csv(self, items):
    #     df = pd.DataFrame.from_dict(items)
    #     df = self.check_errors(df)
    #     output_path = self.output_csv + self.state + '.csv'
    #     df.to_csv (output_path, index = False, header=True) 