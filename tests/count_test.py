import os
# import sys
# sys.path.append('../')
# from parse_unsearchable_rolls.parser.helpers import Helpers

import pandas as pd

class Tests():
    BASE_DATA_PATH = 'data/'
    year = ''

    def main(self, path):
        results = [os.path.join(path, f) for f in os.listdir(path)]
        results = list(filter(lambda x: x.endswith('.csv'), results))

        for r in results:

            df = pd.read_csv(r)
            total_rows = df['file_name'].size - 1
            declared_total = int(df._get_value(1, 'net_electors_total', takeable=False))

            if total_rows ==  declared_total:
                print(f'{r}: Correct total')
            else:
                print(f'{r}: Incorrect total: {total_rows} - {declared_total}')

if __name__ == '__main__':
    TS = Tests()
    TS.main('data/out/daman/2017')