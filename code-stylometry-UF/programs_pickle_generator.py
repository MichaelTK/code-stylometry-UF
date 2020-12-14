import os
import numpy
import pandas
import argparse
import pickle

#MPGH_PATH = "/home/k1462425/Documents/Research/cheaters_datasets/mpgh_astnn_dataset/"
UNKNOWNCHEATS_PATH = "/home/k1462425/Documents/Research/cheaters_datasets/unknowncheats_astnn_dataset/"
MPGH_PATH = "/home/k1462425/Documents/Research/cheaters_datasets_without_clones/mpgh_astnn_dataset/"
#ALL_PATH = "/scratch/michal/uc_and_mpgh_attachments/"
#ALL_PATH = "/scratch/michal/gcj_c/"
ALL_PATH = "/scratch/michal/sourceCode_parentsamples_minusorphans/"
def listdir_fullpath(d):
    return [os.path.join(d, f) for f in os.listdir(d)]


def main(min_number,max_number):
    print("Generating pickle for data...")
    generate_programs_pickle(ALL_PATH,min_number,max_number)
    print("Done.")


def generate_programs_pickle(path,min_number,max_number):
    dirs = listdir_fullpath(path)
    authors = []
    malware_sample_sources = []
    authors_fileamount_dict = {}
    file_and_id_dict = {}
    author_number = 1
    print("Loading source code...")
    for dir in dirs:
        if os.path.isdir(dir):
            authors.append(dir.split('/')[-1])
            files = listdir_fullpath(dir)
            if len(files) >= min_number:
                authors_fileamount_dict[dir.split('/')[-1]] = len(files)
                #index = 0
                #while index < min_number:
                #    triad = (len(malware_sample_sources),get_source_code(files[index]),author_number)
                #    malware_sample_sources.append(triad)
                #    index = index + 1
                doneFiles = 0
                for file in files:
                    if doneFiles <= max_number:
                        triad = (len(malware_sample_sources),get_source_code(file),file.split("/")[-2],file.split("/")[-1])
                        file_and_id_dict[len(malware_sample_sources)] = file
                        malware_sample_sources.append(triad)
                        doneFiles = doneFiles + 1
                author_number = author_number + 1

    with open(ALL_PATH+'ids_and_files.pkl', 'wb') as handle:
        pickle.dump(file_and_id_dict, handle, protocol=pickle.HIGHEST_PROTOCOL)

    print("Source code loaded.")
    print("Pickling the source code...")
    malware_sample_sources = numpy.asarray(malware_sample_sources)

    df = pandas.DataFrame(malware_sample_sources)
    df.columns = [0,1,2,3]
    df.to_pickle(path+"programs.pkl")


def get_source_code(file):
    global number_of_exceptions
    source = ""
    with open(file,'r',encoding='utf-8') as fp:
        line = ""
        try:
            line = fp.readline()
            source += line
        except:
            pass
        while line:
            try:
                line = fp.readline()
                source += line
            except:
                pass
    return source


parser = argparse.ArgumentParser(description="Choose a minimum number of files for each author.")
parser.add_argument('--min',type=int)
parser.add_argument('--max',type=int)
args = parser.parse_args()
if not args.min:
    print("No specified minimum number.")
    exit(1)
if not args.max:
    print("No specified maximum number.")
    exit(1)
main(args.min,args.max)
