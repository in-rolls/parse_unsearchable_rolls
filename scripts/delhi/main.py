import sys
sys.path.append('../')
from parse_unsearchable_rolls.parser.parser import Parser
import pytesseract
import re

from collections import OrderedDict

 
class Delhi(Parser):
    MANDAL_KEYWORDS = {
        'Village': 'main_town',
        'Ward No': 'revenue_division',
        'Police': 'police_station',
        'Tehsil': 'mandal',
        'District': 'district',
        'Pin': 'pin_code'
    }
    P_KEYWORDS = {
        'polling_station_name': 'Name',
        'polling_station_address': 'Address'
        }


    def handle_extra_pages(self, pages):
        return self.extract_first_page_details(pages[0]), self.extract_last_page_details(pages[-1])
        #return super().handle_extra_pages(pages)

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

    def handle_custom_split_not_found(self, r, separator, result):
        last_key = None
        is_splitted = False

        if '-' in r:
            rr = r.split('-')
            key = rr[0]
            value = '-'.join(rr[1:])
            result[key] = value
            last_key = key
            is_splitted = False #??? True

        return result, last_key, is_splitted

    def handle_separation(self, r, result):
        last_key = None
        is_splitted = False
        age = self.handle[0]
        sex = self.handle[1]

        low_r = r.lower().strip()
        found = re.findall('^' + age, low_r) 
        if found:
            result[age] = ''.join(re.findall(age + '[^\d]*(\d*)', r.lower()))
            # cleaning female/male field
            result[sex] = ''.join(re.findall(sex + '[^\w]*([male|female]*)', r.lower()))

            last_key = sex
            is_splitted = True
       
        return result, last_key, is_splitted

    def get_ac(self, text):
        ac_name = ''
        parl_constituency = ''
        if len(text)>=3:
            for t in text:
                if "located" in t:
                    for s in [':','-','>']:
                        if s in t:
                            break
                        
                    row = t.split(s)
                    if len(row)>=2:
                        parl_constituency = row[-1].strip()

                    break

            found = False
            for t in text:
                if found:
                    if "Parliamentary" not in t:
                        ac_name = ac_name + " "+t
                    break

                if "Assembly" in t:
                    row = t.split(":")
                    if len(row)>=2:
                        ac_name = row[-1].strip()

                    found = True

            return {
                    'ac_name': ac_name,
                    'parl_constituency': parl_constituency
                }
     
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
    lang = 'eng'
    rescale = 600/500 # from 500 dpi to 600
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

    columns = ['main_town', 'revenue_division', 'police_station', 'mandal', 'district', 'pin_code', 'part_no', 'polling_station_name', 'polling_station_address', 'ac_name', 'parl_constituency', 'year', 'state', 'assambly_constituency_name', 'assambly_constituency_number', 'section name', 'section number', 'part number', 'accuracy score', 'count', 'id', 'name', 'father\'s name', 'husband\'s name', 'mother\'s name', 'house number', 'age', 'sex', 'net_electors_male', 'net_electors_female', 'net_electors_third_gender', 'net_electors_total', 'file_name']

    contours = ((500,800), (300,1500), (60, 400))
    first_page_coordinates = {
        'mandal': [1770, 1900, 1480, 545],
        'part_no': [3165, 295, 620, 190],
        'police': [185, 3330, 1900, 572],
        'ac': [180, 290, 2806, 405],
        }
    
    last_page_coordinates = {
        'rescale': True,
        'coordinates':[
        [2504, 988, 1200,95],
        [2494, 2486, 1200, 95],
        [2494, 2516, 1200, 95]
        ]
    }

    DL = Delhi('delhi', lang, last_page_coordinates = last_page_coordinates, first_page_coordinates = first_page_coordinates, contours = contours, rescale = rescale, columns = columns, checks = checks, handle=['age', 'sex'], ommit = ['Photo is', 'Available'])

    DL.run(3)