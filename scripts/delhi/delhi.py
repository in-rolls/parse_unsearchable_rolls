#!/usr/bin/env python
# coding: utf-8

import sys
sys.path.append('../')

import os
import pdf2image
from PIL import Image
import pytesseract
import difflib
import re
import pandas as pd

from helper import *
import argparse
import multiprocessing
import time

# python delhi.py '../../data/' 'delhi/'

script_description = """ Delhi parsing """

parser = argparse.ArgumentParser(description=script_description,
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)

parser.add_argument("data_path", help="data path of the states with append /")
parser.add_argument("state_name", help="the exact state name of data with /")

cli_args = parser.parse_args()

DATA_PATH = cli_args.data_path
STATE = cli_args.state_name

def create_path(path):
	if not os.path.exists(path):
		os.makedirs(path)

PARSE_DATA_PAGES = "../../parseData/images/"+STATE
create_path(PARSE_DATA_PAGES)

PARSE_DATA_BLOCKS = "../../parseData/blocks/"+STATE
create_path(PARSE_DATA_BLOCKS)

PARSE_DATA_CSVS = "../../parseData/csvs/"+STATE
create_path(PARSE_DATA_CSVS)

COLUMNS = ["id", "elector_name", "father_or_husband_name", "relationship", "house_no", "age", "sex", "ac_name", "parl_constituency", "part_no", "year", "state", "filename", "main_town", "police_station", "mandal", "revenue_division", "district", "pin_code", "polling_station_name", "polling_station_address", "net_electors_male", "net_electors_female", "net_electors_third_gender", "net_electors_total"]

state_pdfs_path = DATA_PATH+STATE
state_pdfs_files = os.listdir(state_pdfs_path)


def generate_poll_blocks_from_page(page_full_path,page_blocks_path,amend_page):
	
	img = Image.open(page_full_path)

	amend = False
	
	def generate(intial_width,a,b,gap):
		count = 0
		crop_width = 1260
		crop_height = 480

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
		intial_width = 150
		generate(intial_width,intial_width,intial_height,5)
		amend_page = False
	else:
		intial_width = 150
		generate(intial_width,intial_width,intial_height,40)
		amend_page = True
		
	return amend_page

def check_page_type(img,amend_page):
	
	if amend_page:
		return 2,295
	
	a,b,c,d = 130, 280,800,155  # amend page check
	crop_img = crop_section(a,b,c,d,img)

	crop_temp_path = "temp.jpg"
	crop_img.save(crop_temp_path)
	
	text = (pytesseract.image_to_string(crop_temp_path, config='--psm 6', lang='eng+hin')) #config='--psm 4' config='-c preserve_interword_spaces=1'
	text = text.split('\n')
	text = [ i for i in text if i!='' and i!='\x0c']
			   
			
	return 1,270

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
		
def arrange_columns(first_page_list,block_list,last_page_list,filename):
	
	year = 2020
	state = 'delhi'
	
	net_electors_male,net_electors_female,net_electors_third_gender,net_electors_total = last_page_list
	ac_name,parl_constituency,part_no,main_town,police_station,polling_station_name,polling_station_address,revenue_division,mandal,district,pin_code = first_page_list

	v_id,name,rel_name,rel_type,house_no,age,sex = block_list
	
	final_list = [v_id,name,rel_name,rel_type,house_no,age,sex,ac_name,
				 parl_constituency,part_no,year,state,filename,main_town,police_station,mandal,
				 revenue_division,district,pin_code,polling_station_name,polling_station_address,
				 net_electors_male,net_electors_female,net_electors_third_gender,net_electors_total]

	return final_list

