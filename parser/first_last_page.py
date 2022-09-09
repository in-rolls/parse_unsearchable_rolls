import pytesseract
import re
from collections import OrderedDict

class FirstLastPage:
    FIRST_LAST_SEPARATORS = [":-", ":", ">", "-", "."]

    def split_data(self, data):
        seps = self.FIRST_LAST_SEPARATORS
        for s in seps:
            if s in data:
                break
            
        data = data.split(s)
        return [ x.strip() for x in data ]
        
            
    def extract_4_numbers(self, cropped):

        text = (pytesseract.image_to_string(cropped, config='--oem 3 --psm 6 outputbase digits', lang=self.lang)) #config='--psm 4' config='-c preserve_interword_spaces=1'
        
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

        for cs in coordinates:
            c1, c2, c3, c4 = cs
            cropped = self.crop_section(c1, c2, c3, c4, im)
            a, b, c, d = self.extract_4_numbers(cropped)
            if (a == '' and b == '') or a == '0':
                ...
            else:
                break
        
        if year_coordinates:
            c1, c2, c3, c4 = year_coordinates
            cropped = self.crop_section(c1, c2, c3, c4, im)
            text = pytesseract.image_to_string(cropped, lang=self.lang, config='--psm 6')
            year = ''.join(re.findall('\d+', text))
        else:
            year = ''

        result.update({
            'net_electors_male': a,
            'net_electors_female': b,
            'net_electors_third_gender': c,
            'net_electors_total': d,
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

        return result


    def handle_extra_pages(self, pages):
        return self.extract_first_page_details(pages[0]), self.extract_last_page_details(pages[-1])
        #return super().handle_extra_pages(pages)
