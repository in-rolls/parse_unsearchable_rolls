#!/usr/bin/env python
# coding: utf-8

import sys
sys.path.append('../')

import os
import pdf2image
from PIL import Image
import pytesseract
import re
import pandas as pd

from helper import *

import argparse
import multiprocessing
import time

# python karnataka.py '../../data/' 'karnataka/'

script_description = """ Karnataka parsing """

parser = argparse.ArgumentParser(description=script_description,
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)

parser.add_argument("data_path", help="data path of the states with append /")
parser.add_argument("state_name", help="the exact state name of data with /")

cli_args = parser.parse_args()

DATA_PATH = cli_args.data_path
STATE = cli_args.state_name

PARSE_DATA_PAGES = "../../parseData/images/"+STATE
create_path(PARSE_DATA_PAGES)

PARSE_DATA_BLOCKS = "../../parseData/blocks/"+STATE
create_path(PARSE_DATA_BLOCKS)

PARSE_DATA_CSVS = "../../parseData/csvs/"+STATE
create_path(PARSE_DATA_CSVS)

COLUMNS = ["number","id", "elector_name", "father_or_husband_name", "relationship", "house_no", "age", "sex", "ac_name", "parl_constituency", "part_no", "year", "state", "filename", "main_town", "police_station", "mandal", "revenue_division", "district", "pin_code", "polling_station_name", "polling_station_address", "net_electors_male", "net_electors_female", "net_electors_third_gender", "net_electors_total","original_or_amendment"]

state_pdfs_path = DATA_PATH+STATE
state_pdfs_files = os.listdir(state_pdfs_path)


def extract_first_page_details(path):
    
    img = Image.open(path)
        
    a,b,c,d = 940,5210,2820,180  # stats for male and female
    crop_img = crop_section(a,b,c,d,img)

    crop_path = input_images_blocks_path+"page/"
    create_path(crop_path)
    
    crop_stat_path = crop_path+"stat.jpg"
    crop_img.save(crop_stat_path)
    
    a_n,b_n,c_n,d_n = extract_4_numbers(crop_stat_path)
        
    if a_n == "":
        a,b,c,d = 940,5100,2820,180  # stats for male and female
        crop_img = crop_section(a,b,c,d,img)

        crop_path = input_images_blocks_path+"page/"
        create_path(crop_path)

        crop_stat_path = crop_path+"stat.jpg"
        crop_img.save(crop_stat_path)
    
        a_n,b_n,c_n,d_n = extract_4_numbers(crop_stat_path)
    
    a,b,c,d = 2380,2776,1360,1208  # mandal block
    crop_img = crop_section(a,b,c,d,img)
    
    crop_det_path = crop_path+"det.jpg"
    crop_img.save(crop_det_path)
    
    text = (pytesseract.image_to_string(crop_det_path, config='--psm 6', lang='eng+kan')) #config='--psm 4' config='-c preserve_interword_spaces=1'

    text = text.split('\n')

    text = [ i for i in text if i!='' and i!='\x0c']
    
    keywords = ['ಗ್ರಾಮ','ಪಟ್ಟಣ','ಠಾಣೆ','ಸಂಖ್ಯೆ','ತಾಲ್ಲೂಕು','ಜಿಲ್ಲೆ','ಕೋಡ್']

    ref_keywords = ['','','','','','','']

    for idx,k in enumerate(keywords):
        for t in text:

            if k in t:
                t = t.split(k)
                try:
                    t = t[1]
                    ref_keywords[idx] = t
                except:
                    text = ""
                    ref_keywords[idx] = t
                break

    police_station,revenue_division,mandal,district,pin_code = ref_keywords[2:]
    main_town = ''
    
    if ref_keywords[0] != '':
        main_town = ref_keywords[0]

    if ref_keywords[1] != '':
        main_town = ref_keywords[1]

    pin_code = pin_code.replace('\u200c','')

    a,b,c,d = 3136,640,751,250 # part no
    crop_img = crop_section(a,b,c,d,img)
    
    crop_part_path = crop_path+"part.jpg"
    crop_img.save(crop_part_path)

    text = (pytesseract.image_to_string(crop_part_path, config='--psm 6', lang='eng+hin')) #config='--psm 4' config='-c preserve_interword_spaces=1'
    text = re.findall(r'\d+', text)
    
    if len(text)>0:
        part_no = text[-1]
    else:
        part_no = ""
    
    a,b,c,d = 127,4024,2270,765 # police name name and address
    crop_img = crop_section(a,b,c,d,img)
    
    crop_police_path = crop_path+"police.jpg"
    crop_img.save(crop_police_path)

    text = (pytesseract.image_to_string(crop_police_path, config='--psm 6', lang='kan')) #config='--psm 4' config='-c preserve_interword_spaces=1'
    text = text.split('\n')
    text = [ i for i in text if i!='' and i!='\x0c']
    
    keywords = ['ಹೆಸರು','ವಿಳಾಸ']

    ref_keywords = ['','']
    
    for idx,k in enumerate(keywords):
        
        for idx2, t in enumerate(text):

            if k in t:
                try:
                    ref_keywords[idx] = text[idx2+1]
                    
                    if 'ವಿಳಾಸ' in ref_keywords[idx]:
                        ref_keywords[idx] = ''
                        
                except:
                    ref_keywords[idx] = ''
                break

    
    polling_station_name, polling_station_address = ref_keywords
    
    
    a,b,c,d = 127,640,3543,608 # ac name and parl
    crop_img = crop_section(a,b,c,d,img)
    
    crop_ac_path = crop_path+"ac.jpg"
    crop_img.save(crop_ac_path)
    
    text = (pytesseract.image_to_string(crop_ac_path, config='--psm 6', lang='eng+kan')) #config='--psm 4' config='-c preserve_interword_spaces=1'
    text = text.split('\n')
    text = [ i for i in text if i!='' and i!='\x0c']
    
    def split_ac(data):
        seps = [":",";"]

        for s in seps:
            if s in data:
                break

        data = data.split(s)
        data = [ i for i in data if i.strip()!='']
        
        if len(data)>1:
            
            data = data[1].split('ಭಾಗದ')[0]
            return data
        else:
            data = ""
            return data

    
    if len(text) == 4:
        ac_name = split_ac(text[0]) + text[1]
        parl_constituency = text[3]
        
    elif len(text) == 5:
        ac_name = split_ac(text[0]) + text[1]
        parl_constituency = text[3]
            
    else:
        ac_name, parl_constituency = "",""
        
    
    return [ac_name,parl_constituency,part_no,main_town,police_station,polling_station_name,polling_station_address,revenue_division,mandal,district,pin_code,a_n,b_n,c_n,d_n]

