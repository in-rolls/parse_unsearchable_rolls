import sys
import pytesseract
import re
from collections import OrderedDict
import numpy as np
import pandas as pd
import logging

sys.path.append('../')
from parse_unsearchable_rolls.scripts.delhi.main import Delhi

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(message)s',)


class FixStats(Delhi):

    def main(self):
        out_files = self.get_this_state_files('out/', ext='.csv')

        for out_file in out_files:
            logging.info(f'Processing file: {out_file}')
            pdf_file_path = out_file.replace('out/','in/').replace('.csv','.pdf') 
            pages = self.pdf_to_img(pdf_file_path, dpi=self.DPI)
            first_page_results, last_page_results = self.handle_extra_pages(pages)

            del last_page_results['year']

            df = pd.read_csv(out_file)
            # drop last row
            df.drop(df.tail(1).index,inplace=True)

            df = df.convert_dtypes()
            # replace stats
            for k,v in last_page_results.items():
                df[k] = v

            fixed_path =  out_file.replace('delhi','delhi-fixed')
            df.to_csv(fixed_path, index = False, header=True)


if __name__ == '__main__':
    contours = ((500,800), (300,1500), (60, 400))
    last_page_coordinates = {
        'rescale': True,
        'coordinates':[
        [2504, 988, 1200,95],
        [2494, 2486, 1200, 95],
        [2494, 2516, 1200, 95]
        ]
    }
    first_page_coordinates = {
        'mandal': [1770, 1900, 1480, 545],
        'part_no': [3165, 295, 620, 190],
        'police': [185, 3330, 1900, 572],
        'ac': [180, 290, 2806, 405],
        }

    FS = FixStats('delhi', 'eng', contours=contours, last_page_coordinates=last_page_coordinates, rescale = 600/500).main()
    