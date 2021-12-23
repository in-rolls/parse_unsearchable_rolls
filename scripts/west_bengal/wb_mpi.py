#!/usr/bin/env python
# coding: utf-8


import traceback
sys.path.append('../')

import os
import pdf2image
from PIL import Image
import pytesseract
import re
import pandas as pd
import sys
from helper import *
import argparse
import multiprocessing
import time
from datetime import datetime
import shutil
from tempfile import mkstemp
from mpi4py.futures import MPIPoolExecutor

if False:

    script_description = """ wb parsing """

    parser = argparse.ArgumentParser(description=script_description,
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument("data_path", help="data path of the states with append /")
    parser.add_argument("state_name", help="the exact state name of data with /")

    cli_args = parser.parse_args()

    DATA_PATH = cli_args.data_path
    STATE = cli_args.state_name


DATA_PATH = '/share/svasudevan2lab/parse_in_rolls/data/'
STATE = 'wb/'

PARSE_DATA_PAGES = "/share/svasudevan2lab/parse_in_rolls/parseData/images/"+STATE
create_path(PARSE_DATA_PAGES)

PARSE_DATA_BLOCKS = "/share/svasudevan2lab/parse_in_rolls/parseData/blocks/"+STATE
create_path(PARSE_DATA_BLOCKS)

PARSE_DATA_CSVS = "/share/svasudevan2lab/parse_in_rolls/parseData/csvs/"+STATE
create_path(PARSE_DATA_CSVS)

COLUMNS = ["number","id", "elector_name", "father_or_husband_name", "relationship", "house_no", "age", "sex", "ac_name", "parl_constituency", "part_no", "year", "state", "filename", "main_town", "police_station", "mandal", "revenue_division", "district", "pin_code", "polling_station_name", "polling_station_address", "net_electors_male", "net_electors_female", "net_electors_third_gender", "net_electors_total"]

state_pdfs_path = DATA_PATH+STATE
state_pdfs_files = os.listdir(state_pdfs_path)
sort_nicely(state_pdfs_files)


def split_data(data):
    seps = [":","ব্লক","-"]
    
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


def arrange_columns(first_page_list,block_list,filename):
    
    year = 2018
    state = 'wb'
    
    ac_name,parl_constituency,part_no,main_town,police_station,polling_station_name,polling_station_address,revenue_division,mandal,district,pin_code,net_electors_male,net_electors_female,net_electors_third_gender,net_electors_total = first_page_list
    name,rel_name,rel_type,house_no,age,gender,voter_id,number = block_list
    
    final_list = [number,voter_id,name,rel_name,rel_type,house_no,age,gender,ac_name,
                 parl_constituency,part_no,year,state,filename,main_town,police_station,mandal,
                 revenue_division,district,pin_code,polling_station_name,polling_station_address,
                 net_electors_male,net_electors_female,net_electors_third_gender,net_electors_total]
    
    
    return final_list


def get_mandal(a,b,c,d,img,crop_path):
            
    crop_img = crop_section(a,b,c,d,img)

    crop_det_path = crop_path+"det.jpg"
    crop_img.save(crop_det_path)
    crop_img.close()

    text = (pytesseract.image_to_string(crop_det_path, config='--psm 6', lang='ben'))
    text = text.split('\n')
    text = [ i for i in text if i!='' and i!='\x0c']

    return text
    
def get_stats(a,b,c,d,img,crop_path):

    crop_img = crop_section(a,b,c,d,img)

    crop_path = input_images_blocks_path+"page/"
    create_path(crop_path)

    crop_stat_path = crop_path+"stat.jpg"
    crop_img.save(crop_stat_path)
    crop_img.close()

    a_n,b_n,c_n,d_n = extract_4_numbers(crop_stat_path)

    return a_n,b_n,c_n,d_n

def get_police_det(a,b,c,d,img,crop_path):

    crop_img = crop_section(a,b,c,d,img)

    crop_police_path = crop_path+"police.jpg"
    crop_img.save(crop_police_path)
    crop_img.close()

    text = (pytesseract.image_to_string(crop_police_path, config='--psm 6', lang='ben')) #config='--psm 4' config='-c preserve_interword_spaces=1'
    text = text.split('\n')
    text = [ i for i in text if i!='' and i!='\x0c']

    return text

def extract_4_numbers(crop_stat_path):
    
    text = (pytesseract.image_to_string(crop_stat_path, config='--psm 6', lang='eng')) #config='--psm 4' config='-c preserve_interword_spaces=1'

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


def extract_first_page_details(path):
    
    img = Image.open(path)
        
    a,b,c,d = 2557,5205,1237,105  # stats for male and female
    crop_path = input_images_blocks_path+"page/"
    create_path(crop_path)
    
    a_n,b_n,c_n,d_n = get_stats(a,b,c,d,img,crop_path)
    
    if a_n == "" or b_n == "":
        print(a_n,b_n,c_n,d_n)
    
    a,b,c,d = 2520,3172,1386,1140  # mandal block
    main_town,police_station,revenue_division,mandal,district,pin_code = "","","","","",""

    text = get_mandal(a,b,c,d,img,crop_path)
        
    
    if len(text) == 8:
        
        main_town = split_data(text[0])
        police_station = split_data(text[4])
        revenue_division = split_data(text[5])
        mandal = split_data(text[2])
        district = split_data(text[6])
        pin_code = split_data(text[7])
        
 
    a,b,c,d = 3008,280,640,200 # part no
    crop_img = crop_section(a,b,c,d,img)
    
    crop_part_path = crop_path+"part.jpg"
    crop_img.save(crop_part_path)
    crop_img.close()

    text = (pytesseract.image_to_string(crop_part_path, config='--psm 6', lang='ben')) #config='--psm 4' config='-c preserve_interword_spaces=1'
    text = re.findall(r'\d+', text)
    
    if len(text)>0:
        part_no = text[0]
    else:
        part_no = ""
            
        
    a,b,c,d = 280,3610,1850,714 # police name name and address
    
    text = get_police_det(a,b,c,d,img,crop_path)
    
    if len(text) == 6:
        polling_station_name = text[2].strip()
        polling_station_address = text[5].strip()
    elif len(text) >=3:
        polling_station_name = text[2].strip()
        polling_station_address = ''
    else:
        polling_station_name, polling_station_address = "",""
    
        
    a,b,c,d = 266,207,2654,585 # ac name and parl
    crop_img = crop_section(a,b,c,d,img)
    
    crop_ac_path = crop_path+"ac.jpg"
    crop_img.save(crop_ac_path)
    crop_img.close()

    text = (pytesseract.image_to_string(crop_ac_path, config='--psm 6', lang='eng+ben')) #config='--psm 4' config='-c preserve_interword_spaces=1'
    text = text.split('\n')
    text = [ i for i in text if i!='' and i!='\x0c']
    
    ac_name,parl_constituency = '',''
    
        

    if len(text) == 4:
        ac_name = text[1].split(",")
        if len(ac_name)>0:
            ac_name = ac_name[-1].strip()
            
        parl_constituency= text[3].split(",")
        if len(parl_constituency)>0:
            parl_constituency = parl_constituency[-1].strip()

    
    return [ac_name,parl_constituency,part_no,main_town,police_station,polling_station_name,polling_station_address,revenue_division,mandal,district,pin_code,a_n,b_n,c_n,d_n]


def generate_poll_blocks_from_page(page_full_path,page_blocks_path,amend_page):
    
    img = Image.open(page_full_path)

    amend = False
    
    def generate(intial_width,a,b,gap):
        count = 0
        crop_width = 1223
        crop_height = 460

        for col in range(1,11):

            for row in range(1,4):
                c = a+crop_width
                d = b+crop_height
                area = (a, b, c, d)
                cropped_img = img.crop(area)
                count = count+1
                cropped_img.save(page_blocks_path+str(count)+".jpg")
                cropped_img.close()

                a = c

            a = intial_width
            b = b+crop_height+gap
    
    page_type,intial_height = check_page_type(img,amend_page)
    
    if page_type == 1:
        intial_width = 232
        generate(intial_width,intial_width,intial_height,0)

        

def check_page_type(img,amend_page):
    
    return 1,500


def extract_name(name):
    
    row = name.split(":")
    if len(row)!=2:
        return ""
    else:
        return row[1].strip()
    
def extract_id(v_id):
    row = v_id.split(" ")
    if len(row)==2:
        return row[0].strip(), row[-1].strip()
    elif len(row)>2:
        return row[0], row[1]+row[2].strip()
    elif len(row)==1:
        return "",row[-1]
    else:
        return "",""

def extract_house_no(house_no):
    row = house_no.split(":")
    if len(row)==2:
         return row[1].strip()
    else:
        return ""
    
def extract_gender(age_gender):
    
    text = re.findall(r'\d+', age_gender)
    
    if len(text)>0:
        age = text[0]
    else:
        age = ""
        
    row = age_gender.split("লিঙ্গ")
    
    if len(row)>=2:
        gender = row[-1].replace(":","").strip()
        
    else:
        gender =  ""
        
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
    if line.startswith("স্বামীর"):
        rel_type = 'husband'
    elif line.startswith("পিতার"):
        rel_type = 'father'
    else:
        rel_type = "father"
    
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
    age, gender = extract_gender(age_gender)
    number, voter_id = extract_id(v_id)
    
    
    return [name,rel_name,rel_type,house_no,age,gender,voter_id,number]


def run_tesseract(path):
    text = (pytesseract.image_to_string(path, config='--psm 6', lang='eng+ben'))
    params_list = text.split('\n')
    new_params_list = [ i for i in params_list if i!='' and i!='\x0c']

    return new_params_list

def pdf_process(pdf_file_name):

    begin_time = time.time()
    
    print(pdf_file_name, datetime.now().strftime('%Y/%m/%d %H:%M:%S'))

    if not pdf_file_name.endswith(".pdf"):
        return pdf_file_name, 0

    try:
        #create images,blocks and csvs paths for each file
        pdf_file_name_without_ext = pdf_file_name.split('.pdf')[0]
        input_pdf_images_path = PARSE_DATA_PAGES+pdf_file_name_without_ext+"/"
        create_path(input_pdf_images_path)

        input_images_blocks_path = PARSE_DATA_BLOCKS+pdf_file_name_without_ext+"/"
        create_path(input_images_blocks_path)
        
        if os.path.exists(PARSE_DATA_CSVS+pdf_file_name_without_ext+".csv"):
            print(pdf_file_name_without_ext+".csv", "already exists")
            continue
        
        #convert pdf into bunch of images
        try:
            pdf_2_images_list = pdf_to_img(state_pdfs_path+pdf_file_name, input_pdf_images_path,dpi=500)
        except:
            continue
        
        #sort pages for looping
        input_images = os.listdir(input_pdf_images_path)
        sort_nicely(input_images)
        
        #empty intial data
        df = pd.DataFrame(columns = COLUMNS)
        order_problem = []
        
        amend_page = False
        
        #for each page, parse the data
        for page in input_images:
        
            page_full_path = input_pdf_images_path+page
            
            #extract first page content
            if page == '1.jpg':
                first_page_list = extract_first_page_details(page_full_path)
                continue
                

            #ingnore 2nd page and last page
            if page == '2.jpg' or input_images[-1] == page:
                continue
                

            #loop from 3 page onwards
            if page.endswith('.jpg'):
                
                final_invidual_blocks = []
                blocks_path = input_images_blocks_path+"blocks/"
                create_path(blocks_path)

                page_idx = page.split(".jpg")[0] + "/"
                page_blocks_path = blocks_path+page_idx
                create_path(page_blocks_path)
                    
                generate_poll_blocks_from_page(page_full_path,page_blocks_path,amend_page)
                
                
                sorted_blocks = os.listdir(page_blocks_path)
                sort_nicely(sorted_blocks)
                
                for jpg_file in sorted_blocks:
                    
                    if jpg_file.endswith('.jpg') :

                        params_list = run_tesseract(page_blocks_path+jpg_file)

                        if len(params_list) == 5:
                            final_invidual_blocks.append(params_list)
                        else:
                            order_problem.append((page, jpg_file,params_list))
            
            #put the data into dataframe
            for block in final_invidual_blocks:
                
                block_list = extract_details_from_block(block)
                            
                final_list = arrange_columns(first_page_list,block_list,pdf_file_name_without_ext)            
                df_length = len(df)
                df.loc[df_length] = final_list
            
            print("page done : ",page)

        #save the dataframe(pdf) data into csv
        save_to_csv(df,PARSE_DATA_CSVS+pdf_file_name_without_ext+".csv")
        print("CSV saved",pdf_file_name_without_ext)
    
    except Exception as e:
        print('ERROR:', e, pdf_file_name_without_ext)
        traceback.print_exc()
    finally:
        print("Clean up working files...")
        shutil.rmtree(input_pdf_images_path, ignore_errors=True)
        shutil.rmtree(input_images_blocks_path, ignore_errors=True)

    end_time = time.time()

    return pdf_file_name_without_ext, end_time - begin_time


if __name__ == '__main__':

    print('Tesseract Version:', pytesseract.get_tesseract_version())
    print('multiprocessing cpu_count:', multiprocessing.cpu_count())
    print('os cpu_count:', os.cpu_count())
    print('sched_getaffinity:', len(os.sched_getaffinity(0)))

    #a_pool = multiprocessing.Pool(multiprocessing.cpu_count())
    #results = a_pool.map(pdf_process, state_pdfs_files)

    with MPIPoolExecutor() as executor:
        results = executor.map(pdf_process, state_pdfs_files)
        for res in results:
            print(res)

    #combine all state files into one csv
    #combine_all_csvs("wb_final.csv",PARSE_DATA_CSVS)

