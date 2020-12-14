import textdistance
import os
import time
from shutil import copyfile
from shutil import rmtree
import multiprocessing as mp
import itertools
import logging

#SOURCE_PATH = "/scratch/michal/sourceCodeAllForums_C/"
SOURCE_PATH = "/scratch/michal/sourceCode_functionsplit/"
#TRUNCATED_DATASET_PATH = "/scratch/michal/sourceCodeAllForums_C_nocloneshamming/"
TRUNCATED_DATASET_PATH = "/scratch/michal/sourceCode_functionsplit_nocloneshamming2/"

doneFiles = 0
global_files = []
#dictionary relating the snippet with how many times it's been posted.
amount_posted_file_dict = {}
snippet_with_authors_dict = {}
author_number_of_posts_dict = {}
authors_with_posts_dict = {}
global_clones = []
snippet_lengths = []
snippet_line_amounts = []
authors_with_clones = []
author_number_of_clones_dict = {}
author_percentage_clone_dict = {}
order_of_authors = []
total_posts_by_author_list = []
clone_percentage_by_author_list = []

def listdir_fullpath(d):
    return [os.path.join(d, f) for f in os.listdir(d)]

def detect_clones(file):

    with open(file,'r') as fp:
        contents1 = fp.read()
    fp.close()
    if file.endswith("fififo.c"):
        print("File1: "+file)

    #if len(contents1) < 3000: #if length of file contents is smaller than this many characters, skip the comparisons, it will take too long
    clones = []
    clones.append(True)
    for file2 in global_files:
        if file.endswith("fififo.c"):
            print("File2:" +file2)
        if file != file2:
            file2split = file2.split('/')
            filesplit = file.split('/')
            if file2split[:-1] == filesplit[:-1]: #if the two files have the same author, we treat it as not a code clone.
                continue
            with open(file2,'r') as fp:
                contents2 = fp.read()
            fp.close()

                #if len(contents2) > 3000:
                #    continue

            diff = 0

            if len(contents1) > len(contents2):
                diff = len(contents1) - len(contents2)

            if len(contents2) > len(contents1):
                diff = len(contents2) - len(contents1)

                #if diff > 200:
                #    continue

            try: #if the recursion tree breaks the program, treat the file as without clones
                distance = textdistance.hamming.normalized_distance(contents1, contents2)
            except Exception as e:
                print("Exception! Returning file")
                continue

            if (distance > 0.01):
                continue
            elif (distance <= 0.01):
                print("Clone found!")
                print("File 1: "+file)
                print("File 2: "+file2)
                clones.append((file,file2))
                #return (True,file,file2)
        return clones
    #else:
    #    return (False,file)

    return (False,file)


