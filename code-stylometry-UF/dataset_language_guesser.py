import os
import sys

SOURCE_PATH = "/scratch/michal/whole_datasets_without_threads/mpgh/"
#DEST_PATH = "/scratch/michal/cheaters_dataset/"
#SOURCE_PATH = "/home/k1462425/Downloads/unknowncheats_dataset/sourceCode/"
#DEST_PATH = "/home/k1462425/Documents/Research/cheaters_dataset/"

def listdir_fullpath(d):
    return [os.path.join(d, f) for f in os.listdir(d)]

def main():
    dirs = listdir_fullpath(SOURCE_PATH)
    for dir in dirs:
        if os.path.isdir(dir):
            files = listdir_fullpath(dir)
            for file in files:
                command = "cat "+file + " | guesslang > output"
                os.system(command)
                with open("output","r") as fp:
                    lines = []
                    line = fp.readline()
                    lines.append(line)
                    while line:
                        line = fp.readline()
                        lines.append(line)
                    theLine = lines[-2]
                with open("languages","a") as languages_file:
                    languages_file.write(file+": "+theLine)


main()
