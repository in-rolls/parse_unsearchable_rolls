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

	script_description = """ jharkhand parsing """

	parser = argparse.ArgumentParser(description=script_description,
									 formatter_class=argparse.ArgumentDefaultsHelpFormatter)

	parser.add_argument("data_path", help="data path of the states with append /")
	parser.add_argument("state_name", help="the exact state name of data with /")

	cli_args = parser.parse_args()

	DATA_PATH = cli_args.data_path
	STATE = cli_args.state_name

DATA_PATH = '/share/svasudevan2lab/parse_in_rolls/data/'
STATE = 'jharkhand/'

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


def parse_lists(ids_list,names_list,last_list):
		
	house_list,number_list = parse_house_no(ids_list)
	name_list,rel_type_list,rel_name_list,gender_list = parse_names_list(names_list)
	age_list,v_id_list = parse_age_vid(last_list)
	
	final_list = []
	
	for name,rel_name,rel_type,house_no,age,gender,voter_id,number in zip(name_list,rel_name_list,rel_type_list,house_list,age_list,gender_list,v_id_list,number_list):
	
		row = [name,rel_name,rel_type,house_no,age,gender,voter_id,number]
		final_list.append(row)
	
	return final_list
	

def parse_age_vid(last_list):
	age_list = []
	v_id_list = []
	
	for data in last_list:
		data = data.split("फोटो")
		age,v_id = "",""

		if len(data)==2:
			data = data[0]
			try:
				data = data.split(" ")
				if len(data)>=2:
					age = data[0]
					v_id = data[1]
			except:
				pass

		age_list.append(age)
		v_id_list.append(v_id)
	
	return age_list,v_id_list

def parse_house_no(ids_list):
	house_list = []
	number_list = []
	for data in ids_list:
		house_no,number = "",""
		
		try:
			data = data.split(" ")
			house_no = data[-1]
			number = data[0]
		except:
			pass
		
		house_list.append(house_no)
		number_list.append(number)
		
	return house_list,number_list

def parse_names_list(names_list):
	
	name_list,rel_type_list,rel_name_list,gender_list = [],[],[],[]

	for data in names_list:

		name,rel_type,rel_name,gender = "","","",""

		rel_keywords = ['पिता','पति','माता']
		rel_r = ['Father','Husband','Mother']

		gender_keywords = ['पुरूष','प्रूष','परूष','महिला']
		gender_r = ['पुरूष','पुरूष','पुरूष','महिला']

		for idx,k in enumerate(rel_keywords):

			extra = data

			if k in data:

				rel_type = rel_r[idx]

				try:
					lines = data.split(k)
					name = lines[0]
					extra = lines[1].replace(k,'')

				except:
					print(data)


				for idx2,g in enumerate(gender_keywords):

					if g in extra:
						gender = gender_r[idx2]

						try:
							lines = extra.split(g)
							rel_name = lines[0]                
						except:
							print(data)

				break
			
		if rel_name=="" or gender == "" or rel_type == "" or name == "":
			print("missing data ",data)
				
		name_list.append(name)
		rel_name_list.append(rel_name)
		rel_type_list.append(rel_type)
		gender_list.append(gender)

	return name_list,rel_type_list,rel_name_list,gender_list


# In[5]:


def arrange_lists(final_list, first_page_list,a,b,c,d,filename,df):
	
	year = 2017
	state = 'jharkhand'
	
	ac_name,parl_constituency,part_no,main_town,police_station,polling_station_name,polling_station_address,revenue_division,mandal,district,pin_code = first_page_list
	
	for row in final_list:
		name,rel_name,rel_type,house_no,age,gender,voter_id,number = row
		
	
		temp_list = [number,voter_id,name,rel_name,rel_type,house_no,age,gender,ac_name,
					 parl_constituency,part_no,year,state,filename,main_town,police_station,mandal,
					 revenue_division,district,pin_code,polling_station_name,polling_station_address,
					 a,b,c,d]
		
		df_length = len(df)
		df.loc[df_length] = temp_list
		
	return df

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


# In[6]:


def crop_ids(page_full_path,page_blocks_path):
	
	img = Image.open(page_full_path)

	a,b,c,d = 375,740,505,4765  # votes
	crop_img = crop_section(a,b,c,d,img)
	crop_img.save(page_blocks_path+"1.jpg")
	crop_img.close()

def crop_names(page_full_path,page_blocks_path):
	
	img = Image.open(page_full_path)

	a,b,c,d = 820,740,1800,4765  # votes
	crop_img = crop_section(a,b,c,d,img)
	crop_img.save(page_blocks_path+"2.jpg")
	crop_img.close()

def crop_last(page_full_path,page_blocks_path):
	
	img = Image.open(page_full_path)

	a,b,c,d = 2580,740,1375,4765  # votes
	crop_img = crop_section(a,b,c,d,img)
	crop_img.save(page_blocks_path+"3.jpg")
	crop_img.close()
	