def code_clone_hamming_for_forum(forum):
    authors = []

    dirs = listdir_fullpath(forum)

    global global_files, authors_with_clones, authors_with_posts_dict, snippet_line_amounts, snippet_lengths, global_clones, order_of_authors, snippet_with_authors_dict, amount_posted_file_dict, author_number_of_clones_dict, author_percentage_clone_dict, author_number_of_posts_dict

    for dir in dirs:
        if os.path.isdir(dir):
            files = listdir_fullpath(dir)
            author_number_of_posts_dict[dir.split("/")[-1]] = 0
            for file in files:
                author_number_of_posts_dict[dir.split("/")[-1]] = author_number_of_posts_dict[dir.split("/")[-1]] + 1

    dirs = listdir_fullpath(forum)
    for dir in dirs:
        if os.path.isdir(dir):
            files = listdir_fullpath(dir)
            authors_with_posts_dict[dir.split("/")[-1]] = set([])
            for file in files:
                authors_with_posts_dict[dir.split("/")[-1]].add(file)


    print("Getting all files...")
    for dir in dirs:
        if os.path.isdir(dir):
            files = listdir_fullpath(dir)
            authors.append(dir.split("/")[-1])
            for file in files:
                global_files.append(file)
    print("Done.")

    snippet_lengths.extend(get_snippet_lengths(forum))
    snippet_line_amounts.extend(get_snippet_line_amounts(forum))

    #global_files = global_files[:1000] #for debugging

    print("Number of files found: "+str(len(global_files)))
    doneFiles = 0
    #pool = mp.Pool(mp.cpu_count())
    pool = mp.Pool(75)
    results = set([])

    for file in global_files:
        amount_posted_file_dict[file] = 0

    for file in global_files:
        snippet_with_authors_dict[file] = set([])

    try:
        for fil in pool.imap_unordered(detect_clones, global_files):
            if fil[0] == True:

                fil = fil[1:]

                for clone in fil:
                    global_clones.append(clone)
                    newfil = (True,clone[0])
                    results.add(newfil)
                    newfil2 = (True,clone[1])
                    results.add(newfil2)
                    authors_with_clones.append(clone[0].split("/")[-2])
                    authors_with_clones.append(clone[1].split("/")[-2])
                    amount_posted_file_dict[clone[0]] = amount_posted_file_dict[clone[0]] + 1
                    #amount_posted_file_dict[clone[1]] = amount_posted_file_dict[clone[1]] + 1
                    snippet_with_authors_dict[clone[0]].add(clone[0].split("/")[-2])
                    snippet_with_authors_dict[clone[0]].add(clone[1].split("/")[-2])
                    snippet_with_authors_dict[clone[1]].add(clone[0].split("/")[-2])
                    snippet_with_authors_dict[clone[1]].add(clone[1].split("/")[-2])

            doneFiles = doneFiles + 1
            logging.debug(str(doneFiles)) # report progress by printing the result
    except KeyboardInterrupt:
        logging.warning("got Ctrl+C")
    finally:
        pool.terminate()
        pool.join()

    for snippet in snippet_with_authors_dict:
        if len(snippet_with_authors_dict[snippet]) == 0:
            snippet_with_authors_dict[snippet].add(snippet.split("/")[-2])
        amount_posted_file_dict[snippet] = len(snippet_with_authors_dict[snippet])


    set_authors_with_clones = set(authors_with_clones)
    print("Number of authors with clones: "+str(len(set_authors_with_clones)))
    print("Out of number of authors: "+str(len(authors)))

    percentage = len(set_authors_with_clones)/len(authors)
    print("Percentage of total authors that have posted clones: "+str(percentage))

    for author in authors:
        author_number_of_clones_dict[author] = 0

    for clone in results:
        author = clone[1].split("/")[-2]
        author_number_of_clones_dict[author] = author_number_of_clones_dict[author] + 1 #iffy

    for author in authors:
        author_percentage_clone_dict[author] = 0

    for author in authors:
        author_percentage_clone_dict[author] = (author_number_of_clones_dict[author]/author_number_of_posts_dict[author]) #iffy; author_number_of_clones_dict might be overestimating the actual number of clones posted

    for author in author_number_of_posts_dict:
        order_of_authors.append(author)

    print("DEBUG")
    print(len(author_number_of_posts_dict))
    print(len(author_number_of_clones_dict))
    print(len(order_of_authors))

    x = 0
    while x < len(order_of_authors):
        total_posts_by_author_list.append(author_number_of_posts_dict[order_of_authors[x]])
        x = x + 1

    print(len(order_of_authors))
    print(len(authors))
    x = 0
    while x < len(order_of_authors):
        clone_percentage_by_author_list.append(author_percentage_clone_dict[order_of_authors[x]])
        x = x + 1

    print("Authors with more than 200 posts: ")
    for author in authors:
        if author_number_of_posts_dict[author] > 200:
            print("--------------")
            print(author)
            print(author_percentage_clone_dict[author])
            print("--------------")


    number_of_clones = 0

    print("Number of clones found: " +str(len(results)))

    forumSuffix = forum.split('/')[-1]

    print("Populating new dataset at path: "+str(TRUNCATED_DATASET_PATH+forumSuffix))
    if os.path.exists(TRUNCATED_DATASET_PATH):
        print("Destination directory exists. Removing...")
        rmtree(TRUNCATED_DATASET_PATH)
        print("Removed.")
    if not os.path.exists(TRUNCATED_DATASET_PATH):
        print("Creating destination directory...")
        os.mkdir(TRUNCATED_DATASET_PATH)
        os.mkdir(TRUNCATED_DATASET_PATH+forumSuffix)
        print("Done.")
    elif not os.path.exists(TRUNCATED_DATASET_PATH+forumSuffix):
        print("Creating destination directory...")
        os.mkdir(TRUNCATED_DATASET_PATH+forumSuffix)
        print("Done.")

    for fil in global_files:
        if not (True,fil) in results:
            filesplit = fil.split('/')
            if not os.path.exists(TRUNCATED_DATASET_PATH+forumSuffix+"/"+filesplit[-2]):
                os.mkdir(TRUNCATED_DATASET_PATH+forumSuffix+"/"+filesplit[-2])
            copyfile(fil,TRUNCATED_DATASET_PATH+forumSuffix+"/"+filesplit[-2]+"/"+filesplit[-1])

    print("Populated new dataset.")

    #SAVING DICTIONARIES AND LISTS FOR FUTURE USE
    import pickle
    dict = author_number_of_posts_dict
    f = open(TRUNCATED_DATASET_PATH+"author_number_of_posts_dict.pkl","wb")
    pickle.dump(dict,f)
    f.close()

    dict = author_percentage_clone_dict
    f = open(TRUNCATED_DATASET_PATH+"author_percentage_clone_dict.pkl","wb")
    pickle.dump(dict,f)
    f.close()

    dict = author_number_of_clones_dict
    f = open(TRUNCATED_DATASET_PATH+"author_number_of_clones_dict.pkl","wb")
    pickle.dump(dict,f)
    f.close()

    dict = amount_posted_file_dict
    f = open(TRUNCATED_DATASET_PATH+"amount_posted_file_dict.pkl","wb")
    pickle.dump(dict,f)
    f.close()

    dict = snippet_with_authors_dict
    f = open(TRUNCATED_DATASET_PATH+"snippet_with_authors_dict.pkl","wb")
    pickle.dump(dict,f)
    f.close()

    l = order_of_authors
    with open(TRUNCATED_DATASET_PATH+"order_of_authors.pkl", "wb") as fp:   #Pickling
        pickle.dump(l, fp)

    l = global_clones
    with open(TRUNCATED_DATASET_PATH+"clones.pkl", "wb") as fp:   #Pickling
        pickle.dump(l, fp)

    l = snippet_lengths
    with open(TRUNCATED_DATASET_PATH+"snippet_lengths.pkl", "wb") as fp:   #Pickling
        pickle.dump(l, fp)

    l = snippet_line_amounts
    with open(TRUNCATED_DATASET_PATH+"snippet_line_amounts.pkl", "wb") as fp:   #Pickling
        pickle.dump(l, fp)

    dict = authors_with_posts_dict
    f = open(TRUNCATED_DATASET_PATH+"authors_with_posts_dict.pkl","wb")
    pickle.dump(dict,f)
    f.close()

    #with open("test.txt", "rb") as fp:   # Unpickling
    #    b = pickle.load(fp)


