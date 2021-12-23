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


if False:

	script_description = """ tripura parsing """

	parser = argparse.ArgumentParser(description=script_description,
									 formatter_class=argparse.ArgumentDefaultsHelpFormatter)

	parser.add_argument("data_path", help="data path of the states with append /")
	parser.add_argument("state_name", help="the exact state name of data with /")

	cli_args = parser.parse_args()

	DATA_PATH = cli_args.data_path
	STATE = cli_args.state_name

DATA_PATH = '/share/svasudevan2lab/parse_in_rolls/data/'
STATE = 'tripura/'

PARSE_DATA_PAGES = "/share/svasudevan2lab/parse_in_rolls/parseData/images/"+STATE
create_path(PARSE_DATA_PAGES)

PARSE_DATA_BLOCKS = "/share/svasudevan2lab/parse_in_rolls/parseData/blocks/"+STATE
create_path(PARSE_DATA_BLOCKS)

PARSE_DATA_CSVS = "/share/svasudevan2lab/parse_in_rolls/parseData/csvs/"+STATE
create_path(PARSE_DATA_CSVS)

COLUMNS = ["number","id", "elector_name", "father_or_husband_name", "relationship", "house_no", "age", "sex", "ac_name", "parl_constituency", "part_no", "year", "state", "filename", "main_town", "police_station", "mandal", "revenue_division", "district", "pin_code", "polling_station_name", "polling_station_address", "net_electors_male", "net_electors_female", "net_electors_third_gender", "net_electors_total"]

state_pdfs_path = DATA_PATH+STATE
state_pdfs_files = os.listdir(state_pdfs_path)



def split_data(data):
	seps = [":",".",","," "]
	
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


# In[40]:


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

def extract_first_page_details(path,input_images_blocks_path):
	
	img = Image.open(path)
		
	a,b,c,d = 1512,5094,2076,131  # stats for male and female
	crop_img = crop_section(a,b,c,d,img)

	crop_path = input_images_blocks_path+"page/"
	create_path(crop_path)
	
	crop_stat_path = crop_path+"stat.jpg"
	crop_img.save(crop_stat_path)
	crop_img.close()
	
	a_n,b_n,c_n,d_n = extract_4_numbers(crop_stat_path)
		
	
	a,b,c,d = 2515,1875,1227,1631  # mandal block
	crop_img = crop_section(a,b,c,d,img)
	
	crop_det_path = crop_path+"det.jpg"
	crop_img.save(crop_det_path)
	crop_img.close()

	text = (pytesseract.image_to_string(crop_det_path, config='--psm 6', lang='eng+ben')) #config='--psm 4' config='-c preserve_interword_spaces=1'
	text = text.split('\n')
	text = [ i for i in text if i!='' and i!='\x0c']
	
	main_town,police_station,revenue_division,mandal,district,pin_code = "","","","","",""
	
	if len(text) == 6:
		
		main_town = split_data(text[0])
		police_station = split_data(text[2])
		revenue_division = split_data(text[3])
		mandal = split_data(text[1])
		district = split_data(text[4])
		pin_code = split_data(text[5])
	
	elif len(text) == 5:
		
		main_town = split_data(text[0])
		police_station = split_data(text[2])
		revenue_division = split_data(text[3])
		mandal = split_data(text[1])
		district = ''
		pin_code = split_data(text[4])
		
	elif len(text) == 7:
		
		main_town = split_data(text[0])
		police_station = split_data(text[3])
		revenue_division = split_data(text[4])
		mandal = split_data(text[2])
		district = split_data(text[5])
		pin_code = split_data(text[6])
		
 
	a,b,c,d = 3021,330,604,212 # part no
	crop_img = crop_section(a,b,c,d,img)
	
	crop_part_path = crop_path+"part.jpg"
	crop_img.save(crop_part_path)

	text = (pytesseract.image_to_string(crop_part_path, config='--psm 6', lang='eng+ben')) #config='--psm 4' config='-c preserve_interword_spaces=1'
	text = re.findall(r'\d+', text)
	
	if len(text)>0:
		part_no = text[0]
	else:
		part_no = ""
			
		
	a,b,c,d = 328,3874,1850,714 # police name name and address
	crop_img = crop_section(a,b,c,d,img)
	
	crop_police_path = crop_path+"police.jpg"
	crop_img.save(crop_police_path)
	crop_img.close()
	
	text = (pytesseract.image_to_string(crop_police_path, config='--psm 6', lang='eng+ben')) #config='--psm 4' config='-c preserve_interword_spaces=1'
	text = text.split('\n')
	text = [ i for i in text if i!='' and i!='\x0c']
	
	if len(text) == 4:
		polling_station_name = text[1].strip()
		polling_station_address = text[3].strip()
	elif len(text) == 5:
		polling_station_name = text[1].strip()
		polling_station_address = text[3]+" "+text[4]
	else:
		polling_station_name, polling_station_address = "",""
	
		
	a,b,c,d = 275,300,2250,564 # ac name and parl
	crop_img = crop_section(a,b,c,d,img)
	
	crop_ac_path = crop_path+"ac.jpg"
	crop_img.save(crop_ac_path)
	crop_img.close()
	
	text = (pytesseract.image_to_string(crop_ac_path, config='--psm 6', lang='eng+ben')) #config='--psm 4' config='-c preserve_interword_spaces=1'
	text = text.split('\n')
	text = [ i for i in text if i!='' and i!='\x0c']
	
	ac_name,parl_constituency = '',''

	if len(text) == 4:
		
		try:
			seps = [":"]

			for s in seps:
				if s in text[0]:
					break
			text[1] = text[1].replace("-:",'')
			ac_name = text[1].split(s)[1]
		except:
			ac_name = ''
		
		
		try:
			seps = [":"]

			for s in seps:
				if s in text[1]:
					break
			parl_constituency = text[3].split(s)[1]
		except:
			parl_constituency = ''
		
	
	return [ac_name,parl_constituency,part_no,main_town,police_station,polling_station_name,polling_station_address,revenue_division,mandal,district,pin_code,a_n,b_n,c_n,d_n]


