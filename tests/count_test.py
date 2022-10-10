import os
import sys
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
            try:
                total_rows = df['file_name'].size
                declared_total = int(df._get_value(1, 'net_electors_total', takeable=False))

                if total_rows ==  declared_total:
                    print(f'{r}: Correct total')
                else:
                    print(f'{r}: Incorrect total: Total rows:{total_rows} - Declared rows:{declared_total}')
            except:
                print(f'{r}: No total')
        


if __name__ == '__main__':
    TS = Tests()
    try:
        path = sys.argv[1]
        TS.main(path)
    except Exception as e:
        print(f'Path error: {e}')