import sys
sys.path.append('../')
from parse_unsearchable_rolls.parser.parser import Parser
#from parse_unsearchable_rolls.parser.helpers import crop_section, show
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


    def handle_separation(self, r, result):
        low_r = r.lower().strip()
        found = re.findall('^age', low_r) 
        if found:
            result['age'] = ''.join(re.findall('age[^\d]*(\d*)', r.lower()))
            result['sex'] = ''.join(re.findall('sex[^\w]*(\w*)', r.lower()))

            last_key = 'sex'
            is_splitted = True
       
        # redundant
#        elif 'house' in low_r:
#            key = 'house number'
#            value = ''.join(re.findall('house number.*?([\d\w].*)', low_r))
#            result[key] = value
#            last_key = key
#            is_splitted = True
        
        # else:
        #     ### check
        #     last_key = None
        #     is_splitted = False

        return result, last_key, is_splitted

     
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
    lang = 'eng+guj'
    RESCALE = 600/500 # from 500 dpi to 600
    checks = {
        'count': [
            {'r': '\d+', 's': -1},
            {'r': '^[^\$|s|e].*', 's': -100}
        ],
        'id': [{
            'r':'\w+', 's': -1
        }],
        'house number': [{
            'r':'[\d|\w]+', 's': -1
        }],
        'age': [{
            'r':'\d+', 's': -1
        }],
        'sex': [{
            'r':'male|female', 's': -1
        }]
    }

    columns = []

    Gujarat('gujarat', lang).run()#, columns = columns, checks = checks).run()
