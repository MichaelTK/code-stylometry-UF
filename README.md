# code-stylometry-UF
dataset_language_guesser.py

run within the dataset directory

dataset_language_copier_allforums.py

run from anywhere, makes a new dataset directory with only C/C++ files.

code_clone_hamming_trimmer_allforums.py

run from anywhere, makes a new dataset directory with clones removed.

joern_function_index_generator.py
joern_function_index_generator_continue.py

generate function indices in files in dataset. If the first script crashes, use the
second to pick up where it left off.

function_extractor.py

extracts functions from the original files using the function indices generated in the
previous step.

code_clone_hamming_trimmer_allforums.py

run this on the new functionsplit dataset.

programs_pickle_generator.py

use this to generate a pickle of the code of a specific number of authors specified with
--authors. --min specifies the minimum number of samples per author, --max specifies
the maximum number of samples per author.

pickle_top_authors_selector.py    

Use this to create a new pickle containing only the top X authors. Use the --authors option to     
specify this.

pickle_thresholdsize_remover.py 

use this to remove samples below a certain LoC threshold using the --lines argument.

pickle_number_of_samples_per_author_trimmer.py

use this to remove authors who have below a threshold of number of samples. The --samples argument
will do this.
