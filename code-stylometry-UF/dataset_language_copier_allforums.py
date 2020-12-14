import os
import sys
import subprocess
from pathlib import Path
from shutil import copyfile
from shutil import rmtree

SOURCE_PATH = "/scratch/michal/sourceCodeAllForums/"
DEST_PATH = "/scratch/michal/sourceCodeAllForums_C/"
#SOURCE_PATH = "/home/k1462425/Downloads/unknowncheats_dataset/sourceCode/"
#DEST_PATH = "/home/k1462425/Documents/Research/unknowncheats_astnn_dataset/"

def listdir_fullpath(d):
    return [os.path.join(d, f) for f in os.listdir(d)]

def copyFiles(dir):
    forum = dir.split('/')[-1]
    fl = open(SOURCE_PATH+forum+"/"+"languages",'r')

    line = fl.readline()
    path = line.split(":")[0]
    parent_directory = path.split("/")[-2]

    line = line.rstrip()

    if line.endswith("C") or line.endswith("C++"):
        try:
            os.mkdir(DEST_PATH+forum)
        except Exception as e:
            pass
        try:
            os.mkdir(DEST_PATH+forum+"/"+parent_directory)
        except Exception as e:
            pass
        copyfile(path,DEST_PATH+forum+"/"+parent_directory+"/"+path.split("/")[-1])


    while line:
        line = fl.readline()
        line = line.rstrip()
        forum = dir.split('/')[-1]
        path = line.split(":")[0]
        print(path)
        try:
            parent_directory = path.split("/")[-2]
            #print(repr(line))
            linesplit = line.split(" ")
            language_word = linesplit[-1]

            if "C++" in language_word:
                try:
                    os.mkdir(DEST_PATH+forum)
                except Exception as e:
                    pass
                try:
                    print("Making directory "+forum+"/"+parent_directory)
                    os.mkdir(DEST_PATH+forum+"/"+parent_directory)
                except Exception as e:
                    pass
                copyfile(path,DEST_PATH+forum+"/"+parent_directory+"/"+path.split("/")[-1]+".cpp")

            if ("C" in language_word and not "++" in language_word and not "SS" in language_word):
                try:
                    os.mkdir(DEST_PATH+forum)
                except Exception as e:
                    pass
                try:
                    print("Making directory "+forum+"/"+parent_directory)
                    os.mkdir(DEST_PATH+forum+"/"+parent_directory)
                except Exception as e:
                    pass
                copyfile(path,DEST_PATH+forum+"/"+parent_directory+"/"+path.split("/")[-1]+".c")
        except Exception as e:
            print("No path found. Exception.")

    fl.close()

def main():
    if os.path.exists(DEST_PATH):
        rmtree(DEST_PATH)
    try:
        os.mkdir(DEST_PATH)
    except Exception as e:
        pass

    entities = listdir_fullpath(SOURCE_PATH)
    dirs = []
    for entity in entities:
        if os.path.isdir(entity):
            dirs.append(entity)

    for dir in dirs:
        print(dir)
    for dir in dirs:
        copyFiles(dir)


main()
