from joern.all import JoernSteps
import subprocess
import os
from shutil import copyfile
import time

#DATASET_PATH = "/home/k1462425/Documents/Research/src_allforums_c_nocloneshamming/src_allforums_c_nocloneshamming/"
#JOERN_INPUT_PATH = "/home/k1462425/Documents/Research/ast_bigram_approach/joern/"
#JOERN_JAR_PATH = "/home/k1462425/Documents/Research/StylometryFramework/joern-0.3.1/bin/joern.jar"
#NEO4J_BIN_PATH = "/home/k1462425/neo4j-community-2.1.8/bin/neo4j"
#SAVE_FUNCTION_INDICES_PATH = "/home/k1462425/Documents/Research/sample_function_indices/"
#NUM_FUNCTIONS_PER_SAMPLE_PATH = "/home/k1462425/Documents/Research/sample_function_indices/samples_num_functions.csv"

DATASET_PATH = "/scratch/michal/unknowncheats_dataset_working/"
JOERN_INPUT_PATH = "/scratch/michal/joern_working_dir/"
JOERN_JAR_PATH = "/opt/joern-0.3.1/bin/joern.jar"
NEO4J_BIN_PATH = "/scratch/michal/neo4j-community-2.1.8/bin/neo4j"
SAVE_FUNCTION_INDICES_PATH = "/scratch/michal/sample_function_indices/"
NUM_FUNCTIONS_PER_SAMPLE_PATH = "/scratch/michal/sample_function_indices/samples_num_functions_uc.csv"

count = 0
filecount = 0

def listdir_fullpath(d):
    return [os.path.join(d, f) for f in os.listdir(d)]


def main():
    files_done = []
    with open(NUM_FUNCTIONS_PER_SAMPLE_PATH,'r') as fp:
        contents = fp.read()
    fp.close()
    lines = contents.split("\n")
    for line in lines:
        if len(line.split(",")) > 1:
            if line.split(",")[1] == "0":
                files_done.append(line.split(",")[0])
    print(files_done)
    print(len(files_done))
    skipfile_counter = 0
    #for file in files_done:
    #    if file == "1031806_17840559_1.c":
    #        print("FOUND!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")

    functions_files = listdir_fullpath(SAVE_FUNCTION_INDICES_PATH)
    functions_files_c = []
    for function_file in functions_files:
        filename = function_file.split("/")[-1][:-4]
        #print(filename)
        functions_files_c.append(filename)

    dirs = listdir_fullpath(DATASET_PATH)
    for dir in dirs:
        if os.path.isdir(dir):
            files = listdir_fullpath(dir)
            for file in files:
                if (file.endswith(".c") or file.endswith(".cpp")) and (not file.split("/")[-1].rstrip() in files_done) and (not file.split("/")[-1].rstrip() in functions_files_c):
                    print("extracting")
                    print(file.split("/")[-1].rstrip())
                    copyfile(file, JOERN_INPUT_PATH+file.split("/")[-1])
                    produce_indices(file)
                else:
                    skipfile_counter += 1
                    print("Skipping file, already done.")
                    print(file.split("/")[-1])
                    print("Skipped: "+str(skipfile_counter))


def produce_indices(file):
    subprocess.call(['java', '-jar', JOERN_JAR_PATH, JOERN_INPUT_PATH],cwd=JOERN_INPUT_PATH)
    subprocess.call([NEO4J_BIN_PATH,'start-no-wait'])
    time.sleep(5)
    file_function_location_triads = produce_file_function_location_triads(file)
    subprocess.call([NEO4J_BIN_PATH,'stop'])
    subprocess.call(['rm', '-r', JOERN_INPUT_PATH+".joernIndex"])
    subprocess.call(['rm', '-r', JOERN_INPUT_PATH+file.split("/")[-1]])

    if not os.path.exists(SAVE_FUNCTION_INDICES_PATH):
        os.mkdir(SAVE_FUNCTION_INDICES_PATH)
    with open(SAVE_FUNCTION_INDICES_PATH+file.split("/")[-1]+".txt",'a+') as fp:
        print("IN OPEN")
        #fp.write("\n")
        for triad in file_function_location_triads:
            triadString = triad[0]+","+triad[1]+","+triad[2]
            fp.write(triadString+"\n")

    fp.close()

    global count
    global filecount
    filecount += 1
    count += len(file_function_location_triads)

    print("Number of functions extracted: "+str(count))
    print("Files done: "+str(filecount))

    with open(NUM_FUNCTIONS_PER_SAMPLE_PATH,'a') as fp:
        fp.write(file.split("/")[-1]+","+str(len(file_function_location_triads))+"\n")

    fp.close()


def produce_file_function_location_triads(file):
    j = JoernSteps()
    j.setGraphDbURL('http://localhost:7474/db/data/')
    j.connectToDatabase()
    root_nodes = j.runGremlinQuery('queryNodeIndex("type:Function")')
    start_indices = []
    function_names = []
    for root_node in root_nodes:
        locationString = root_node.properties['location']
        lineNumber = locationString.split(":")[0]
        start_indices.append(str(int(lineNumber)-1))
        function_names.append(root_node.properties['name'])

    triads = []

    x = 0
    while x < len(start_indices):
        triads.append((file.split("/")[-1],function_names[x],start_indices[x]))
        x = x + 1

    return triads


main()