def generate_poll_blocks_from_page(page_full_path,page_blocks_path,amend_page):
    
    img = Image.open(page_full_path)

    amend = False
    
    def generate(intial_width,a,b,gap):
        count = 0
        crop_width = 1250
        crop_height = 495

        for col in range(1,11):

            for row in range(1,4):
                c = a+crop_width
                d = b+crop_height
                area = (a, b, c, d)
                cropped_img = img.crop(area)
                count = count+1
                cropped_img.save(page_blocks_path+str(count)+".jpg")

                a = c

            a = intial_width
            b = b+crop_height+gap
    
    page_type,intial_height = check_page_type(img,amend_page)
    
    if page_type == 1:
        intial_width = 130
        generate(intial_width,intial_width,intial_height,6)
        amend_page = False
    else:
        intial_width = 130
        generate(intial_width,intial_width,intial_height,40)
        amend_page = True
        
    return amend_page

def check_page_type(img,amend_page):
    
    return 1,333

    if amend_page:
        return 2,295
    
    return 1,270

def extract_name(name):
    
    row = name.split(":")
    if len(row)!=2:
        return ""
    else:
        return row[1].strip()
    
def extract_vid(v_id):
    row = v_id.split(" ")
    
    if len(row) == 1:
        return "",row[0]
    elif len(row)==2:
        number = re.findall(r'\d+', row[0].strip())
        if len(number)>0:
            return number[0],row[1]
        else:
            return "",row[1]
    
    elif len(row)>2:
        
        number = re.findall(r'\d+', row[0].strip())
        if len(number)>0:
            return number[0],row[1]+" "+row[2]
        else:
            return "",row[1]+" "+row[2]  
    else:
        return "",""

