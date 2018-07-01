import pstats
import argparse

parser = argparse.ArgumentParser(description='Process stats from another Python program.')

import argparse
parser = argparse.ArgumentParser()
parser.add_argument('filename', help='specify filename of cprofile output to parse and produce stats for')
args = parser.parse_args()

print(args)

p = pstats.Stats(args.filename)
p.strip_dirs().sort_stats('cumulative').print_stats()
