import os
import pickle
import pandas
import argparse

#PROGRAMS_PATH = "/home/k1462425/Documents/Research/ast_bigram_approach/data/gcj_4columns_min2perauthor.pkl"
#PROGRAMS_PATH = "/home/k1462425/Documents/Research/cheaters_c_functionsplit_noclones_above25lines_top_100.pkl"
PROGRAMS_PATH = "/home/k1462425/Documents/Research/allsource_C.pkl"
PARENT_PATH = "/home/k1462425/Documents/Research/"

def listdir_fullpath(d):
    return [os.path.join(d, f) for f in os.listdir(d)]

def main():
    programs = pandas.read_pickle(PROGRAMS_PATH)
    #print(programs)
    elements = []
    x = 0
    while x < len(programs[1]):
        lines = programs[1][x].split("\n")
        linestowrite = programs[1][x]

        if len(lines) >= 25:
            lines = ''.join(lines)
            triad = (x, linestowrite, programs[2][x], programs[3][x])
            elements.append(triad)
        #print(lines)
        x = x + 1


    df = pandas.DataFrame(elements)
    print(df)
    if os.path.exists(PARENT_PATH+"cheaters_c_above25lines.pkl"):
        os.remove(PARENT_PATH+"cheaters_c_above25lines.pkl")
    pandas.to_pickle(df, PARENT_PATH+"cheaters_c_above25lines.pkl")

main()