def extract_house_no(house_no):
    row = house_no.split(":")
    if len(row)==2:
        house_no = re.findall(r'\d+', row[1].strip())
        if len(house_no)>0:
            return house_no[0]
        else:
            return ""
    else:
        house_no = re.findall(r'\d+', row[0].strip())
        if len(house_no)>0:
            return house_no[0]
        else:
            return ""
    
def extract_age_gender(age_gender):
    row = age_gender.split(":")
    
    if len(row)!=3:
        return "",""
    else:    
        age = re.findall(r'\d+', row[1].strip())
        if len(age)>0:
            age =  age[0]
        else:
            age = ""
        
        if 'ಗಂಡು' in row[2].strip():
            gender = 'Male'
        elif 'ಹೆ' in row[2].strip():
            gender = 'Female'
        else:
            gender =''

    return age, gender

def extract_rel_name(rel_name):
    row = rel_name.split(":")
    if len(row)!=2:
        
        row = rel_name.split(";")
        if len(row)!=2:
            return "",""
        else:
            rel_type = extract_rel_type(row[0].strip())
            return row[1].strip(),rel_type
    else:
        rel_type = extract_rel_type(row[0].strip())
        
        return row[1].strip(),rel_type
    
def extract_rel_type(rel_type):
    line = rel_type
    if line.startswith("ತಂದೆಯ") :
        rel_type = 'father'
        
    elif line.startswith("ಗಂಡನ"):
        rel_type = 'husband'
        
    elif line.startswith("ತಾಯಿ") :
        rel_type = 'mother'
    else:
        rel_type = ""
    
    return rel_type 

def extract_details_from_block(block):
    
    v_id = block[0]
    name = block[1]
    rel_name = block[2]
    house_no = block[3]
    age_gender = block[4]
    
    name = extract_name(name)
    rel_name,rel_type = extract_rel_name(rel_name)
    house_no = extract_house_no(house_no)
    age, gender = extract_age_gender(age_gender)
    number,voter_id = extract_vid(v_id)

    return [name,rel_name,rel_type,house_no,age,gender,voter_id,number]

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
        return data
            
def extract_4_numbers(crop_stat_path):
    
    text = (pytesseract.image_to_string(crop_stat_path, config='--psm 6', lang='eng+hin')) #config='--psm 4' config='-c preserve_interword_spaces=1'

    text = re.findall(r'\d+', text)    
    if len(text)==4:
        if int(text[0]) + int(text[1]) == int(text[2]):
            net_electors_male,net_electors_female,net_electors_third_gender,net_electors_total = text[0],text[1],"0",text[2]
        elif int(text[0]) + int(text[1]) == int(text[3]):
            net_electors_male,net_electors_female,net_electors_third_gender,net_electors_total = text[0],text[1],"0",text[3]
        else:
            net_electors_male,net_electors_female,net_electors_third_gender,net_electors_total = text[0],text[1],text[2],text[3]
    elif len(text) == 3 and int(text[2])>=int(text[1]) and int(text[2])>=int(text[0]):
        net_electors_male,net_electors_female,net_electors_third_gender,net_electors_total = text[0],text[1],"0",text[2]
    elif len(text) == 2 and int(text[0])*2-100<int(text[1]):
        net_electors_male,net_electors_female,net_electors_third_gender,net_electors_total = text[0],int(text[1])-int(text[0]),"0",text[1]
    else:
        net_electors_male,net_electors_female,net_electors_third_gender,net_electors_total = "","","",""
    
    return net_electors_male,net_electors_female,net_electors_third_gender,net_electors_total

def arrange_columns(first_page_list,block_list,filename):
    
    year = 2017
    state = 'karnataka'
    
    ac_name,parl_constituency,part_no,main_town,police_station,polling_station_name,polling_station_address,revenue_division,mandal,district,pin_code,net_electors_male,net_electors_female,net_electors_third_gender,net_electors_total = first_page_list
    
    name,rel_name,rel_type,house_no,age,gender,voter_id,number = block_list
    
    final_list = [number,voter_id,name,rel_name,rel_type,house_no,age,gender,ac_name,
                 parl_constituency,part_no,year,state,filename,main_town,police_station,mandal,
                 revenue_division,district,pin_code,polling_station_name,polling_station_address,
                 net_electors_male,net_electors_female,net_electors_third_gender,net_electors_total]

    return final_list

