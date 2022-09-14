import pytesseract
import re
from collections import OrderedDict
import cv2
import numpy as np

class FirstLastPage:
    FIRST_LAST_SEPARATORS = [":-", ":", ">", "-", "."]

    def split_data(self, data):
        seps = self.FIRST_LAST_SEPARATORS
        for s in seps:
            if s in data:
                break
            
        data = data.split(s)
        return [ x.strip() for x in data ]
        
    def check_stats_nums(self, sn):
        # check if stats nums count are accurate
        try:
            sni = [int(x) for x in sn]
            if sni[0] + sni[1] + sni[2] == sni[3]:
                return sn
        except:
            pass
        
        return None


    def extract_4_numbers(self, cropped):
        # Extract numbers
        text = (pytesseract.image_to_string(cropped, config='--psm 6', lang=self.lang)) #config='--psm 4' config='-c preserve_interword_spaces=1'
        text = re.findall(r'\d+', text)

        if text:
            nums = [int(x) for x in text]
            if nums[-1] != sum(nums[:-1]):
                # Remove box lines
                im = np.array(cropped) 
                im = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
                contours = self.get_countours(im)
                cropped_p = self.remove_contours(im, contours, (70,150))

                # Retry
                text = (pytesseract.image_to_string(cropped_p, config='--psm 6 --oem 3 -c tessedit_char_whitelist=0123456789', lang=self.lang)) 
                text = re.findall(r'\d+', text)

        #Interpretation
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
        
        return (a, b, c, d)


    def get_police_data(self, result, cs, im, rescale):
            a, b, c, d = self.rescale_cs(cs) if rescale else cs # police name name and address
            crop_police = self.crop_section(a, b, c, d, im)
            text = (pytesseract.image_to_string(crop_police, config='--psm 6', lang=self.lang)) 

            text = text.split('\n')
            text = [ i for i in text if i!='' and i!='\x0c']
            for k,v in self.P_KEYWORDS.items():
                for i,t in enumerate(text):
                    if v in t:
                        result[k] = text[i+1]
                        try:
                            text[i+3]
                        except:
                            result[k] = result[k] + ' ' + ' '.join(text[i+2:]) 
                        break
            return result

    def extract_last_page_details(self, im):
        result = OrderedDict()
        a, b, c, d = '','','',''
        coordinates = []
        rescale = self.last_page_coordinates.get('rescale', False)
        input_coordinates = self.last_page_coordinates.get('coordinates', [])
        year_coordinates = self.last_page_coordinates.get('year', [])

        if rescale:
            for c in input_coordinates:
                coordinates.append(
                    [x * self.rescale for x in c]
                )
        else:
            coordinates = input_coordinates

        # if not stats nums check for the second time
        if not self.stats_nums:
            for cs in coordinates:
                c1, c2, c3, c4 = cs
                cropped = self.crop_section(c1, c2, c3, c4, im)
                stat_nums = self.extract_4_numbers(cropped)
                if (stat_nums[0] == '' and stat_nums[1] == '') or stat_nums[0] == '0':
                    ...
                else:
                    break

            self.stats_nums = self.check_stats_nums(stat_nums)

        if not self.stats_nums:
            self.stats_nums = '', '', '', ''   

        if year_coordinates:
            c1, c2, c3, c4 = year_coordinates
            cropped = self.crop_section(c1, c2, c3, c4, im)
            text = pytesseract.image_to_string(cropped, lang=self.lang, config='--psm 6')
            year = ''.join(re.findall('\d+', text))
        else:
            year = ''

        result.update({
            'net_electors_male': self.stats_nums[0],
            'net_electors_female': self.stats_nums[1],
            'net_electors_third_gender': self.stats_nums[2],
            'net_electors_total': self.stats_nums[3],
            'year': year
        })
        return result

    def rescale_cs(self, l):
        return [ x * self.rescale for x in l] 
        
    def extract_first_page_details(self, im):
        coordinates = self.first_page_coordinates
        result = OrderedDict()
        rescale = coordinates.get('rescale', True)

        if cs := coordinates.get('mandal', None):
            a,b,c,d = self.rescale_cs(cs) if rescale else cs # mandal block

            crop_mandal = self.crop_section(a,b,c,d,im)
            text = (pytesseract.image_to_string(crop_mandal, config='--psm 6', lang=self.lang)) 
            text = text.split('\n')
            text = [ i for i in text if i!='' and i!='\x0c']

            for t in text:
                k, v = self.split_data(t)
                for kk, vv in self.MANDAL_KEYWORDS.items(): 
                    if kk in k:
                        result[vv] = v
                        break

        if cs := coordinates.get('part_no', None):
            a, b, c, d = self.rescale_cs(cs) if rescale else cs # part no
            crop_part = self.crop_section(a, b, c, d, im)
            text = (pytesseract.image_to_string(crop_part, config='--psm 6', lang=self.lang))
            text = re.findall(r'\d+', text)
            
            result['part_no'] = ''.join(text)

        if cs := coordinates.get('police', None):
            result = self.get_police_data(result, cs, im, rescale)

        if cs := coordinates.get('ac', None):
            a, b, c, d = self.rescale_cs(cs) if rescale else cs # ac name and parl
            crop_ac = self.crop_section(a, b, c, d, im)
            text = (pytesseract.image_to_string(crop_ac, config='--psm 6', lang=self.lang)) 
            text = text.split('\n')
            text = [ i for i in text if i!='' and i!='\x0c']
            
            result.update(self.get_ac(text))

        if cs := coordinates.get('stats_nums', None):
            a, b, c, d = self.rescale_cs(cs) if rescale else cs # ac name and parl
            crop_stats_nums = self.crop_section(a, b, c, d, im)
            self.stats_nums = self.check_stats_nums(self.extract_4_numbers(crop_stats_nums))

        return result

    def handle_extra_pages(self, pages):
        return self.extract_first_page_details(pages[0]), self.extract_last_page_details(pages[-1])
        #return super().handle_extra_pages(pages)
