# code-stylometry-UF
**dataset_language_guesser.py**

Run this within the dataset directory to generate a file containing the languages of the samples.

**dataset_language_copier_allforums.py**

Run from anywhere, makes a new dataset directory with only C/C++ files.

**code_clone_hamming_trimmer_allforums.py**

Run from anywhere, makes a new dataset directory with clones removed.

**joern_function_index_generator.py**

**joern_function_index_generator_continue.py**

generate function indices in files in dataset. If the first script crashes, use the
second to pick up where it left off.

**function_extractor.py**

Extracts functions from the original files using the function indices generated in the
previous step.

**code_clone_hamming_trimmer_allforums.py**

Run this on the new functionsplit dataset. 

**programs_pickle_generator.py**

Use this to generate a pickle of the code of a specific number of authors specified with
--authors. --min specifies the minimum number of samples per author, --max specifies
the maximum number of samples per author.

**pickle_top_authors_selector.py**   

Use this to create a new pickle containing only the top X authors. Use the --authors option to     
specify this.

**pickle_thresholdsize_remover.py**

Use this to remove samples below a certain LoC threshold using the --lines argument.

**pickle_number_of_samples_per_author_trimmer.py**

Use this to remove authors who have below a threshold of number of samples. The --samples argument
will do this.

**preprocessor.py**

Specify the pickle file to generate feature vectors from using --source. By default this file is assumed to be within a data/ subdirectory.

**classifier_bigrams_layout_lexical.py**

Perform learning and classification on the --input file generated in the previous step. By default this file will be generated in a data/train/ subdirectory, and will be called blocks.pkl.