def crop_voter_images(page_full_path,page_blocks_path):
	
	crop_ids(page_full_path,page_blocks_path)
	crop_names(page_full_path,page_blocks_path)
	crop_last(page_full_path,page_blocks_path)
		


# In[7]:


def extract_first_page_details(path,input_images_blocks_path):
	
	img = Image.open(path)

	crop_path = input_images_blocks_path+"page/"
	create_path(crop_path)
		
	a,b,c,d = 2380,2590,1310,1050  # mandal block
	crop_img = crop_section(a,b,c,d,img)
	
	crop_det_path = crop_path+"det.jpg"
	crop_img.save(crop_det_path)
	crop_img.close()

	text = (pytesseract.image_to_string(crop_det_path, config='--psm 6', lang='eng+hin')) #config='--psm 4' config='-c preserve_interword_spaces=1'
	text = text.split('\n')
	text = [ i for i in text if i!='' and i!='\x0c']
	
	def split_d(text):
		try:
			text = text.split(" ")[1]
		except:
			text = ""
		return text
	
	def split_name(text):
		try:
			text = text.split("नाम")[1]
		except:
			text = ""
		return text
	
	if len(text) == 8:
		
		main_town = split_name(text[0])
		police_station = split_d(text[4])
		revenue_division =  split_d(text[2])
		mandal =  split_d(text[5])
		district =  split_d(text[6])
		pin_code =  split_d(text[7])
	
	else:
		main_town,police_station,revenue_division,mandal,district,pin_code = "","","","","",""
	
	a,b,c,d = 3470,316,438,290 # part no
	crop_img = crop_section(a,b,c,d,img)
	
	crop_part_path = crop_path+"part.jpg"
	crop_img.save(crop_part_path)
	crop_img.close()

	text = (pytesseract.image_to_string(crop_part_path, config='--psm 6', lang='eng+hin')) #config='--psm 4' config='-c preserve_interword_spaces=1'
	text = re.findall(r'\d+', text)
	
	if len(text)>0:
		part_no = text[0]
	else:
		a,b,c,d = 3440,326,438,290 # part no
		crop_img = crop_section(a,b,c,d,img)

		crop_part_path = crop_path+"part.jpg"
		crop_img.save(crop_part_path)

		text = (pytesseract.image_to_string(crop_part_path, config='--psm 6', lang='eng+hin')) #config='--psm 4' config='-c preserve_interword_spaces=1'
		text = re.findall(r'\d+', text)


		if len(text)>0:
			part_no = text[0]
		else:
			part_no = ""
		
	a,b,c,d = 390,3810,2130,635 # police name name and address
	crop_img = crop_section(a,b,c,d,img)
	
	crop_police_path = crop_path+"police.jpg"
	crop_img.save(crop_police_path)
	crop_img.close()
	
	text = (pytesseract.image_to_string(crop_police_path, config='--psm 6', lang='eng+hin')) #config='--psm 4' config='-c preserve_interword_spaces=1'
	text = text.split('\n')
	text = [ i for i in text if i!='' and i!='\x0c']
	
	def split_p1_data(text):

		keywords = ['संख्या व','व','=']
		out = ''
		
		for k in keywords:
			if k in text:
				try:
					out = text.split(k)[1]
					break
				except:
					out = ""
			
					
		return out
	
	def split_p2_data(text):
		
		keywords = ['भवन का','का']
		out = ''
		
		for k in keywords:
			if k in text:
				try:
					out = text.split(k)[1]
					break
				except:
					out = ""
					
		return out
				
	if len(text) >= 3:
		polling_station_name = split_p1_data(text[0])
		polling_station_address = split_p2_data(text[2])
	else:
		polling_station_name, polling_station_address = "",""
		
	
	a,b,c,d = 300,340,2706,555 # ac name and parl
	crop_img = crop_section(a,b,c,d,img)
	
	crop_ac_path = crop_path+"ac.jpg"
	crop_img.save(crop_ac_path)
	crop_img.close()
	
	text = (pytesseract.image_to_string(crop_ac_path, config='--psm 6', lang='eng+hin')) #config='--psm 4' config='-c preserve_interword_spaces=1'
	text = text.split('\n')
	text = [ i for i in text if i!='' and i!='\x0c']
	
	if len(text) >= 4:
		
		ac_name = split_data(text[1])
		parl_constituency = split_data(text[3])

	else:
		a,b,c,d = 300,340,2736,565 # ac name and parl
		crop_img = crop_section(a,b,c,d,img)

		crop_ac_path = crop_path+"ac.jpg"
		crop_img.save(crop_ac_path)
		crop_img.close()

		text = (pytesseract.image_to_string(crop_ac_path, config='--psm 6', lang='eng+hin')) #config='--psm 4' config='-c preserve_interword_spaces=1'
		text = text.split('\n')
		text = [ i for i in text if i!='' and i!='\x0c']
		
		if len(text) >= 4:
		
			ac_name = split_data(text[1])
			parl_constituency = split_data(text[3])

		else:
			ac_name,parl_constituency = "",""
	
	
	return [ac_name,parl_constituency,part_no,main_town,police_station,polling_station_name,polling_station_address,revenue_division,mandal,district,pin_code]


