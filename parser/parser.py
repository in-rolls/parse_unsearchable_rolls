import os
from .helpers import Helpers
from .first_last_page import FirstLastPage 
import logging
#import pytesseract
from collections import OrderedDict
import re
# import time
# import multiprocessing
import traceback

import concurrent.futures
#import queue
import time

import numpy as np
import tesserocr


logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(message)s',
                    handlers=[logging.FileHandler("parser/debug.log"),
                              logging.StreamHandler()])

class Parser(Helpers, FirstLastPage):
    BASE_DATA_PATH = 'data/'    
    DPI = 600
    SEPARATORS = [":-", ":", ">", "=", ';']
    MAX_WORKERS = 7
    
    # Pages where not to search boxes
    FIRST_PAGES = 1
    LAST_PAGE = -1

    # Initiate parameters
    first_page_coordinates={}
    last_page_coordinates={}
    translate_columns = {}
    multiple_rows = False
    rescale = 1
    checks = {}
    lang = 'eng'
    unreadable = 'UNREADABLE'

    def run(self):
        pdf_files = self.get_file_paths('in/')
        pdf_files = self.check_processed_files(pdf_files)

        for pdf in pdf_files:
            self.process_pdf(pdf)

    def __init__(self, state, year=None, ignore_last=False, handle=[], check_supplementary_data=None, check_updated_counts=None, detect_columns=False):
        self.test = os.getenv('TEST')
        self.state = state.lower()
        self.handle = handle
        self.ignore_last = ignore_last
        self.year = year
        self.stop = False # testing
        self.stats_nums = None # for multiple check of stats nums
        self.check_updated_counts = check_updated_counts
        self.check_supplementary_data = check_supplementary_data

        # if there's no boxes columns detect them
        try:
            self.columns = ['main_town', 'revenue_division', 'police_station', 'mandal', 'district', 'pin_code', 'part_no', 'polling_station_name', 'polling_station_address', 'ac_name', 'parl_constituency', 'year', 'state', 'number', 'id'] + self.boxes_columns + ['net_electors_male', 'net_electors_female', 'net_electors_third_gender', 'net_electors_total', 'file_name']
            self.detect_columns = False
        except:
            self.detect_columns = True

        # When detecting columns avoid joining rows and eliminate columns
        if detect_columns:
            self.columns = []
            self.multiple_rows = False
            self.detect_columns = True

        # Column names one time convertion
        self.house_number = 'house number'
        self.age = 'age'
        self.gender = 'sex'

        for k,v in self.translate_columns.items():
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

    def handle_ids(self, raw, result):
        id_ = raw.pop(0).strip()
        first = id_.split(' ')

        # join separated id
        if len(first) > 2:
            first = [first[0], ''.join(first[1:])]

        if len(first) > 1:
            result.update({
                'number': first[0],   
                'id': first[1]
            })
        elif first:
            if re.findall('[a-z]', first[0].lower()):
                result['id'] = first[0]
            else:
                result['number'] = first[0]

        return raw, result

    def process_boxes_text(self, text):
        result = OrderedDict()
            
        # clean raw text
        raw = text.replace('\n\n', '\n').split('\n')
        try:
            raw = [x.strip() for x in raw]
            raw = list(filter(None, raw))
        except Exception as e:
            logging.error(f'Clean error: {e}: {raw}')

        # If correct aligment is activated
        try:
            raw = self.correct_alignment(raw)
        except:
            pass

        # Get and handle Id and count data
        raw, result = self.handle_ids(raw, result)

        # To add data to previous column
        last_key = None

        # If ignore last row option is activated
        if self.ignore_last:
            raw = list(filter(None, raw))
            raw = raw[:-1]

        # Iter over results and split with separators
        for r in raw:
            # Split data depending on known columns
            if not self.detect_columns:
                result, last_key, is_splitted = self.columns_split(r, self.columns, result, last_key)

            # Detect columns by splitting with separators if detect_columns is activated
            else:
                is_splitted = False
                for sep in self.detect_columns:
                    if sep in r.lower():
                        result, last_key, is_splitted = self.separator_split(r, sep, result, last_key)

                        if is_splitted:
                            break

            # Try known exceptions when line not found with columns
            if r and not is_splitted:
                result, is_splitted = self.known_exceptions(result, r, raw)

            # If line not recognized add data to previous field
            if r and not is_splitted and self.multiple_rows:
                try:    
                    # Add last line to previous key
                    result[last_key] = result[last_key] + ' ' + r.strip()
                except Exception as e:
                    logging.warning(f'Add extra last key: {r}; Exception: {e}: ; Line: {raw} ; Result: {result}') 
                    # logging.warning(f'Add extra last key: {r} \nException: {traceback.format_exc()}: \n{raw} \n{result}') 
            elif r and not is_splitted:
                pass

        # # Get accuracy score if check accuracy is activated
        # if self.checks:
        #     result['accuracy score'] = self.check_accuracy(result, raw)
        
        return result

    def male_or_female(self, r):
        # Force Male or Female
        if self.FEMALE in r:
            return self.FEMALE
        elif self.MALE in r:
            return self.MALE

        return 'UNREADABLE'

    def handle_separator_without_column(self, r, result, last_key):
        # For when column isnt found but there's a separator in the field

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
        # Split columns by known columns

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
        
    # def check_accuracy(self, d, raw_data):
    #     # Checks data and returns an accuracy score dependint on checks dictionary

    #     accuracy = 0 
    #     for k,v in self.checks.items():
    #         extracted_value = d.get(k, '').lower().strip()

    #         if not extracted_value:
    #             accuracy -= 1
    #         else:
    #             for condition in v:
    #                 checked = ''.join(re.findall(condition['r'], extracted_value))
    #                 if checked != extracted_value:
    #                     accuracy += condition['s']

    #     return accuracy 

    def process_pdf(self, pdf_file_path):
        # Get pdf file, process convertion and process output

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

            pages_range = pages[self.FIRST_PAGES:self.LAST_PAGE]
            is_supp = False
            for i, page in enumerate(pages_range):
                logging.info(f'Processing page {self.FIRST_PAGES + i+1}')

                base_item.update(self.get_header(page))
                boxes = self.get_boxes(page, self.contours)

                #logging.debug(f'{len(boxes)} boxes detected')

                # Check last 15 pages for supplementary data
                if self.check_updated_counts:
                    if i > len(pages_range) - 15:
                        last_page_results = self.update_counts(page, last_page_results)
                if self.check_supplementary_data:
                    if i > len(pages_range) - 15 and not is_supp:
                        is_supp = self.mark_supplementary_data(page)

                # concurrent tesserocr
                def get_data(im):
                    try:
                        item = base_item.copy()
                        text = tesserocr.image_to_text(im, lang=self.lang, psm=tesserocr.PSM.SINGLE_BLOCK) #tesserocr.PSM.SPARSE_TEXT
                        processed_box = self.process_boxes_text(text)
                        item.update(processed_box)
                        item['supplementary_data'] = is_supp if is_supp else '' # add if data is supplementary or not
                        item = self.check_data(item)
                        items.append(item)
                    except Exception as e:
                        logging.error(traceback.format_exc())

                bbim = [self.array_to_im(box) for box in boxes] 

                if not self.test:
                    with concurrent.futures.ThreadPoolExecutor(max_workers=self.MAX_WORKERS) as executor:
                        for r in executor.map(get_data, bbim):
                            if r:
                                logging.warning(r)
                else:
                    [get_data(_) for _ in bbim]



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
                    {**first_page_results, **additional, **item, **last_page_results}
                )
            except Exception as e:
                print(f'Format error: {item} - {e}')

        return result

    def check_data(self, item):
        return item

    def known_exceptions(self, result, r, raw):
        is_splitted = False
        return result, is_splitted


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

