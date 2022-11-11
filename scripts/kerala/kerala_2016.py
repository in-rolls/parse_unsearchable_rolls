import sys
sys.path.append('../')
from parse_unsearchable_rolls.scripts.kerala.main import Kerala


if __name__ == '__main__':
    if len(sys.argv) > 1:
        KR.MAX_WORKERS = 1
        KR.BASE_DATA_PATH = sys.argv[1]    
    KR = Kerala('kerala', year='2016')
    KR.first_page_coordinates = {
        'rescale': False,
        'mandal': [1244, 950, 2341-1244, 1597-950], 
        'part_no': [2154, 290, 2331-2154, 367-290],
        'police': [119, 1682, 1200-119, 2000-1682],
        'ac': [730, 244, 1360-720, 580-244],
        'stats_nums': [1400, 3100, 2356-1400, 3168-3100]
    } 
    KR.run()