def extract_details_from_block(new_params_list):
	
	seps = [":","-","."]
	
	v_id,name,house_no,age,sex,rel_name,rel_type = '','','','','','',''

	if len(new_params_list[0])>6:

		row = new_params_list[0].split(" ")
		v_id = row[-1]
	elif "Name" not in new_params_list[1]:
		if len(new_params_list[1])>6:
			row = new_params_list[1].split(" ")
			v_id = row[-1]
	
		

	for param in new_params_list:

		if 'Name' in param:
			
			for s in seps:
				if s in param:
					break
				
			row = param.split(s)
			if len(row)!=2:
				name =  ""
			else:
				name = row[1].strip()
			break

	for param in new_params_list:

		if 'House' in param:
			row = param.split(":")

			if len(row)!=2:
				house_no =  ""
			else:
				row = row[1].strip().split(" ")

				if len(row)>=1:
					house_no = row[0].strip()
			break

	for param in new_params_list:

		if 'Age' in param:

			row = param.split(":")

			if len(row)<2:
				age =  ""
			else:
				age = re.findall(r'\d+', row[1].strip())
				if len(age)>0:
					age =  age[0]
				else:
					age = ""
			break

	for param in new_params_list:

		if 'Sex' in param:

			if "FEMALE" in param:
				sex = 'FEMALE'
			elif "MALE" in param:
				sex = "MALE"
			else:
				sex = ''
			break


	found = False
	for param in new_params_list:

		if found:
			if "House" not in param:
				rel_name = rel_name + " "+param
			break

		if 'Father' in param:
			
			for s in seps:
				if s in param:
					break
				
			row = param.split(s)
			if len(row)!=2:
				rel_name,rel_type =  "",'father'
			else:
				rel_name,rel_type = row[1].strip(),'father'

			found = True
			continue


		if 'Husband' in param:

			for s in seps:
				if s in param:
					break
				
			row = param.split(s)
			if len(row)!=2:
				rel_name,rel_type =  "",'husband'
			else:
				rel_name,rel_type = row[1].strip(),'husband'
			found = True
			continue

		if 'Mother' in param:

			for s in seps:
				if s in param:
					break
				
			row = param.split(s)
			if len(row)!=2:
				rel_name,rel_type =  "",'mother'
			else:
				rel_name,rel_type = row[1].strip(),'mother'

			found = True
			continue
	return v_id,name,rel_name,rel_type,house_no,age,sex

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

def extract_last_page_details(path):
	
	img = Image.open(path)
	crop_path = input_images_blocks_path+"page/"
	create_path(crop_path)
	
	a,b,c,d = 2504, 988, 1200,95  # last page 1st
	crop_img = crop_section(a,b,c,d,img)

	crop_last_path = crop_path+"last.jpg"
	crop_img.save(crop_last_path)
	
	a_1,b_1,c_1,d_1 = extract_4_numbers(crop_last_path)    

	crop_path = input_images_blocks_path+"page/"
	create_path(crop_path)
	
	a,b,c,d = 2494, 2486, 1200, 95 # last page 1st
	crop_img = crop_section(a,b,c,d,img)

	crop_last_path = crop_path+"last.jpg"
	crop_img.save(crop_last_path)
	
	a_n,b_n,c_n,d_n = extract_4_numbers(crop_last_path)
	
	if (a_n == '' and b_n == '') or a_n == "0":
		a,b,c,d = 2494, 2516, 1200, 95 # last page 1st
		crop_img = crop_section(a,b,c,d,img)

		crop_last_path = crop_path+"last.jpg"
		crop_img.save(crop_last_path)
		
		a_n,b_n,c_n,d_n = extract_4_numbers(crop_last_path)
	
	return a_n,b_n,c_n,d_n
	
