import sys
sys.path.append('../')
from parse_unsearchable_rolls.parser.parser import Parser
from parse_unsearchable_rolls.parser.helpers import crop_section, show
import pytesseract
import re

from collections import OrderedDict

# methods specific to this state
 
def split_data(data):
    seps = [":",">","-","."]
    
    for s in seps:
        if s in data:
            break
        
    data = data.split(s)
    data = [ i for i in data if i.strip()!='']
    if len(data)>1:
        data = data[1].strip()
        return data
    else:
        data = ""
        
def extract_4_numbers(crop_stat_path):
    text = (pytesseract.image_to_string(crop_stat_path, config='--psm 6', lang='eng')) #config='--psm 4' config='-c preserve_interword_spaces=1'
    text = re.findall(r'\d+', text)    
    if len(text)==4:
        if int(text[0]) + int(text[1]) == int(text[2]):
            a,b,c,d = text[0],text[1],"0",text[2]
        elif int(text[0]) + int(text[1]) == int(text[3]):
            a,b,c,d = text[0],text[1],"0",text[3]
        else:
            a,b,c,d = text[0],text[1],text[2],text[3]
    elif len(text) == 3 and int(text[2])>=int(text[1]) and int(text[2])>=int(text[0]):
        a,b,c,d = text[0],text[1],"0",text[2]
    elif len(text) == 2 and int(text[0])*2-100<int(text[1]):
        a,b,c,d = text[0],int(text[1])-int(text[0]),"0",text[1]
    else:
        a,b,c,d = "","","",""
    
    return a,b,c,d

def extract_detail_section(text):
    keywords = ['Village','Ward No','Police','Tehsil','District','Pin']
    found_keywords = ["","","","","",""]
    for idx,keyword in enumerate(keywords):
        for t in text:
            if keyword in t:
                found_keywords[idx] = split_data(t)
                break
    return found_keywords

def extract_p_name_add(text):
    keywords = ['Name','Address']
    found_keywords = ["",""]
    
    for idx,key in enumerate(keywords):
        for t_idx, t in enumerate(text):
            if key in t:
                if len(text)>t_idx+1:
                    found_keywords[idx]  = text[t_idx+1]
                    
    return found_keywords

def extract_last_page_details(img):
    result = OrderedDict()
    coordinates = [
        [x * RESCALE for x in [2504, 988, 1200,95]],
        [x * RESCALE for x in [2494, 2486, 1200, 95]],
        [x * RESCALE for x in [2494, 2516, 1200, 95]]
    ]
    
    for cs in coordinates:
        c1, c2, c3, c4 = cs
        cropped = crop_section(c1,c2,c3,c4,img)
        a, b, c, d = extract_4_numbers(cropped)
        if (a == '' and b == '') or a == '0':
            ...
        else:
            break
    
    result.update({
        'net_electors_male': a,
        'net_electors_female': b,
        'net_electors_third_gender': c,
        'net_electors_total': d
    })
    return result
    
def extract_first_page_details(img):
    result = OrderedDict()

    a,b,c,d = [ x * RESCALE for x in [1770, 1900, 1480, 545]] # mandal block
    crop_img = crop_section(a,b,c,d,img)

    text = (pytesseract.image_to_string(crop_img, config='--psm 6', lang='eng+hin')) #config='--psm 4' config='-c preserve_interword_spaces=1'
    text = text.split('\n')
    text = [ i for i in text if i!='' and i!='\x0c']
        
    right_length = True if len(text) == 6 else False
    result.update({
        'main_town': split_data(text[0]) if right_length else extract_detail_section(text)[0],
        'revenue_division': split_data(text[1]) if right_length else extract_detail_section(text)[1],
        'police_station': str(split_data(text[2])) if right_length else extract_detail_section(text)[2],
        'mandal': split_data(text[3]) if right_length else extract_detail_section(text)[3],
        'district': split_data(text[4]) if right_length else extract_detail_section(text)[4],
        'pin_code': split_data(text[5]) if right_length else extract_detail_section(text)[5]
    })
        
    a,b,c,d = [ x * RESCALE for x in [3165, 295, 620, 190]]  # part no
    part_crop = crop_section(a,b,c,d,img)
    
    text = (pytesseract.image_to_string(part_crop, config='--psm 6', lang='eng+hin')) #config='--psm 4' config='-c preserve_interword_spaces=1'
    text = re.findall(r'\d+', text)
    
    right_length = True if len(text)>0 else False 
    result.update({
        'part_no': text[0] if right_length else ''
    })
        
    a,b,c,d = [ x * RESCALE for x in [185, 3330, 2000, 672]] # police name name and address
    police_crop = crop_section(a,b,c,d,img)
    
    text = (pytesseract.image_to_string(police_crop, config='--psm 6', lang='eng+hin')) #config='--psm 4' config='-c preserve_interword_spaces=1'
    text = text.split('\n')
    text = [ i for i in text if i!='' and i!='\x0c']
    
    right_length = True if len(text)>0 else False  
    result.update({
        'polling_station_name': text[1] if right_length else extract_p_name_add(text)[0],
        'polling_station_address': text[3] if right_length else extract_p_name_add(text)[1]  
    })

    a,b,c,d = [ x * RESCALE for x in [180, 290, 2806, 405]]# ac name and parl
    ac_crop = crop_section(a,b,c,d,img)
    
    text = (pytesseract.image_to_string(ac_crop, config='--psm 6', lang='eng')) #config='--psm 4' config='-c preserve_interword_spaces=1'
    text = text.split('\n')
    text = [ i for i in text if i!='' and i!='\x0c']
    
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

        result.update({
                'ac_name': ac_name,
                'parl_constituency': parl_constituency
            })
    
    return result #[ac_name,parl_constituency,part_no,main_town,police_station,polling_station_name,polling_station_address,revenue_division,mandal,district,pin_code]


class Gujarat(Parser):
    def handle_extra_pages(self, pages):
        return extract_first_page_details(pages[0]), extract_last_page_details(pages[-1])
        #return super().handle_extra_pages(pages)

    def get_header(self, page):
        result = OrderedDict()
        a,b,c,d = 0,0,4700,335
        header = crop_section(a,b,c,d,page)
    
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


    def handle_separation(self, r, result):
        low_r = r.lower().strip()
        found = re.findall('^age', low_r) 
        if found:
            result['age'] = ''.join(re.findall('age[^\d]*(\d*)', r.lower()))
            result['sex'] = ''.join(re.findall('sex[^\w]*(\w*)', r.lower()))

            last_key = 'sex'
            is_splitted = True
       
        # redundant
#        elif 'house' in low_r:
#            key = 'house number'
#            value = ''.join(re.findall('house number.*?([\d\w].*)', low_r))
#            result[key] = value
#            last_key = key
#            is_splitted = True
        
        # else:
        #     ### check
        #     last_key = None
        #     is_splitted = False

        return result, last_key, is_splitted

     
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
    lang = 'eng+guj'
    RESCALE = 600/500 # from 500 dpi to 600
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

    columns = []

    Gujarat('gujarat', lang).run()#, columns = columns, checks = checks).run()
