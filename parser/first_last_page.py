import pytesseract
import re
from collections import OrderedDict

class FirstLastPage:

    def split_data(self, data):
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
            
    def extract_4_numbers(self, crop_stat_path):
        text = (pytesseract.image_to_string(crop_stat_path, config='--psm 6', lang=self.lang)) #config='--psm 4' config='-c preserve_interword_spaces=1'
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

    def extract_detail_section(self, text):
        keywords = ['Village','Ward No','Police','Tehsil','District','Pin']
        found_keywords = ["","","","","",""]
        for idx,keyword in enumerate(keywords):
            for t in text:
                if keyword in t:
                    found_keywords[idx] = self.split_data(t)
                    break
        return found_keywords

    def extract_p_name_add(self, text):
        keywords = ['Name','Address']
        found_keywords = ["",""]
        
        for idx,key in enumerate(keywords):
            for t_idx, t in enumerate(text):
                if key in t:
                    if len(text)>t_idx+1:
                        found_keywords[idx]  = text[t_idx+1]
                        
        return found_keywords

    def extract_last_page_details(self, img):
        result = OrderedDict()
        coordinates = []

        for c in self.last_page_coordinates:
            coordinates.append(
                [x * self.rescale for x in c]
            )
        
        for cs in coordinates:
            c1, c2, c3, c4 = cs
            cropped = self.crop_section(c1,c2,c3,c4,img)
            a, b, c, d = self.extract_4_numbers(cropped)
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
        
    def extract_first_page_details(self, img):
        coordinates = self.first_page_coordinates
        result = OrderedDict()

        if A:= coordinates.get('A', None):
            a,b,c,d = [ x * self.rescale for x in A] # mandal block
            crop_img = self.crop_section(a,b,c,d,img)

            text = (pytesseract.image_to_string(crop_img, config='--psm 6', lang=self.lang)) #config='--psm 4' config='-c preserve_interword_spaces=1'
            text = text.split('\n')
            text = [ i for i in text if i!='' and i!='\x0c']
                
            right_length = True if len(text) == 6 else False
            result.update({
                'main_town': self.split_data(text[0]) if right_length else self.extract_detail_section(text)[0],
                'revenue_division': self.split_data(text[1]) if right_length else self.extract_detail_section(text)[1],
                'police_station': str(self.split_data(text[2])) if right_length else self.extract_detail_section(text)[2],
                'mandal': self.split_data(text[3]) if right_length else self.extract_detail_section(text)[3],
                'district': self.split_data(text[4]) if right_length else self.extract_detail_section(text)[4],
                'pin_code': self.split_data(text[5]) if right_length else self.extract_detail_section(text)[5]
            })
            
        if B:= coordinates.get('B', None):
            a,b,c,d = [ x * self.rescale for x in B]  # part no
            part_crop = self.crop_section(a,b,c,d,img)
            
            text = (pytesseract.image_to_string(part_crop, config='--psm 6', lang=self.lang)) #config='--psm 4' config='-c preserve_interword_spaces=1'
            text = re.findall(r'\d+', text)
            
            right_length = True if len(text)>0 else False 
            result.update({
                'part_no': text[0] if right_length else ''
            })
        

        if C:= coordinates.get('C', None):
            a,b,c,d = [ x * self.rescale for x in C] # police name name and address
            police_crop = self.crop_section(a,b,c,d,img)
            
            text = (pytesseract.image_to_string(police_crop, config='--psm 6', lang=self.lang)) #config='--psm 4' config='-c preserve_interword_spaces=1'
            text = text.split('\n')
            text = [ i for i in text if i!='' and i!='\x0c']
            
            right_length = True if len(text)>0 else False  
            result.update({
                'polling_station_name': text[1] if right_length else self.extract_p_name_add(text)[0],
                'polling_station_address': text[3] if right_length else self.extract_p_name_add(text)[1]  
            })

        if D:= coordinates.get('D', None):
            a,b,c,d = [ x * self.rescale for x in D]# ac name and parl
            ac_crop = self.crop_section(a,b,c,d,img)
            
            text = (pytesseract.image_to_string(ac_crop, config='--psm 6', lang=self.lang)) #config='--psm 4' config='-c preserve_interword_spaces=1'
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


    def handle_extra_pages(self, pages):
        return self.extract_first_page_details(pages[0]), self.extract_last_page_details(pages[-1])
        #return super().handle_extra_pages(pages)
