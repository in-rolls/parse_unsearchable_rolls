import sys
sys.path.append('../')
from parse_unsearchable_rolls.scripts.kerala.main import Kerala


if __name__ == '__main__':
    if len(sys.argv) > 1:
        Kerala.MAX_WORKERS = 1
        Kerala.BASE_DATA_PATH = sys.argv[1]    
    KR = Kerala('kerala', year='2011', check_supplementary_data=True)
    KR.columns = ['main_town', 'revenue_division', 'police_station', 'mandal', 'district', 'pin_code', 'part_no', 'polling_station_name', 'polling_station_address', 'ac_name', 'parl_constituency', 'year', 'state', 'number', 'id'] + KR.boxes_columns + ['supplementary_data'] + ['net_electors_male', 'net_electors_female', 'net_electors_third_gender', 'net_electors_total', 'file_name']
    KR.run()


