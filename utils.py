import argparse
def parse_args():
    parser = argparse.ArgumentParser(prog='bball_stats')
    parser.add_argument("--data_file", type=str)
    return parser.parse_args()

import os
def mkdir(path):
    if not os.path.exists(path):
        os.makedirs(path) 
    return path  