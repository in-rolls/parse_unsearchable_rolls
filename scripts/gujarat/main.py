import sys
from typing import _get_type_hints_obj_allowed_types
sys.path.append('../')
from parse_unsearchable_rolls.parser.parser import Parser
import pytesseract
import re


from collections import OrderedDict

# methods specific to this state
 
class Gujarat(Parser):
    MANDAL_KEYWORDS = {
        'મુખ્ય ગામ/શહેર': 'main_town',
        #'Ward No': 'revenue_division',
        'પોલિસ સ્ટેશન': 'police_station',
        'પોસ્ટ ઓફિસ': 'mandal',
        'જીલ્લા': 'district',
        'પીન કોડ': 'pin_code'
    }
    
    P_KEYWORDS = {
        'polling_station_name': '',
        'polling_station_address': ''
        }
    
    def get_header(self, page):
        result = OrderedDict()
        # a,b,c,d = 0,0,4700,335
        # header = self.crop_section(a,b,c,d,page)
    
        # text = (pytesseract.image_to_string(header, config='--psm 6', lang=self.lang))
        # ano = ''.join(re.findall('Assembly Constituency No and Name: (\d)', text)).strip()
        # an = ''.join(re.findall('Assembly Constituency No and Name: \d-(.*)Part', text)).strip()
        # sn = ''.join(re.findall('Section No and Name .*-(.*)', text)).strip()
        # sno = ''.join(re.findall('Section No and Name .*(\d)', text)).strip()
        # pn = ''.join(re.findall('Assembly Constituency No and Name: .*:(.*)', text)).strip()

        # result.update({
        #     'assambly_constituency_name': an,
        #     'assambly_constituency_number': ano,
        #     'section name': sn,
        #     'section number': sno,
        #     'part number': pn
        # })

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


if __name__ == '__main__':

    columns = []
    lang = 'eng+guj'

    first_page_coordinates = {
        'rescale': False,
        'mandal': [2869, 3800, 4234-2869,5000-3800],
        'part_no': [4200,500,4600-4200,900-500],
        'police': [520,5150,2000-520,5500-5150],
        'ac': [382+50,450+50,2207+1500,475],
    } 

    last_page_coordinates = {
        'rescale': False,
        'coordinates':[
        [3030,2321,4669-3030,2653-2321]
        ]
    }

    #columns = ['main_town', 'revenue_division', 'police_station', 'mandal', 'district', 'pin_code', 'part_no', 'polling_station_name', 'polling_station_address', 'ac_name', 'parl_constituency', 'year', 'state', 'assambly_constituency_name', 'assambly_constituency_number', 'section name', 'section number', 'part number', 'accuracy score', 'count', 'id', 'નામ', 'પિતાન નામ', 'પતીનં નામ', 'પતીનં નામ', 'માતાન નામ', 'ઘરનં', 'age', 'sex', 'net_electors_male', 'net_electors_female', 'net_electors_third_gender', 'net_electors_total']

    columns = ['main_town', 'revenue_division', 'police_station', 'mandal', 'district', 'pin_code', 'part_no', 'polling_station_name', 'polling_station_address', 'ac_name', 'parl_constituency', 'year', 'state', 'accuracy score', 'count', 'id', 'નામ', 'પિતાન નામ', 'પતીનં નામ', 'માતાન નામ', 'ઘરનં', 'net_electors_male', 'net_electors_female', 'net_electors_third_gender', 'net_electors_total', 'file_name']

    translate_columns = {
        'નામ': 'name',
        'પિતાન નામ': 'father\'s name',
        'પતીનં નામ': 'husband\'s name',
        'ઘરનં': 'house_number',
        #'પતીનં નામ':  'wife\'s name',
        'માતાન નામ': 'mother\'s name',
    }

    contours = ((500,800), (300,1500), (70, 400))
    GJ = Gujarat('gujarat', lang, contours, translate_columns = translate_columns,last_page_coordinates = last_page_coordinates, first_page_coordinates = first_page_coordinates, columns = columns, test=False, separators = [':-', '--', '=='], rescale = 600/500 )

    # 8 cores processing 
    GJ.run(8)


