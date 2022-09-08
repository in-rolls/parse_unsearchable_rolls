import sys
sys.path.append('../')
#from parse_unsearchable_rolls.parser.parser import Parser
from parse_unsearchable_rolls.scripts.gujarat.main import Gujarat

import pytesseract
import re


from collections import OrderedDict

# methods specific to this state
 
class Daman(Gujarat):

    MALE = 'પૂરૂષ'
    FEMALE = 'સ્ત્રી'

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
    
    def get_header(self, page):
        result = OrderedDict()
        return result
     
    def format_items(self, items, first_page_results, last_page_results):
        result = []

        additional = {
            #'year': '2021',
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

    def check_data(self, item):
        # house no check
        test_h = item.get('ઘરનં', '').strip().replace('-', '').replace('|', '')
        if not test_h :
            item['ઘરનં'] = ''

        return item

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

    columns = []
    lang = 'eng+guj'

    first_page_coordinates = {
        'rescale': False,
        'mandal': [2850, 3520, 4520-2850, 4736-3520],
        'part_no': [4200,500,4600-4200,900-500],
        'police': [504,4948,2154-504,5274-4948],
        'ac': [382+50,450+50,2207+1500,475],
    } 

    last_page_coordinates = {
        'rescale': False,
        'coordinates':[
        [3030,2321,4669-3030,2653-2321]
        ],
        'year': [1354, 2434, 2460-1354, 2640-2434]
    }

    boxes_columns = ['નામ', 'પિતાનુ નામ', 'પતીનું નામ', 'ઘરનં', 'માતાનુ નામ', 'ઉમર', 'જાતિ']
    columns = ['main_town', 'revenue_division', 'police_station', 'mandal', 'district', 'pin_code', 'part_no', 'polling_station_name', 'polling_station_address', 'ac_name', 'parl_constituency', 'year', 'state', 'accuracy score', 'count', 'id'] + boxes_columns + ['net_electors_male', 'net_electors_female', 'net_electors_third_gender', 'net_electors_total', 'file_name']

    translate_columns = {
        'નામ': 'name',
        'પિતાનુ નામ': 'father\'s name',
        'પતીનું નામ': 'husband\'s name',
        'ઘરનં': 'house_number',
        'માતાનુ નામ': 'mother\'s name',
        'ઉમર':'age',
        'જાતિ':'sex'
    }

    contours = ((500,800), (300,1500), (70, 400))

    DM = Daman('daman', lang, contours, year='2015', translate_columns=translate_columns, last_page_coordinates=last_page_coordinates, first_page_coordinates=first_page_coordinates, columns=columns, boxes_columns=boxes_columns, rescale=600/500, handle=['ઉમર', 'જાતિ'] )
    DM.run(3)