def extract_first_page_details(path):

	img = Image.open(path)
	crop_path = input_images_blocks_path+"page/"
	create_path(crop_path)
	
	a,b,c,d = 1770,1900,1480,545  # mandal block
	crop_img = crop_section(a,b,c,d,img)
	
	crop_det_path = crop_path+"det.jpg"
	crop_img.save(crop_det_path)

	text = (pytesseract.image_to_string(crop_det_path, config='--psm 6', lang='eng+hin')) #config='--psm 4' config='-c preserve_interword_spaces=1'
	text = text.split('\n')
	text = [ i for i in text if i!='' and i!='\x0c']
		
	if len(text) == 6:
		main_town,revenue_division,police_station,mandal,district,pin_code = split_data(text[0]),split_data(text[1]),str(split_data(text[2])),split_data(text[3]),split_data(text[4]),split_data(text[5]),
	else:
		main_town,revenue_division,police_station,mandal,district,pin_code = extract_detail_section(text)
		
	a,b,c,d = 3165,295,620,190 # part no
	crop_img = crop_section(a,b,c,d,img)
	
	crop_part_path = crop_path+"part.jpg"
	crop_img.save(crop_part_path)

	text = (pytesseract.image_to_string(crop_part_path, config='--psm 6', lang='eng+hin')) #config='--psm 4' config='-c preserve_interword_spaces=1'
	text = re.findall(r'\d+', text)
	
	if len(text)>0:
		part_no = text[0]
	else:
		part_no = ""
		
	a,b,c,d = 185,3330,2000,672 # police name name and address
	crop_img = crop_section(a,b,c,d,img)
	
	crop_police_path = crop_path+"police.jpg"
	crop_img.save(crop_police_path)

	text = (pytesseract.image_to_string(crop_police_path, config='--psm 6', lang='eng+hin')) #config='--psm 4' config='-c preserve_interword_spaces=1'
	text = text.split('\n')
	text = [ i for i in text if i!='' and i!='\x0c']
	
	if len(text) == 4:
		polling_station_name, polling_station_address = text[1],text[3]
	else:
		polling_station_name, polling_station_address = extract_p_name_add(text) 
					
	
	a,b,c,d = 180,290,2806,405 # ac name and parl
	crop_img = crop_section(a,b,c,d,img)
	
	crop_ac_path = crop_path+"ac.jpg"
	crop_img.save(crop_ac_path)
	
	ac_name, parl_constituency = '',''

	text = (pytesseract.image_to_string(crop_ac_path, config='--psm 6', lang='eng')) #config='--psm 4' config='-c preserve_interword_spaces=1'
	text = text.split('\n')
	text = [ i for i in text if i!='' and i!='\x0c']
	
	
	if len(text)>=3:
	
		for t in text:
			if "located" in t:
				
				for s in [':','-','>']:
					if s in t:
						break
					   
				row = t.split(s)
				if len(row)>=2:
					parl_constituency = row[-1].strip()
				else:
					parl_constituency = ""
				break

		found= False
		for t in text:
			if found:
				if "Parliamentary" not in t:
					ac_name = ac_name + " "+t
				break

			if "Assembly" in t:
				row = t.split(":")
				if len(row)>=2:
					ac_name = row[-1].strip()
				else:
					ac_name = ""

				found = True
	
	return [ac_name,parl_constituency,part_no,main_town,police_station,polling_station_name,polling_station_address,revenue_division,mandal,district,pin_code]

def run_tesseract(path):
	text = (pytesseract.image_to_string(path, config='--psm 6', lang='eng'))
	params_list = text.split('\n')
	new_params_list = [ i for i in params_list if i!='' and i!='\x0c']

	return new_params_list

	
if __name__ == '__main__':

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

	for pdf_file_name in state_pdfs_files:
	# for pdf_file_name in ['U05A64P66.pdf']:

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

		if input_images[-1]=='.DS_Store': 
			last_page_list = extract_last_page_details(input_pdf_images_path+input_images[-2])
		else:
			last_page_list = extract_last_page_details(input_pdf_images_path+input_images[-1])

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

				print(page)

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
					final_invidual_blocks.append(res)

			#put the data into dataframe
			for block in final_invidual_blocks:
				if len(block)<5:
					order_problem.append(block)
					continue

				block_list = extract_details_from_block(block)
				final_list = arrange_columns(first_page_list,block_list,last_page_list,pdf_file_name_without_ext)

				df_length = len(df)
				df.loc[df_length] = final_list

		save_to_csv(df,PARSE_DATA_CSVS+pdf_file_name_without_ext+".csv")
		print("CSV saved",pdf_file_name_without_ext)
	
	#combine all state files into one csv
	combine_all_csvs("delhi_final.csv",PARSE_DATA_CSVS)