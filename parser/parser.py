import os
from .helpers import get_boxes, pdf_to_img, items_to_csv, strip_lower
import logging
import pytesseract
from collections import OrderedDict
import re

# import matplotlib.pyplot as plt
# import keras_ocr

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(message)s',
                    handlers=[logging.FileHandler("parser/debug.log"),
                              logging.StreamHandler()])

class Parser:
    BASE_DATA_PATH = 'data/'
    DPI = 600

    def __init__(self, state, lang, separator= ':', columns = [], handle = [], separators = [], ommit = None, remove_columns = []):
        self.state = state.lower()
        self.columns = columns
        self.lang = lang
        self.separator = separator
        self.ommit = ommit
        self.separators = separators
        self.handle = handle
        self.remove_columns = remove_columns

        self.output_csv = self.BASE_DATA_PATH + 'out/' + self.state + '/'
        if not os.path.exists(self.output_csv):
            os.makedirs(self.output_csv)

    def get_full_path_files(self, path):
        return [os.path.join(path, f) for f in os.listdir(path)]

    def filter_and_sort(self, objs, ext):
        result = list(filter(lambda x: x.endswith(ext), objs))
        result.sort()
        return result

    def get_this_state_files(self):
        path = f'{self.BASE_DATA_PATH}in/{self.state}'
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

    def split_2(self, separated):
        key = strip_lower(separated[0])
        value = separated[1].strip()
        return key, value

    def custom_split(self, r, separator, result):
        is_splitted = False

        # for exceptions
        #if any([re.findall(f"^[\w]{x}^[\w]", r.lower()) for x in self.handle]):
        if any([x in r.lower() for x in self.handle]):
            return self.handle_separation(r, separator, result)

        # normal split
        else:
            separated = r.split(separator)

            if len(separated) == 2:
                key, value = self.split_2(separated)
                result[key] = value
                last_key = key
                is_splitted = True

            else:
                return self.handle_separation_error(r, separator, result)
        
        return result, last_key, is_splitted

    
    def columns_split(self, r, columns, result, last_key):
        is_splitted = False
        low_r = r.lower().strip()

        for c in columns:
            cc = c.replace('_', ' ').replace('\'', '.?') 

            found = re.findall('^' + cc + '.*?([\w\d].*)', low_r)
            if found and any([x == c  for x in self.handle]):
                return self.handle_separation(r, result)

            elif found:
                v = ''.join(found)
                result[c] = v
                last_key = c
                is_splitted = True
                break
        
        return result, last_key, is_splitted


     
    def process_boxes_text(self, text):
        #logging.info('Processing boxes\' text..')
        raw = self.ommit_sentences(text)
        raw = raw.replace('\n\n', '\n').split('\n')
        result = OrderedDict()
        
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
            if not self.columns:
                is_splitted = False
                for sep in self.separators:
                    if sep in r.lower():
                        result, last_key, is_splitted = self.custom_split(r, sep, result)

                        if is_splitted:
                            break
            else:
                result, last_key, is_splitted = self.columns_split(r, self.columns, result, last_key)

            if r and not is_splitted:
                try:
                    result[last_key] = result[last_key] + ' ' + r.strip()
                except Exception as e:
                    logging.error(f'Exception: {e}: {raw}') 
                    #breakpoint()
                    result, last_key, is_splitted = self.handle_separation_error(r, self.separators, result)
        return result

    # def handle_extra_pages(self, pages):
    #     # Overwrite with particular scripts
    #     return {}, {}

    # def format_items(self, items, first_page_results, last_page_results):
    #     # Overwrite with particular scripts
    #     return items

    # def get_header(self, page):
    #     # Overwrite with particular scripts
    #     return {}

    def check_columns(self, items):
        result = []
        for i in items:
            for rk in self.remove_columns:
                if rk in i.keys():
                    logging.error(f'Removed {k} from {str(i)}')
                    del i[rk]
            result.append(i)

        return result

    # def export_to_csv(self, items):
    #     df = pd.DataFrame.from_dict(items)
    #     df = self.check_errors(df)
    #     output_path = self.output_csv + self.state + '.csv'
    #     df.to_csv (output_path, index = False, header=True) 


    def run(self):
        pdf_files_paths = self.get_this_state_files()
        if not pdf_files_paths:
            logging.info(f'No files found for {self.state}')

        for pdf_file_path in pdf_files_paths:
            logging.info(f'Converting {pdf_file_path} ...')
            logging.info('Converting pdf to imgs ...')
            pages = pdf_to_img(pdf_file_path, dpi=self.DPI)#, page=(1,6))
            items = []
            filename = pdf_file_path.split('/')[-1].strip('.pdf')

            first_page_results, last_page_results = self.handle_extra_pages(pages)
            for page in pages[2:-1]:
                logging.info('Getting boxes..')

                header = self.get_header(page)
                boxes = get_boxes(page, (500,800), (300,1500), (60, 400))
                for box in boxes:
                    # todo get number and id separated
                    text = pytesseract.image_to_string(box, lang=self.lang, config='--psm 6')

                    #img = keras_ocr.tools.read(box)
                    #prediction_groups = pipeline.recognize([box])
                    #keras_ocr.tools.drawAnnotations(image=img, predictions=prediction_groups[0])

                    item = header.copy()
                    item.update(self.process_boxes_text(text))
                    items.append(item)

            
            #items = self.check_columns(items)
            formatted_items = self.format_items(items, first_page_results, last_page_results)
            output_path = self.output_csv + filename + '.csv'
            items_to_csv(formatted_items, output_path, self.columns)
            logging.info(f'Converted to csv: {output_path}')