def extract_4_numbers(crop_stat_path):
	
	text = (pytesseract.image_to_string(crop_stat_path, config='--psm 6', lang='eng+hin')) #config='--psm 4' config='-c preserve_interword_spaces=1'

	text = re.findall(r'\d+', text)    
	if len(text)==3:
		if int(text[0]) + int(text[1]) == int(text[2]):
			net_electors_male,net_electors_female,net_electors_third_gender,net_electors_total = text[0],text[1],"0",text[2]
		else:
			net_electors_male,net_electors_female,net_electors_third_gender,net_electors_total = text[0],text[1],"0",text[2]            
	else:
		net_electors_male,net_electors_female,net_electors_third_gender,net_electors_total = "","","",""
	
	return net_electors_male,net_electors_female,net_electors_third_gender,net_electors_total


def extract_last_page_content(path,input_images_blocks_path):
	
	img = Image.open(path)
	crop_path = input_images_blocks_path+"page/"
	create_path(crop_path)
	
	a,b,c,d = 2796, 1010, 1074, 300 # last page 1st
	crop_img = crop_section(a,b,c,d,img)

	crop_last_path = crop_path+"last.jpg"
	crop_img.save(crop_last_path)
	crop_img.close()
	
	a_1,b_1,c_1,d_1 = extract_4_numbers(crop_last_path)
	
	if a_1 == "":
		a,b,c,d = 2796, 1040, 1014, 300 # last page 1st
		crop_img = crop_section(a,b,c,d,img)

		crop_last_path = crop_path+"last.jpg"
		crop_img.save(crop_last_path)
		crop_img.close()

		a_1,b_1,c_1,d_1 = extract_4_numbers(crop_last_path)
		
	return a_1,b_1,c_1,d_1
  



def pdf_process(pdf_file_name):

	begin_time = time.time()
	
	print(pdf_file_name, datetime.now().strftime('%Y/%m/%d %H:%M:%S'))

	if not pdf_file_name.endswith(".PDF"):
		return pdf_file_name, 0

	try:
		#create images,blocks and csvs paths for each file
		pdf_file_name_without_ext = pdf_file_name.split('.PDF')[0]
		input_pdf_images_path = PARSE_DATA_PAGES+pdf_file_name_without_ext+"/"
		create_path(input_pdf_images_path)

		input_images_blocks_path = PARSE_DATA_BLOCKS+pdf_file_name_without_ext+"/"
		create_path(input_images_blocks_path)

		if os.path.exists(PARSE_DATA_CSVS+pdf_file_name_without_ext+".csv"):
			print(pdf_file_name_without_ext+".csv", "already exists")
			return pdf_file_name_without_ext, 0

		#convert pdf into bunch of images
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
		
		last_page = input_images[-1]
		
		if input_images[-1] == '.DS_Store':
			last_page = input_images[-2]
		
		a,b,c,d = extract_last_page_content(input_pdf_images_path+last_page,input_images_blocks_path)
		
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
				
				print("page",page)
				
				final_invidual_blocks = []
				blocks_path = input_images_blocks_path+"blocks/"
				create_path(blocks_path)

				page_idx = page.split(".jpg")[0] + "/"
				page_blocks_path = blocks_path+page_idx
				create_path(page_blocks_path)
				
				crop_voter_images(page_full_path,page_blocks_path)
				
				text = (pytesseract.image_to_string(page_blocks_path+'1.jpg', config='--psm 6', lang='eng+hin')) #config='--psm 4' config='-c preserve_interword_spaces=1'
				
				ids_list = text.split('\n')
				ids_list = [ i for i in ids_list if i!='' and i!='\x0c']
				
				text = (pytesseract.image_to_string(page_blocks_path+'2.jpg', config='--psm 6', lang='hin')) #config='--psm 4' config='-c preserve_interword_spaces=1'
				
				names_list = text.split('\n')
				names_list = [ i for i in names_list if i!='' and i!='\x0c']
				
				text = (pytesseract.image_to_string(page_blocks_path+'3.jpg', config='--psm 6', lang='eng+hin')) #config='--psm 4' config='-c preserve_interword_spaces=1'
				
				last_list = text.split('\n')
				last_list = [ i for i in last_list if i!='' and i!='\x0c']
				
				final_list = parse_lists(ids_list,names_list,last_list)
				
				df = arrange_lists(final_list,first_page_list,a,b,c,d,pdf_file_name_without_ext,df)
				
				
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