# In[41]:


def generate_poll_blocks_from_page(page_full_path,page_blocks_path,amend_page):
	
	img = Image.open(page_full_path)

	amend = False
	
	def generate(intial_width,a,b,gap):
		count = 0
		crop_width = 1220
		crop_height = 480

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
		intial_width = 120
		generate(intial_width,intial_width,intial_height,5)

		

def check_page_type(img,amend_page):
	
	return 1,495

	
		
def step2_order(params):
	
	if len(params) == 6:
		new_params_list = []
		
		new_params_list.append(params[0] + " " + params[1])
	   
		for i in params[2:]:
			new_params_list.append(i)
			
		return new_params_list

	return params


# In[50]:


def getAG(new_params_list):
	if len(new_params_list)>=5:
		return new_params_list[-2],new_params_list[-1]
	else:
		return "",""
def getN(new_params_list):
	if len(new_params_list)>0 and len(new_params_list[0])<=2:
		return new_params_list[0]
	else:
		return ""
	
def getRel(new_params_list):
	
	if len(new_params_list) == 10:
		return new_params_list[4]
	try:
		value = int(new_params_list[0])
		return new_params_list[3]
	except:
		if len(new_params_list)>5 :
			return new_params_list[2]
	
	return ""


# In[51]:


def split_data_n(data, seps):
	
	for s in seps:
		
		if s in data:
			break
	
	data = data.split(s)

	if len(data)>1:
		data = data[-1].strip()
		return data
	else:
		data = ""
		return data

def extract_name(name):
	
	row = name.split(":")
	if len(row)!=2:
		return ""
	else:
		return row[1].strip()
	
def extract_id(id):
	row = id.split(" ")
	if len(row)>0:
		return row[-1].strip()

	else:
		return "",""

def extract_house_no(house_no):
	row = house_no.split(":")
	if len(row)==2:
		 return row[1].strip()
	else:
		return ""
	
def extract_gender(gender):
	row = gender.split(":")
	
	if len(row)==2:
		
		if 'পুং' in row[1]:
			return "Male"
		if 'স্ত্রী' in row[1]:
			return "Female"
		else:
			return "Male"
		
	else:
		return ""


