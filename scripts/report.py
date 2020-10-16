# Reports for all files

# 1. Verify if each row has the age between MIN and Max
# 2. Verify if each elector_name length
# 3. Verify if each father_or_husband_name length
# 4. Verify if each id length
# 5. Verfy number of male against the net male
# 6. Verfy number of female against the net female
# 7. verify if the total matches with the data
# 8. verify the unique sex values count
# 9. verify the unique relationship values count
# 10.Count the original and amendaments list

import os
import pandas as pd
import sys
import argparse

sys.path.append('../')

script_description = """Generate statewise reports."""

parser = argparse.ArgumentParser(description=script_description,
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("csvs_path", help="csvs path",default='/csvs/')
parser.add_argument("state_name", help="state name",default='haryana')
parser.add_argument("male_key", help="male keyword")
parser.add_argument("female_key", help="female keyword")
parser.add_argument("final_report_csv", help="final report csv",default='report.csv')

cli_args = parser.parse_args()

CSVS_LOC = cli_args.csvs_path
STATE = cli_args.state_name
CSVS_PATH = CSVS_LOC+STATE+"/"

M_KEYWORD = cli_args.male_key
F_KEYWORD = cli_args.female_key
FINAL_CSV = cli_args.final_report_csv

DEFAULT_MIN_AGE = 18
DEFAULT_MAX_AGE = 100
DEFAULT_NAME_MIN_LENGTH = 3
DEFAULT_PIN_MIN_LENGTH = 6
DEFAULT_ID_MIN_LENGTH = 4

COLUMNS = ['file_name','total_records_found','no_of_missing_records','nan_in_number','no_of_males_found','no_of_males_claimed','no_of_females_found','no_of_females_claimed','age_pass_cases','age_fail_cases',
           'elector_name_length_pass_cases','elector_name_length_fail_cases','father_or_husband_name_length_pass_cases','father_or_husband_name_length_fail_cases','id_length_pass_cases','id_length_fail_cases',
          'unique_sex_values','unique_relationship','unique_main_town','unique_mandal','unique_district','unique_pin_code','unique_ac_name','unique_parl_constituency','unique_police_station',
          'unique_revenue_division']

def get_total_records_found(df):
    total_records_found = len(df)
    return total_records_found

def get_no_of_missing_records(df):

    if df['net_electors_total'][0]>= len(df):
        no_of_missing_records = df['net_electors_total'][0] - len(df)
        return no_of_missing_records
    else:
        return 0

def get_nan_in_number(df):
    return df['number'].isna().sum()

def get_no_of_males_found(df,keyword):
    
    temp_df = df[(df['sex']==keyword)]
    return len(temp_df)

def get_no_of_females_found(df,keyword):
    temp_df = df[(df['sex']==keyword)]
    return len(temp_df)

def get_no_of_males_claimed(df):
    if df['net_electors_male'][0]:
        return df['net_electors_male'][0]

def get_no_of_females_claimed(df):
    if df['net_electors_female'][0]:
        return df['net_electors_female'][0]

def get_age_pf_cases(df,total_records):
    temp_df = df[(DEFAULT_MIN_AGE <= df['age']) & (df['age'] <= DEFAULT_MAX_AGE)]

    return len(temp_df), total_records-len(temp_df)

def get_ename_pf_cases(df,total_records):
    temp_df = df[(DEFAULT_NAME_MIN_LENGTH <= df['elector_name'].str.len())]
    return len(temp_df), total_records-len(temp_df)

def get_fhname_pf_cases(df,total_records):
    temp_df = df[(DEFAULT_NAME_MIN_LENGTH <= df['father_or_husband_name'].str.len())]
    return len(temp_df), total_records-len(temp_df)

def get_id_length_pf_cases(df,total_records):
    temp_df = df[(DEFAULT_ID_MIN_LENGTH <= df['id'].str.len())]
    return len(temp_df), total_records-len(temp_df)

def get_amend_original(df):
    data = df['original_or_amendment'].value_counts()

    if len(data)==2:
        return data[0],data[1]
    else:
        return data[0],0

def missing_to_typecast(df,column,default_value,datatype):
    df[column] = df[column].fillna(default_value)

    try:
        df[column] = df[column].astype(datatype)
    except:
        for idx,i in enumerate(df[column]):
            
            i = str(i).replace('.', '')
            try:
                i = int(i)
            except:
                i = 0
            df[column][idx] = i

def get_unique_list(df,column):
    unique_list = df[column].unique()

    return unique_list

def save_to_csv(dataframe, full_filepath):

    if dataframe.empty:
        return
    else :
        dataframe.to_csv(full_filepath,index=False)
        
def generate_report():
    
    stat_df = pd.DataFrame(columns = COLUMNS)
    files = os.listdir(CSVS_PATH)
    
    for file in files:

        if not file.endswith('csv'):
            continue

        df = pd.read_csv(CSVS_PATH+file,low_memory=False)

        missing_to_typecast(df,'age',0,'int')
        missing_to_typecast(df,'net_electors_male',0,'int')
        missing_to_typecast(df,'net_electors_female',0,'int')
        missing_to_typecast(df,'net_electors_total',0,'int')
        
        total_records_found = get_total_records_found(df)
        no_of_missing_records = get_no_of_missing_records(df)
        nan_in_number = get_nan_in_number(df)
        
        no_of_males_found = get_no_of_males_found(df,M_KEYWORD)
        no_of_males_claimed = get_no_of_males_claimed(df)
        no_of_females_found = get_no_of_females_found(df,F_KEYWORD)
        no_of_females_claimed = get_no_of_females_claimed(df)
        
        age_pass_cases,age_fail_cases = get_age_pf_cases(df,total_records_found)
        elector_name_length_pass_cases,elector_name_length_fail_cases = get_ename_pf_cases(df,total_records_found)
        father_or_husband_name_length_pass_cases,father_or_husband_name_length_fail_cases = get_fhname_pf_cases(df,total_records_found)
        id_length_pass_cases,id_length_fail_cases = get_id_length_pf_cases(df,total_records_found)
        unique_sex_values = get_unique_list(df,'sex')
        unique_relationship = get_unique_list(df,'relationship')
        
        final_list = [file,total_records_found,no_of_missing_records,nan_in_number,no_of_males_found,no_of_males_claimed,
                    no_of_females_found,no_of_females_claimed,age_pass_cases,age_fail_cases,elector_name_length_pass_cases,elector_name_length_fail_cases,
                    father_or_husband_name_length_pass_cases,father_or_husband_name_length_fail_cases,
                    id_length_pass_cases,id_length_fail_cases,unique_sex_values,unique_relationship,
                    df['main_town'][0],df['mandal'][0],df['district'][0],df['pin_code'][0],df['ac_name'][0],df['parl_constituency'][0],df['police_station'][0],df['revenue_division'][0]]

        df_length = len(stat_df)
        stat_df.loc[df_length] = final_list

        print("new row has been added ",file)
    
    save_to_csv(stat_df,FINAL_CSV)

if __name__ == "__main__":
    generate_report()
