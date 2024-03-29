import sys
sys.path.append('../')
#from parse_unsearchable_rolls.parser.parser import Parser
from parse_unsearchable_rolls.scripts.gujarat.main import Gujarat

import pytesseract
import re


from collections import OrderedDict

# methods specific to this state
 
class Daman(Gujarat):
    MANDAL_KEYWORDS = {
        'મુખ્ય ગામ/શહેર': 'main_town',
        #'Ward No': 'revenue_division',
        'પોલિસ સ્ટેશન': 'police_station',
        'પોસ્ટ ઓફિસ': 'mandal',
        'જીલ્લા': 'district',
        'પીન કોડ': 'pin_code'
    }
    
    P_KEYWORDS = {
        'polling_station_name': 'મતદાન કેન્દ્રનો',
        # 'polling_station_address': ''
        }

    lang = 'eng+guj'
    boxes_columns = ['નામ', 'પિતાન નામ', 'પતીનં નામ', 'ઘરનં', 'માતાન નામ', 'ઉમર', 'જાતિ']
    rescale=600/500
    first_page_coordinates = {
        'rescale': False,
        'mandal': [2858, 3800, 4250-2858, 4933-3800],
        'part_no': [4200,500,4600-4200,900-500],
        'police': [490,5134,2349-504,5657-5134],
        'ac': [382+50,450+50,2207+1500,475],
        'stats_nums': [1572, 6446, 4616-1572, 6588-6446]
    } 
    last_page_coordinates = {
        'rescale': False,
        'coordinates':[
        [3030,2321,4669-3030,2653-2321]
        ],
        'year': [1354, 2434, 2460-1354, 2640-2434]
    }
    translate_columns = {
        'નામ': 'name',
        'પિતાન નામ': 'father\'s name',
        'પતીનં નામ': 'husband\'s name',
        'ઘરનં': 'house_number',
        'માતાન નામ': 'mother\'s name',
        'ઉમર':'age',
        'જાતિ':'sex'
    }
    contours = {
        'limits_h': (500,800),
        'limits_w': (300,1500),
        'remove_limits': (70, 400)
    }
    
    def get_header(self, page):
        result = OrderedDict()
        return result
    
    def check_data(self, item):
        # house no check
        test_h = item.get('ઘરનં', '').strip().replace('-', '').replace('|', '')
        if not test_h :
            item['ઘરનં'] = ''
        return item

    def known_exceptions(self, result, r, raw):
        is_splitted = False
        house_no = re.findall('\s(\d.+)', r)
        if house_no:
            result['ઘરનં'] = house_no[0]
            is_splitted = True

        return result, is_splitted
    
    def get_ac(self, text):
        try: 
            ac_name = text[1].strip()
        except:
            ac_name = ''
        
        try:
            parl_constituency = text[3].strip()
        except:
            parl_constituency = ''

        return {
            'ac_name':ac_name,
            'parl_constituency': parl_constituency
        }

    def handle_separation(self, r, result):
        last_key = None
        is_splitted = False
        age = self.handle[0]
        sex = self.handle[1]

        low_r = r.lower().strip()
        found = re.findall('^' + age, low_r) 
        if found:
            result[age] = ''.join(re.findall(age + '[^\d]*(\d*)', low_r))
            result[sex] = ''.join(re.findall(sex + '[^\w]*(.*)', low_r))

            last_key = sex
            is_splitted = True
       
        return result, last_key, is_splitted

if __name__ == '__main__':
    DM = Daman('daman', year='2017', ignore_last=True)
    DM.run()


