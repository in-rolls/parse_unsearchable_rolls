import sys
sys.path.append('../')
#from parse_unsearchable_rolls.parser.parser import Parser
from parse_unsearchable_rolls.scripts.gujarat.main import Gujarat

import pytesseract
import re
import traceback

from collections import OrderedDict

# methods specific to this state
 
class Kerala(Gujarat):
    
    DPI = 300
    MALE = 'പു'
    FEMALE = 'സ്ത്രീ'
    #SEPARATORS = ['\u200c', '\u200d']
    FIRST_PAGES = 2
    LAST_PAGE = None
    
    P_KEYWORDS = {
        'polling_station_name': ' મતદડન કકનનનફ નબન ર અનન નડમ',
        # 'polling_station_address': ''
        }
    
    # def get_header(self, page):
    #     result = OrderedDict()
    #     return result
     
    # def extract_4_numbers(self, cropped):
    #     text = (pytesseract.image_to_string(cropped, config='--psm 6', lang=self.lang)) 
    #     c = ''
    #     a,b,d = re.findall(r'\d+', text)
    #     d = int(a) + int(b)

    #     return a,b,c,d

    # def get_police_data(self, result, cs, im, rescale):
    #     #a, b, c, d = self.rescale_cs(cs) if rescale else cs # police name name and address
    #     a, b, c, d = cs
    #     crop_police = self.crop_section(a, b, c, d, im)
    #     text = (pytesseract.image_to_string(crop_police, config='--psm 6', lang=self.lang)) 
    #     result['polling_station_name'] = text.split(',')[-1]

    #     return result

    # def get_ac(self, text):
    #     try: 
    #         ac_name = text[0].strip(',').strip()
    #     except:
    #         ac_name = ''

    #     return {
    #         'ac_name':ac_name,
    #         'parl_constituency': ''
    #     }



    def known_exceptions(self, result, r, raw):
        is_splitted = False

        sex_key = '(സ്ത്രീ /പു)'
        age_key = 'വയസ്സ്'
        
        if sex_key in r or age_key in r:
            try:
                values = r.split('\u200c')[-1].strip().split(' ')
                if len(values) > 1:
                    result[sex_key] = values[0]
                    result[age_key] = values[1][1:]
                elif len(values) == 1:
                    result[sex_key] = self.male_or_female(values[0])
            except:
                pass

        return result, is_splitted


    def male_or_female(self, r):
        # Force Male or Female
        if self.FEMALE in r:
            return self.FEMALE
        elif self.MALE in r:
            return self.MALE
        else:
            return 'UNREADABLE'

if __name__ == '__main__':
    columns = []

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

    boxes_columns = ['പേര്', 'അച്ഛന്റെ പേര്', 'ഭര്‍ത്താവിന്റെ പേര്', 'വീട്ടുനമ്പര്', 'അമ്മയുടെ പേര്', 'വീട്ടുപേര്', 'വയസ്സ്', '(സ്ത്രീ /പു)'] 
    columns = ['main_town', 'revenue_division', 'police_station', 'mandal', 'district', 'pin_code', 'part_no', 'polling_station_name', 'polling_station_address', 'ac_name', 'parl_constituency', 'year', 'state', 'count', 'id'] + boxes_columns + ['net_electors_male', 'net_electors_female', 'net_electors_third_gender', 'net_electors_total', 'file_name']

    translate_columns = {
        'പേര്': 'name',
        'അച്ഛന്റെ പേര്': 'father\'s name',
        'ഭര്‍ത്താവിന്റെ പേര്': 'husband\'s name',
        'വീട്ടുനമ്പര്': 'house_number',
        'അമ്മയുടെ പേര്': 'mother\'s name',
        'വീട്ടുപേര്': 'household name',
        'വയസ്സ്':'age',
        '(സ്ത്രീ /പു)':'sex'
    }

    contours = ((230,270), (750,850), (70/2, 400/2))
    
    #KR = Kerala('kerala', lang, contours, boxes_columns=boxes_columns, columns=columns, translate_columns=translate_columns, first_page_coordinates=first_page_coordinates, last_page_coordinates=last_page_coordinates, rescale=300/500, multiple_rows=False)

    KR = Kerala('kerala', 'mal+eng', contours, rescale=300/500, boxes_columns=boxes_columns, columns=columns,  multiple_rows=False)#detect_columns = ['\u200c', '\u200d'])


    KR.run(0)


