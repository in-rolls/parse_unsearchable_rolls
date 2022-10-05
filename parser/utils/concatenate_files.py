import os
import glob
import pandas as pd
import sys

def main(paths):

    # Gather files
    files = []
    for path in paths:
        files.extend([os.path.join(path, f) for f in os.listdir(path)])
    files = list(filter(lambda x: x.endswith('.csv'), files))

    #combine all files in the list
    combined_csv = pd.concat([pd.read_csv(f) for f in files ])
    #export to csv
    combined_csv.to_csv( "all_csv.csv", index=False, encoding='utf-8-sig')


if __name__ == '__main__':
    paths = sys.argv[1:]
    main(paths)