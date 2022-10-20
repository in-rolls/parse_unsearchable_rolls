import sys
sys.path.append('../')
from parse_unsearchable_rolls.parser.parser import Parser
import pytesseract
import re


from collections import OrderedDict

# methods specific to this state
 
class Gujarat(Parser):

    # MALE = ''
    # FEMALE = ''

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
            'year': '2021',
            'state': self.state
        }

        first_page_results = self.basic_clean(first_page_results)
        last_page_results = self.basic_clean(last_page_results)

        for item in items:
            item = self.basic_clean(item)
            try:
                result.append(
                    first_page_results | additional | item | last_page_results
                )
            except Exception as e:
                print(f'Format error: {item} - {e}')

        return result

    def handle_separation_error(self, r, separator, result):
        last_key = None
        is_splitted = False

        if '-' in r:
            rr = r.split('-')
            key = rr[0]
            value = '-'.join(rr[1:])
            result[key] = value
            last_key = key
            is_splitted = False

        return result, last_key, is_splitted

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
        ],
        'year': [1354, 2500, 2270-1354, 2640-2500]

    }

    boxes_columns = ['નામ', 'પિતાન નામ', 'પતીનં નામ', 'માતાન નામ', 'ઘરનં']
    columns = ['main_town', 'revenue_division', 'police_station', 'mandal', 'district', 'pin_code', 'part_no', 'polling_station_name', 'polling_station_address', 'ac_name', 'parl_constituency', 'year', 'state', 'accuracy score', 'count', 'id'] + boxes_columns + ['net_electors_male', 'net_electors_female', 'net_electors_third_gender', 'net_electors_total', 'file_name']

    translate_columns = {
        'નામ': 'name',
        'પિતાન નામ': 'father\'s name',
        'પતીનં નામ': 'husband\'s name',
        'ઘરનં': 'house_number',
        #'પતીનં નામ':  'wife\'s name',
        'માતાન નામ': 'mother\'s name',
    }
    contours = {
        'limits_h': (500,800),
        'limits_w': (300,1500),
        'remove_limits': (70, 400)
    }
    
    GJ = Gujarat('gujarat', lang, contours, ignore_last=True, translate_columns=translate_columns, last_page_coordinates=last_page_coordinates, first_page_coordinates=first_page_coordinates, columns=columns, boxes_columns=boxes_columns, rescale=600/500)

    GJ.run()