def run_tesseract(path):
    text = (pytesseract.image_to_string(path, config='--psm 6', lang='eng+kan'))
    params_list = text.split('\n')
    new_params_list = [ i for i in params_list if i!='' and i!='\x0c']

    return new_params_list

if __name__ == '__main__':

    # block = generate the images from pdfs for all files 
    temp_pdf_img_path = []
    temp_pdf_img_outputs_path = []

    for pdf_file_name in state_pdfs_files:

        if not pdf_file_name.endswith(".pdf"):
            continue

        pdf_file_name_without_ext = pdf_file_name.split('.pdf')[0]
        input_pdf_images_path = PARSE_DATA_PAGES+pdf_file_name_without_ext+"/"
        create_path(input_pdf_images_path)

        temp_pdf_img_path.append(state_pdfs_path+pdf_file_name)

        temp_pdf_img_outputs_path.append(input_pdf_images_path)

    a_pool = multiprocessing.Pool()
    a_pool.starmap(pdf_to_img, zip(temp_pdf_img_path,temp_pdf_img_outputs_path))
    # end block

    # block = parse every pdf 
    for pdf_file_name in state_pdfs_files:

        print(pdf_file_name)

        if not pdf_file_name.endswith(".pdf"):
            continue

        #create images,blocks and csvs paths for each file
        pdf_file_name_without_ext = pdf_file_name.split('.pdf')[0]
        input_pdf_images_path = PARSE_DATA_PAGES+pdf_file_name_without_ext+"/"
        create_path(input_pdf_images_path)

        input_images_blocks_path = PARSE_DATA_BLOCKS+pdf_file_name_without_ext+"/"
        create_path(input_images_blocks_path)

        #sort pages for looping
        input_images = os.listdir(input_pdf_images_path)
        sort_nicely(input_images)

        #empty intial data
        df = pd.DataFrame(columns = COLUMNS)
        order_problem = []

        amend_page = False

        for page in input_images:
    
            page_full_path = input_pdf_images_path+page
            
            #extract first page content
            if page == '1.jpg':
                first_page_list = extract_first_page_details(page_full_path)
                continue

            #ingnore 2nd page and last page
            if page == '2.jpg' or input_images[-1] == page:
                continue
            
            if os.path.exists(PARSE_DATA_CSVS+pdf_file_name_without_ext+".csv"):
                print(pdf_file_name_without_ext+".csv", "already exists")
                break
                
            #loop from 3 page onwards
            if page.endswith('.jpg'):
                
                final_invidual_blocks = []
                blocks_path = input_images_blocks_path+"blocks/"
                create_path(blocks_path)

                page_idx = page.split(".jpg")[0] + "/"
                page_blocks_path = blocks_path+page_idx
                create_path(page_blocks_path)
                    
                amend_page = generate_poll_blocks_from_page(page_full_path,page_blocks_path,amend_page)

                if amend_page:
                    page_type = 'amendment'
                else:
                    page_type = 'original'
                    
                sorted_blocks = os.listdir(page_blocks_path)
                sort_nicely(sorted_blocks)

                temp_array = []
                for i in sorted_blocks:
                    temp_array.append(page_blocks_path+i)

                a_pool = multiprocessing.Pool()
                result = a_pool.map(run_tesseract, temp_array)
                
                for res in result:
                    if len(res) !=5:
                        pass
                    else:
                        final_invidual_blocks.append(res)
        
            #put the data into dataframe
            for block in final_invidual_blocks:
                block_list = extract_details_from_block(block)
                            
                final_list = arrange_columns(first_page_list,block_list,pdf_file_name_without_ext)
                final_list.append(page_type)
                
                df_length = len(df)
                df.loc[df_length] = final_list
            
        save_to_csv(df,PARSE_DATA_CSVS+pdf_file_name_without_ext+".csv")
        print("CSV saved",pdf_file_name_without_ext)
    #end block

    #combine all state files into one csv
    combine_all_csvs("karnataka_final.csv",PARSE_DATA_CSVS)



