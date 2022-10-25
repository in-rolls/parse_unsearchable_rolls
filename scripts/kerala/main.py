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
    FIRST_PAGES = 2
    LAST_PAGE = None

    lang = 'mal+eng'
    rescale = 300/500
    first_page_coordinates = {
        'rescale': False,
        'mandal': [1244, 950, 2341-1244, 1597-950], 
        'part_no': [2154, 290, 2331-2154, 367-290],
        'police': [119, 1682, 1200-119, 2000-1682],
        'ac': [730, 244, 1360-720, 580-244],
        'stats_nums': [1400, 3000, 2400-1400, 3200-3000]
    } 
    boxes_columns = ['പേര്', 'അച്ഛന്റെ പേര്', 'ഭര്‍ത്താവിന്റെ പേര്', 'വീട്ടുനമ്പര്', 'അമ്മയുടെ പേര്', 'വീട്ടുപേര്', 'വയസ്സ്', '(സ്ത്രീ /പു)'] 
    translate_columns = {
        'പേര്': 'elector_name',
        'അച്ഛന്റെ പേര്': 'father_or_husband_name',
        'ഭര്‍ത്താവിന്റെ പേര്': 'husband',
        'വീട്ടുനമ്പര്': 'house_number',
        'അമ്മയുടെ പേര്': 'mother_name',
        'വീട്ടുപേര്': 'household_name',
        'വയസ്സ്':'age',
        '(സ്ത്രീ /പു)':'sex'
    }
    contours = {
        'limits_h': (240,330),
        'limits_w': (730,900),
        'remove_limits': (70/2, 400/2)
    }

    def check_data(self, item):
        # check for correct data

        number = item.get('number', '')
        try:
            assert ''.join(re.findall('[\w\d]', number)) == number
            assert bool(re.match('\d+', number))
        except:
            item['number'] = self.unreadable

        id_ = item.get('id', '')
        try:
            assert ''.join(re.findall('[A-Za-z\d/]', id_)) == id_
            assert bool(re.match('[A-Za-z]+', id_))
            assert len(id_) > 8
        except:
            item['id'] = self.unreadable

        age = item.get('വയസ്സ്', '')
        if age:
            try:
                assert bool(re.match('\d+', age))
            except:
                item['വയസ്സ്'] = self.unreadable

        # Global checks
        keys = ['പേര്', 'അച്ഛന്റെ പേര്', 'ഭര്‍ത്താവിന്റെ പേര്', 'അമ്മയുടെ പേര്', 'വീട്ടുപേര്']
        for k in keys:
            gl = item.get(k, '')
            if gl:
                try:
                    assert bool(re.match('\w+', gl))
                    assert not bool(re.match('[\d\W]', gl))
                except:
                    item[k] = self.unreadable

        return item
        

    def replace_u2(self, s):
        return s.replace('\u200d', '-').replace('\u200c', ',').strip().strip(',')

    def get_mandal_data(self, result, cs, im, rescale):
        a,b,c,d = self.rescale_cs(cs) if rescale else cs # mandal block

        crop_mandal = self.crop_section(a,b,c,d,im)
        text = (pytesseract.image_to_string(crop_mandal, config='--psm 6', lang=self.lang)) 
        text = text.split('\n')
        text = [self.replace_u2(_) for _ in text]

        try:
            result['main_town'] = text[1].split(':')[-1].strip().strip(',')
        except:
            pass

        try:
            result['revenue_division'] = text[3].split(':')[-1].strip().strip(',').replace('|', '1')
        except:
            pass

        try:
            mandal = text[4].split(':')[-1].strip().strip(',')
            mandal = re.sub('[A-Z]', '', mandal)
            mandal = re.sub('[0-9]', '', mandal)
            result['mandal'] = mandal
        except:
            pass

        try:
            result['district'] = text[5].split(':')[-1].strip().strip(',')
        except:
            pass

        return result


    def get_police_data(self, result, cs, im, rescale):
        #a, b, c, d = self.rescale_cs(cs) if rescale else cs # police name name and address
        a, b, c, d = cs
        crop_police = self.crop_section(a, b, c, d, im)
        text = (pytesseract.image_to_string(crop_police, config='--psm 6', lang=self.lang)) 
        text = text.split('\n')

        try:
            result['polling_station_name'] = self.replace_u2(text[1])
            result['polling_station_address'] = self.replace_u2(text[2])
        except:
            pass

        return result

    def get_ac(self, text):
        try: 
            ac_name = self.replace_u2(text[0])
        except:
            ac_name = ''
        
        try: 
            parl_constituency =  self.replace_u2(text[1])
        except:
            parl_constituency = ''

        return {
            'ac_name':ac_name,
            'parl_constituency': parl_constituency
        }

    def known_exceptions(self, result, r, raw):
        is_splitted = False

        sex_key = '(സ്ത്രീ /പു)'
        age_key = 'വയസ്സ്'
        
        if sex_key in r or age_key in r:
            try:
                values = r.split('\u200c')[-1].strip().split(' ')
                if len(values) > 1:
                    result[sex_key] = self.male_or_female(values[0])
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
        elif 'പൂ' == r:
            return self.MALE 
        else:
            return self.unreadable

if __name__ == '__main__':
    KR = Kerala('kerala', year='2014', check_updated_counts=True) #detect_columns = ['\u200c', '\u200d'])
    KR.run()



