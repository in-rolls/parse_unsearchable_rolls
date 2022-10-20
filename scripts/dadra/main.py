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
    DPI = 300
    MALE = 'પુરૂષ'
    FEMALE = 'સ્ત્રી'
    
    P_KEYWORDS = {
        'polling_station_name': ' મતદડન કકનનનફ નબન ર અનન નડમ',
        # 'polling_station_address': ''
        }
    
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

    def known_exceptions(self, result, r, raw):
        is_splitted = False
        
        try:
            if r == raw[2]:
                house_no = re.findall('\s(\d.?)', r)
                if house_no:
                    result['ઘર નં'] = house_no[0]
                    is_splitted = True
        except:
            pass

        return result, is_splitted

    def correct_alignment(self, raw):
        # If correct aligment acrivated
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

    def male_or_female(self, r):
        # Force Male or Female
        if self.FEMALE in r:
            return self.FEMALE
        elif self.MALE in r:
            return self.MALE
        else:
            try:
                return r.split(':')[-1].strip()
            except:
                return 'UNREADABLE'

if __name__ == '__main__':

    columns = []
    lang = 'eng+guj'

    first_page_coordinates = {
        'rescale': False,
        'mandal': '', 
        'part_no': [2100, 225, 2350-2100, 340-225],
        'police': [245, 2500, 1684-245, 2857-2500],
        'ac': [1000, 250, 1500-1000, 330-250],
    } 

    last_page_coordinates = {
        'rescale': False,
        'coordinates':[
        [1688, 1400, 2344-1688, 1500-1400]
        ],
        'year': [1100, 700, 1300-1100, 1300-700]
    }

    boxes_columns = ['મતદારનુ નામ', 'પિતાનુ નામ', 'પતિનુ નામ', 'ઘર નં', 'માતાનુ નામ', 'ઉમર', 'જાતિ'] 
    columns = ['main_town', 'revenue_division', 'police_station', 'mandal', 'district', 'pin_code', 'part_no', 'polling_station_name', 'polling_station_address', 'ac_name', 'parl_constituency', 'year', 'state', 'count', 'id'] + boxes_columns + ['net_electors_male', 'net_electors_female', 'net_electors_third_gender', 'net_electors_total', 'file_name']

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
        'limits_h': (300,400),
        'limits_w': (700,800),
        'remove_limits': (70/2, 400/2)
    }
    
    DD = Dadra('dadra', lang, contours, year='main', boxes_columns=boxes_columns, columns=columns, translate_columns=translate_columns, first_page_coordinates=first_page_coordinates, last_page_coordinates=last_page_coordinates, rescale=300/500, multiple_rows=False)

    DD.run()


