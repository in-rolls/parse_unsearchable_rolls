import os
from .parser import Parser
import logging
from collections import OrderedDict
import re
import traceback


import numpy as np
import tesserocr
from PIL import Image
from matplotlib import cm

#from PIL import Image


logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(message)s',
                    handlers=[logging.FileHandler("parser/debug.log"),
                              logging.StreamHandler()])

class GoogleVisionParser(Parser):

    def paste_boxes_into_image(self, boxes):
        
        breakpoint()
        one_array = np.vstack([_ for _ in boxes[:10]])

        im =  Image.fromarray(np.uint8(cm.gist_earth(one_array)*255))
        im.save('one.png')
        breakpoint()
        return im
  
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


    def process_pdf(self, pdf_file_path):
        logging.info(f'Converting {pdf_file_path} to img...')
        try:
            pages = self.pdf_to_img(pdf_file_path, dpi=self.DPI)
            items = []
            boxes = []
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
                boxes.extend(self.get_boxes(page, self.contours))

            # paste together
            # send google
            # interpret

            merged_boxes = self.paste_boxes_into_image(boxes)
            breakpoint()
            interpretation = self.google_vision_req(merged_boxes)
            self.process_interpretation(interpretation)


            # # concurrent tesserocr
            # def get_data(im):
            #     try:
            #         item = base_item.copy()
            #         text = tesserocr.image_to_text(im, lang=self.lang, psm=tesserocr.PSM.SINGLE_BLOCK) #tesserocr.PSM.SPARSE_TEXT
            #         processed_box = self.process_boxes_text(text)
            #         item.update(processed_box)
            #         item = self.check_data(item)
            #         items.append(item)
            #     except Exception as e:
            #         logging.error(traceback.format_exc())

            # bbim = [Image.fromarray(np.uint8(cm.gist_earth(box)*255))  for box in boxes] 

            # with concurrent.futures.ThreadPoolExecutor(max_workers=self.tesseorc_workers) as executor:
            #     future = executor.map(get_data, bbim)
            #     try:
            #         future.result()
            #     except:
            #         pass

            logging.info(f'Formatting and exporting {pdf_file_path} data..')
            formatted_items = self.format_items(items, first_page_results, last_page_results)
            output_path = self.output_csv + filename + '.csv'
            self.items_to_csv(formatted_items, output_path, self.columns)
            logging.info(f'Converted to csv: {output_path}')
        except:
            logging.error(f'Error converting {pdf_file_path}: {traceback.format_exc()}')
