import sys
sys.path.append('../')
from parse_unsearchable_rolls.scripts.kerala.main import Kerala

if __name__ == '__main__':
    KR = Kerala('kerala', year='2012', check_updated_counts=True)
    KR.run()


