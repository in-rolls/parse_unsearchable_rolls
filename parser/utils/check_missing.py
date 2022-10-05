import os
import sys

def main(paths):

    results = []
    A = [_.rstrip('.pdf') for _ in os.listdir(paths[0])]
    B = [_.rstrip('.csv') for _ in os.listdir(paths[1])]

    for a in A:
        if a not in B:
            results.append(a)

    print(results)
    print(len(results))


if __name__ == '__main__':
    paths = sys.argv[1:]
    main(paths)