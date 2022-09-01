import sys
sys.path.append('../')
#from parse_unsearchable_rolls.parser.parser import Parser
from parse_unsearchable_rolls.scripts.gujarat.main import Gujarat

import pytesseract
import re
import traceback

from collections import OrderedDict

# methods specific to this state
 
class Dadra(Gujarat):

    MALE = 'પુરૂષ'
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

    def correct_alignment(self, raw):

        if len(raw) == 7:
            age = ''.join(re.findall('\d+', raw[5]))
            gender = self.male_or_female(raw[5])
            ordered = raw[:3] + [raw[4] + raw[3]] + [self.age + ': ' + age] + [self.gender + ': ' + gender]
        elif len(raw) == 6:
            age = ''.join(re.findall('\d+', raw[4]))
            gender = self.male_or_female(raw[4])
            ordered = raw[:3] + [raw[3]] + [self.age + ': ' + age] + [self.gender + ': ' + gender]
        elif len(raw) == 5:
            age = ''.join(re.findall('\d+', raw[3]))
            gender = self.male_or_female(raw[3])
            ordered = raw[:3] + [self.age + ': ' + age] + [self.gender + ': ' + gender]
        else:
            print(raw)
            breakpoint()

        return ordered

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

    columns = ['main_town', 'revenue_division', 'police_station', 'mandal', 'district', 'pin_code', 'part_no', 'polling_station_name', 'polling_station_address', 'ac_name', 'parl_constituency', 'year', 'state', 'accuracy score', 'count', 'id', 'મતદારનુ નામ', 'પિતાનુ નામ', 'પતિનુ નામ', 'ઘર નં', 'માતાનુ નામ', 'ઉમર', 'જાતિ', 'net_electors_male', 'net_electors_female', 'net_electors_third_gender', 'net_electors_total', 'file_name']

    translate_columns = {
        'મતદારનુ નામ': 'name',
        'પિતાનુ નામ': 'father\'s name',
        'પતિનુ નામ': 'husband\'s name',
        'ઘર નં': 'house_number',
        'માતાનુ નામ': 'mother\'s name',
        'ઉમર':'age',
        'જાતિ':'sex'
    }

    contours = ((500,800), (300,1500), (70, 400))
    
    DD = Dadra('dadra', lang, contours, columns=columns, translate_columns=translate_columns, rescale=600/500)

    DD.run(2)


