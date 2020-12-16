import os
import pickle
import pandas
import argparse
from random import randint

PROGRAMS_PATH = "/home/k1462425/Documents/Research/cheaters_functionsplit_fromtop100_noclones_c_above120lines.pkl"
PARENT_PATH = "/home/k1462425/Documents/Research/"

def listdir_fullpath(d):
    return [os.path.join(d, f) for f in os.listdir(d)]

def main(number_of_samples):
    programs = pandas.read_pickle(PROGRAMS_PATH)
    elements = []

    author_and_number_of_samples = {}
    x = 0
    while x < len(programs[1]):
        author_and_number_of_samples[programs[2][x]] = 0
        x = x + 1

    x = 0
    while x < len(programs[1]):
        author_and_number_of_samples[programs[2][x]] = author_and_number_of_samples[programs[2][x]] + 1
        x = x + 1

    authors_to_remove = []

    for elem in author_and_number_of_samples:
        #print(author_and_number_of_samples[elem])
        if author_and_number_of_samples[elem] >= number_of_samples:
            authors_to_remove.append(elem)

    print("Number of authors to keep:")
    print(len(authors_to_remove))

    elements = []
    x = 0
    while x < len(programs[1]):
        triad = (programs[0][x],programs[1][x],programs[2][x],programs[3][x])
        if programs[2][x] in authors_to_remove:
            elements.append(triad)
        x = x + 1

    df = pandas.DataFrame(elements)
    if os.path.exists(PARENT_PATH+"cheaters_c_min5perauthor_above120lines_fromtop100_"+str(number_of_samples)+".pkl"):
        os.remove(PARENT_PATH+"cheaters_c_min5perauthor_above120lines_fromtop100_"+str(number_of_samples)+".pkl")
    pandas.to_pickle(df, PARENT_PATH+"cheaters_c_min5perauthor_above120lines_fromtop100_"+str(number_of_samples)+".pkl")



parser = argparse.ArgumentParser(description="Choose a number of minimum samples per author.")
parser.add_argument('--samples',type=int)
args = parser.parse_args()
if not args.samples:
    print("No specified number of samples per author.")
    exit(1)
main(args.samples)
