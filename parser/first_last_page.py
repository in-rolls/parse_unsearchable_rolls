import pytesseract
import re
from collections import OrderedDict
import cv2
import numpy as np
import tesserocr
import logging

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(message)s',
                    handlers=[logging.FileHandler("parser/debug.log"),
                              logging.StreamHandler()])

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
            sni = [int(x) if x else 0 for x in sn]
            if sni[0] + sni[1] + sni[2] == sni[3]:
                return sn
        except:
            pass
        
        return None


    def extract_4_numbers(self, cropped):
        # Extract numbers
        cc = self.transform_and_remove_contours(cropped, (40,200))
        text = tesserocr.image_to_text(cc, lang=self.lang, psm=tesserocr.PSM.SPARSE_TEXT) 
        text = re.findall(r'\d+', text)

        #Interpretation
        if len(text)==4:
            if int(text[0]) + int(text[1]) == int(text[2]):
                result = text[0], text[1], "0", text[2]
            elif int(text[0]) + int(text[1]) == int(text[3]):
                result = text[0], text[1], "0", text[3]
            else:
                result = text[0], text[1], text[2], text[3]
        elif len(text) == 3 and int(text[2])>=int(text[1]) and int(text[2])>=int(text[0]):
            result = text[0], text[1], "0", text[2]
        elif len(text) == 2 and int(text[0])*2-100<int(text[1]):
            result = text[0], int(text[1])-int(text[0]), "0", text[1]
        else:
            result = None
        
        return result


    def get_police_data(self, result, cs, im, rescale):
        a, b, c, d = self.rescale_cs(cs) if rescale else cs # police name name and address
        crop_police = self.crop_section(a, b, c, d, im)
        text = (pytesseract.image_to_string(crop_police, config='--psm 6', lang=self.lang)) 

        text = text.split('\n')
        text = [ i for i in text if i!='' and i!='\x0c']
        for k,v in self.P_KEYWORDS.items():
            for i,t in enumerate(text):
                if v in t:
                    try:
                        result[k] = text[i+1]
                        try:
                            text[i+3]
                        except:
                            result[k] = result[k] + ' ' + ' '.join(text[i+2:]) 
                        break
                    except:
                        result[k] = text[i]
        return result

    def get_mandal_data(self, result, cs, im, rescale):
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
        
        return result


    def rescale_cs(self, l):
        return [ x * self.rescale for x in l] 
        
    def extract_first_page_details(self, im):
        coordinates = self.first_page_coordinates
        result = OrderedDict()
        rescale = coordinates.get('rescale', True)
        stats_nums = []

        if cs := coordinates.get('mandal', None):
            result = self.get_mandal_data(result, cs, im, rescale)

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
            stats_nums = self.check_stats_nums(self.extract_4_numbers(crop_stats_nums))

        return result, stats_nums

    def extract_last_page_details(self, im, stats_nums):
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
        if not stats_nums:
            for cs in coordinates:
                c1, c2, c3, c4 = cs
                cropped = self.crop_section(c1, c2, c3, c4, im)
                s_nums = self.extract_4_numbers(cropped)
                try:
                    if (s_nums[0] == '' and s_nums[1] == '') or s_nums[0] == '0':
                        ...
                    else:
                        break
                except:
                    pass

            try:
                stats_nums = self.check_stats_nums(s_nums)
            except:
                pass

        if not stats_nums:
            stats_nums = '', '', '', ''   

        if self.year:
            year = self.year
        elif year_coordinates:
            c1, c2, c3, c4 = year_coordinates
            cropped = self.crop_section(c1, c2, c3, c4, im)
            text = pytesseract.image_to_string(cropped, lang=self.lang, config='--psm 6')
            year = ''.join(re.findall('\d+', text))
        else:
            year = ''

        result.update({
            'net_electors_male': stats_nums[0],
            'net_electors_female': stats_nums[1],
            'net_electors_third_gender': stats_nums[2],
            'net_electors_total': stats_nums[3],
            'year': year
        })
        return result

    def handle_extra_pages(self, pages):
        fp_result, stats_nums = self.extract_first_page_details(pages[0])
        lp_result = self.extract_last_page_details(pages[-1], stats_nums)

        return fp_result, lp_result

    def check_supp_counts(self, page):
        cropped = page.crop((1783, 401, 2443, 750))
        im = self.transform_and_remove_contours(cropped, (40,200))
        text = tesserocr.image_to_text(im, lang=self.lang, psm=tesserocr.PSM.SPARSE_TEXT)
        return re.findall('\d+', text)

    def update_counts(self, page, last_page_results):
        # check if there's additional stats
        p_stats = self.check_supp_counts(page) 
        
        # validate
        if len(p_stats) == 3: 
            try:
                # check correct values
                m = int(p_stats[0])
                f = int(p_stats[1])
                t = int(p_stats[2])

                if m + f == t:
                    #add
                    last_page_results['net_electors_male'] = int(last_page_results['net_electors_male']) + m
                    last_page_results['net_electors_female'] = int(last_page_results['net_electors_female']) + f
                    #last_page_results['net_electors_third_gender'] += 
                    last_page_results['net_electors_total'] = int(last_page_results['net_electors_total']) + t

            except Exception as e:
                logging.debug(f'Adding stats error: {e}')

        return last_page_results

    def mark_supplementary_data(self, page):
        # check if there's additional counts
        v = False
        p_stats = self.check_supp_counts(page) 
        
        # validate
        if len(p_stats) == 3: 
            v = True

        return v