import sys
sys.path.append('../')
from parse_unsearchable_rolls.parser.parser import Parser
import pytesseract
import re

from collections import OrderedDict

# methods specific to this state
 
class Gujarat(Parser):
    def get_header(self, page):
        result = OrderedDict()
        a,b,c,d = 0,0,4700,335
        header = self.crop_section(a,b,c,d,page)
    
        text = (pytesseract.image_to_string(header, config='--psm 6', lang=self.lang))
        ano = ''.join(re.findall('Assembly Constituency No and Name: (\d)', text)).strip()
        an = ''.join(re.findall('Assembly Constituency No and Name: \d-(.*)Part', text)).strip()
        sn = ''.join(re.findall('Section No and Name .*-(.*)', text)).strip()
        sno = ''.join(re.findall('Section No and Name .*(\d)', text)).strip()
        pn = ''.join(re.findall('Assembly Constituency No and Name: .*:(.*)', text)).strip()

        result.update({
            'assambly_constituency_name': an,
            'assambly_constituency_number': ano,
            'section name': sn,
            'section number': sno,
            'part number': pn
        })

        return result
     
    def format_items(self, items, first_page_results, last_page_results):
        result = []

        additional = {
            'year': '2021',
            'state': self.state
        }

        for item in items:
            try:
                result.append(
                    first_page_results | additional | item | last_page_results
                )
            except Exception as e:
                print(f'Format error: {item} - {e}')

        return result

if __name__ == '__main__':

    columns = []
    lang = 'eng+guj'

    contours = ((500,800), (300,1500), (70, 400))
    Gujarat('gujarat', lang, contours, test=True, separators = [':-', '--', '=='], rescale = 600/500 ).run()