def extract_rel_name(rel_name):
	seps = [":",";","পিতাঃ","পিতা"]
	
	rel = split_data_n(rel_name,seps)        
	rel_type = extract_rel_type(rel_name)
		
	return rel,rel_type
	
def extract_rel_type(rel_type):
	line = rel_type
	if line.startswith("স্বামী"):
		rel_type = 'husband'
	elif line.startswith("পিতা"):
		rel_type = 'father'
	else:
		rel_type = ""
	
	return rel_type 


def extract_details_from_block(block):
		
	id = block[0]
	name = block[1]
	rel_name = block[2]
	house_no = block[3]
	age = block[4]
	gender = block[5]
	number = block[6]
	
	name = extract_name(name)
	rel_name,rel_type = extract_rel_name(rel_name)
	house_no = extract_house_no(house_no)
	gender = extract_gender(gender)
	voter_id = extract_id(id)
	
	
	return [name,rel_name,rel_type,house_no,age,gender,voter_id,number]


# In[52]:


def arrange_columns(first_page_list,block_list,filename):
	
	year = 2018
	state = 'tripura'
	
	ac_name,parl_constituency,part_no,main_town,police_station,polling_station_name,polling_station_address,revenue_division,mandal,district,pin_code,net_electors_male,net_electors_female,net_electors_third_gender,net_electors_total = first_page_list
	name,rel_name,rel_type,house_no,age,gender,voter_id,number = block_list
	
	final_list = [number,voter_id,name,rel_name,rel_type,house_no,age,gender,ac_name,
				 parl_constituency,part_no,year,state,filename,main_town,police_station,mandal,
				 revenue_division,district,pin_code,polling_station_name,polling_station_address,
				 net_electors_male,net_electors_female,net_electors_third_gender,net_electors_total]
	
	
	return final_list



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
			return pdf_file_name_without_ext, 0
		
		
		try:
			pdf_2_images_list = pdf_to_img(state_pdfs_path+pdf_file_name, input_pdf_images_path,dpi=500)
		except:
			print(pdf_file_name_without_ext+".csv", "problem generating images from this pdf, must be empty or corrupted")
			return pdf_file_name_without_ext, 0

		
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
				first_page_list = extract_first_page_details(page_full_path,input_images_blocks_path)
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

						text = (pytesseract.image_to_string(page_blocks_path+jpg_file, config='--psm 6', lang='eng+ben')) #config='--psm 4' config='-c preserve_interword_spaces=1'
						params_list = text.split('\n')
						params_list = [ i for i in params_list if i!='' and i!='\x0c']
						temp_list = params_list.copy()
						
						text = (pytesseract.image_to_string(page_blocks_path+jpg_file, config='--psm 11', lang='eng+ben')) #config='--psm 4' config='-c preserve_interword_spaces=1'
						new_params_list = text.split('\n')
						new_params_list = [ i for i in new_params_list if i!='' and i!='\x0c']
						
						
						if len(temp_list)==4:
							a,g = getAG(new_params_list)
							
							params_list.append(a)
							params_list.append(g)
							
							n = getN(new_params_list)
							params_list.append(n)

							
						elif len(temp_list) == 3:
							rel = getRel(new_params_list)
							a,g = getAG(new_params_list)
							temp = params_list[2]
							params_list[2] = rel
							params_list.append(temp)
							params_list.append(a)
							params_list.append(g)
							
							n = getN(new_params_list)
							params_list.append(n)
							
						if len(params_list) == 7:
							final_invidual_blocks.append(params_list)
						else:
							order_problem.append((page, jpg_file,params_list))
			
			#put the data into dataframe
			for block in final_invidual_blocks:
				
				block_list = extract_details_from_block(block)
				name,rel_name,rel_type,house_no,age,gender,voter_id,number = block_list
				
				if name == "":
					continue
				
				final_list = arrange_columns(first_page_list,block_list,pdf_file_name_without_ext)            
				df_length = len(df)
				df.loc[df_length] = final_list
			
			print("page done : ",page)
			   
		#save the dataframe(pdf) data into csv
		save_to_csv(df,PARSE_DATA_CSVS+pdf_file_name_without_ext+".csv")
		print("CSV saved")

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


