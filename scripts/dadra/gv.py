import sys
sys.path.append('../')
from parse_unsearchable_rolls.parser.google_vision_parser import GoogleVisionParser
#from parse_unsearchable_rolls.scripts.gujarat.main import Gujarat

import pytesseract
import re
import traceback

from collections import OrderedDict

# methods specific to this state
 
class Dadra(GoogleVisionParser):
    MALE = 'પુરૂષ'
    FEMALE = 'સ્ત્રી'

    # MANDAL_KEYWORDS = {
    #     'મુખ્ય ગામ/શહેર': 'main_town',
    #     #'Ward No': 'revenue_division',
    #     'પોલિસ સ્ટેશન': 'police_station',
    #     'પોસ્ટ ઓફિસ': 'mandal',
    #     'જીલ્લા': 'district',
    #     'પીન કોડ': 'pin_code'
    # }
    
    # P_KEYWORDS = {
    #     'polling_station_name': 'મતદાન કેન્દ્રનો',
    #     # 'polling_station_address': ''
    #     }
    
    def get_header(self, page):
        result = OrderedDict()
        return result
     
    def extract_4_numbers(self, cropped):
        text = (pytesseract.image_to_string(cropped, config='--psm 6', lang=self.lang)) 
        c = ''
        a,b,d = re.findall(r'\d+', text)
        d = int(a) + int(b)

        return a,b,c,d

    def get_police_data(self, result, cs, im, rescale):
        #a, b, c, d = self.rescale_cs(cs) if rescale else cs # police name name and address
        a, b, c, d = cs
        crop_police = self.crop_section(a, b, c, d, im)
        text = (pytesseract.image_to_string(crop_police, config='--psm 6', lang=self.lang)) 
        result['polling_station_name'] = text.split(',')[-1]

        return result

    def get_ac(self, text):
        try: 
            ac_name = text[0].strip(',').strip()
        except:
            ac_name = ''

        return {
            'ac_name':ac_name,
            'parl_constituency': ''
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
            print('warning' + raw)

        return ordered

if __name__ == '__main__':

    columns = []
    lang = 'eng+guj'

    first_page_coordinates = {
        'rescale': False,
        'mandal': '', 
        'part_no': [4200, 450, 4600-4200, 690-450],
        'police': [500, 5000, 3000 - 500, 5400 - 5000],
        'ac': [1600+400, 500 , 3000-1600+400, 665-500],
    } 

    last_page_coordinates = {
        'rescale': False,
        'coordinates':[
        [3400, 2786, 4700-3400, 3000-2786]
        ],
        'year': [1600, 2300, 2500-1600, 2500-2300]
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

    contours = {
        'limits_h': (500,800),
        'limits_w': (300,1500),
        'remove_limits': (70, 400)
    }
    
    DD = Dadra('dadra', lang, contours, last_page_coordinates=last_page_coordinates, first_page_coordinates=first_page_coordinates ,columns=columns, translate_columns=translate_columns)

    DD.run()


