import os
from .helpers import Helpers
from .first_last_page import FirstLastPage 
import logging
#import pytesseract
from collections import OrderedDict
import re
import time
import multiprocessing
import traceback

import concurrent.futures
#import queue
import time

import numpy as np
import tesserocr
from PIL import Image
from matplotlib import cm


logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(message)s',
                    handlers=[logging.FileHandler("parser/debug.log"),
                              logging.StreamHandler()])

class Parser(Helpers, FirstLastPage):
    BASE_DATA_PATH = 'data/'
    DPI = 600
    SEPARATORS = [":-", ":", ">", "=", ';']
    FIRST_PAGES = 1

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
                self.process_pdf(pdf)

    def __init__(self, state, lang, contours, year=None, ignore_last=False, translate_columns={} , first_page_coordinates={}, last_page_coordinates={}, rescale=1, columns=[], boxes_columns=[], checks=[], handle=[], detect_columns=[]):

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
        self.year = year
        self.stop = False # testing
        self.boxes_columns = boxes_columns
        self.stats_nums = None # for multiple check of stats nums
        
        if self.test:
            self.tesseorc_workers = 1
        else:
            self.tesseorc_workers = 8

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
        if self.year:
            self.output_csv += self.year + '/'

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
            result.update({
                'count': first[0],   
                'id': first[1]
            })
        elif first:
            if re.findall('[a-z]', first[0].lower()):
                result['id'] = first[0]
            else:
                result['count'] = first[0]

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

            # detect columns splitting with separators
            else:
                is_splitted = False
                for sep in self.detect_columns:
                    if sep in r.lower():
                        result, last_key, is_splitted = self.separator_split(r, sep, result, last_key)

                        if is_splitted:
                            break

            # Try known exceptions when line not found with columns
            if r and not is_splitted:
                result, is_splitted = self.known_exceptions(result, r)

            # If line not recognized add data to previous field
            if r and not is_splitted:
                try:    
                    # Add last line to previous key
                    result[last_key] = result[last_key] + ' ' + r.strip()
                except Exception as e:
                    logging.warning(f'Add extra last key: {r}; Exception: {e}: ; Line: {raw} ; Result: {result}') 
                    # logging.warning(f'Add extra last key: {r} \nException: {traceback.format_exc()}: \n{raw} \n{result}') 

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
                try:
                    # search age and gender
                    result[self.age] = ''.join(re.findall('\d+', r)).strip()
                    result[self.gender] = self.male_or_female(r)

                    is_splitted, last_key = True, self.gender
                except:
                    pass

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

        for c_name in self.boxes_columns:
            cc = c_name.replace('_', ' ').replace('\'', '.?') 

            # find column name in line
            found = re.findall('^' + cc + '.*?([\w\d].*)', low_r)
            
            if found and any([x == c_name  for x in self.handle]):
                return self.handle_separation(r, result)

            elif found:
                v = ''.join(found).strip()
                result[c_name] = v
                last_key = c_name
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
        logging.info(f'Converting {pdf_file_path} to img...')
        try:
            pages = self.pdf_to_img(pdf_file_path, dpi=self.DPI)
            items = []
            filename = pdf_file_path.split('/')[-1].strip('.pdf')
            base_item = {
                'file_name' : filename
                }

            if not self.detect_columns:
                logging.info('Parsing first and last page data..')
                first_page_results, last_page_results = self.handle_extra_pages(pages)
            else:
                first_page_results, last_page_results = {}, {} 

            logging.info(f'Detecting and parsing {pdf_file_path} boxes..')
            for page in pages[self.FIRST_PAGES:-1]:
                base_item.update(self.get_header(page))
                boxes = self.get_boxes(page, self.contours)

                # concurrent tesserocr
                def get_data(im):
                    try:
                        item = base_item.copy()
                        text = tesserocr.image_to_text(im, lang=self.lang, psm=tesserocr.PSM.SINGLE_BLOCK) #tesserocr.PSM.SPARSE_TEXT
                        processed_box = self.process_boxes_text(text)
                        item.update(processed_box)
                        item = self.check_data(item)
                        items.append(item)
                    except Exception as e:
                        logging.error(traceback.format_exc())

                bbim = [Image.fromarray(np.uint8(cm.gist_earth(box)*255))  for box in boxes] 

                with concurrent.futures.ThreadPoolExecutor(max_workers=self.tesseorc_workers) as executor:
                    future = executor.map(get_data, bbim)
                    try:
                        future.result()
                    except:
                        pass

            logging.info(f'Formatting and exporting {pdf_file_path} data..')
            formatted_items = self.format_items(items, first_page_results, last_page_results)
            output_path = self.output_csv + filename + '.csv'
            self.items_to_csv(formatted_items, output_path, self.columns)
            logging.info(f'Converted to csv: {output_path}')
        except:
            logging.error(f'Error converting {pdf_file_path}: {traceback.format_exc()}')

    def basic_clean(self, dic):
        try:
            cleaned = {}
            for k,v in dic.items():
                cleaned[k] = v.strip().replace(' ,', ',').replace('\n','')

            return cleaned
        except:
            return dic

    def format_items(self, items, first_page_results, last_page_results):
        result = []

        additional = {
            #'year': '',
            'state': self.state
        }

        first_page_results = self.basic_clean(first_page_results)
        last_page_results = self.basic_clean(last_page_results)

        for item in items:
            item = self.basic_clean(item)
            try:
                result.append(
                    first_page_results | additional | item | last_page_results
                )
            except Exception as e:
                print(f'Format error: {item} - {e}')

        return result

    def check_data(self, item):
        return item

    def known_exceptions(self, result, r):
        is_splitted = False
        return result, is_splitted


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