def main():
    global global_files, authors_with_posts_dict, snippet_line_amounts, snippet_lengths, global_clones, order_of_authors, snippet_with_authors_dict, amount_posted_file_dict, author_number_of_clones_dict, author_percentage_clone_dict, author_number_of_posts_dict

    logging.basicConfig(format="%(asctime)-15s %(levelname)s %(message)s",datefmt="%F %T", level=logging.DEBUG)

    entities = listdir_fullpath(SOURCE_PATH)
    dirs = []
    for entity in entities:
        if os.path.isdir(entity):
            dirs.append(entity)

    for dir in dirs:
        code_clone_hamming_for_forum(dir)


def get_snippet_lengths(forum):
    forumSuffix = forum.split('/')[-1]
    lengths = []
    dirs = listdir_fullpath(SOURCE_PATH+forumSuffix)
    for dir in dirs:
        if os.path.isdir(dir):
            files = listdir_fullpath(dir)
            for file in files:
                with open(file,'r') as fp:
                    contents1 = fp.read()
                fp.close()
                lengths.append(len(contents1))
    return lengths

def get_snippet_line_amounts(forum):
    forumSuffix = forum.split('/')[-1]
    lengths = []
    dirs = listdir_fullpath(SOURCE_PATH+forumSuffix)
    for dir in dirs:
        if os.path.isdir(dir):
            files = listdir_fullpath(dir)
            for file in files:
                lines = []
                with open(file,'r') as fp:
                    line = fp.readline()
                    lines.append(line)
                    while line:
                        line = fp.readline()
                        lines.append(line)

                fp.close()
                lengths.append(len(lines))
    return lengths


main()
