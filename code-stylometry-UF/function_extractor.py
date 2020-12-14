import os

#DATASET_PATH = "/scratch/michal/sourceCodeAllForums_C_nocloneshamming_forfunctionsplitting/sourceCode4/"
#NUM_FUNCTIONS_PER_SAMPLE_PATH = "/scratch/michal/sample_function_indices/samples_num_functions.csv"
#SAVE_FUNCTION_INDICES_PATH = "/scratch/michal/sample_function_indices/"
#FUNCTIONSPLIT_DATASET_PATH = "/scratch/michal/sourceCode_functionsplit/"

DATASET_PATH = "/scratch/michal/gcj_c/"
NUM_FUNCTIONS_PER_SAMPLE_PATH = "/scratch/michal/sample_function_indices/samples_num_functions_gcj.csv"
SAVE_FUNCTION_INDICES_PATH = "/scratch/michal/sample_function_indices/"
FUNCTIONSPLIT_DATASET_PATH = "/scratch/michal/gcj_c_functionsplit2/"

def listdir_fullpath(d):
    return [os.path.join(d, f) for f in os.listdir(d)]

def main():
    nonzero_files = []
    with open(NUM_FUNCTIONS_PER_SAMPLE_PATH,'r') as fp:
        content = fp.read()
    fp.close()

    lines = content.split("\n")
    for line in lines:
        if len(line) > 3:
            if line.split(",")[1] != "0":
                nonzero_files.append(line.split(",")[0].rstrip())

    nonzero_files = list(set(nonzero_files))
    #print(nonzero_files)

    txt_files = listdir_fullpath(SAVE_FUNCTION_INDICES_PATH)
    source_files = []

    source_file_dirs = listdir_fullpath(DATASET_PATH)
    for source_file_dir in source_file_dirs:
        if os.path.isdir(source_file_dir):
            files = listdir_fullpath(source_file_dir)
            for file in files:
                source_files.append(file)

    #print(source_files)

    if not os.path.exists(FUNCTIONSPLIT_DATASET_PATH):
        os.mkdir(FUNCTIONSPLIT_DATASET_PATH)
    for dir in source_file_dirs:
        if os.path.isdir(dir):
            dirname = dir.split("/")[-1]
            if not os.path.exists(FUNCTIONSPLIT_DATASET_PATH+dirname):
                os.mkdir(FUNCTIONSPLIT_DATASET_PATH+dirname)

    files_progress_count = 0
    for file in nonzero_files:
        files_progress_count += 1
        print(str(files_progress_count)+"/"+str(len(nonzero_files)))
        corresponding_file = ""
        for f in source_files:
            if f.endswith(file):
        #        print(f)
                corresponding_file = f
        authordir = corresponding_file.split("/")[-2]
        #print(file)
        #print(authordir)
        exceptioncounter = 0
        if os.path.exists(SAVE_FUNCTION_INDICES_PATH+file+".txt"):
            with open(SAVE_FUNCTION_INDICES_PATH+file+".txt",'r') as fp:
                content = fp.read()
                lines = content.split("\n")
                lines = list(set(lines))

            fp.close()
            lineIndex = 0
            for line in lines:
                if len(line) > 3:
                    #print("here")
                    linesplit = line.split(",")
                    filename = linesplit[0]
                    functionname = linesplit[1]
                    startline = int(linesplit[2])
                    lines3 = []
                    with open(DATASET_PATH+authordir+"/"+file,'r') as fp:
                        line4 = fp.readline()
                        lines3.append(line4)
                        while line4:
                            line4 = fp.readline()
                            lines3.append(line4)

                        #print(lines3)

                        fp.close()

                        curly_stack = []
                        start_line_string = lines3[startline]
                        remainder_lines = lines3[startline:]
                        endline = -1
                        x = 0
                        #print("----------------------------------------------------------")
                        curly_stack = []
                        try:
                            while x < len(remainder_lines):
                                line2 = remainder_lines[x]
                                #print(line2)
                                #print(line2)
                                for letter in line2:
                                    if letter == "{":
                                        curly_stack.append("{")
                                    elif letter == "}":
                                        #print(curly_stack)
                                        curly_stack.pop(-1)
                                        #print(len(curly_stack))
                                        if len(curly_stack) == 0:
                                            endline = x+startline+1
                                            x = 9999999
                                            break

                                x = x + 1

                            function_lines = lines3[startline:endline]
                            with open(FUNCTIONSPLIT_DATASET_PATH+authordir+"/"+file.split(".")[-2]+"_"+str(lineIndex)+".c",'a+') as fp:
                                fp.writelines(function_lines)
                            lineIndex += 1
                        except Exception as e:
                            exceptioncounter += 1
                            pass

        print("Number of exceptions:")
        print(exceptioncounter)

                        #print(file)
                        #print(function_lines)
                        #for line5 in function_lines:
                        #    print(line5)
                        #print(function_lines)









main()
