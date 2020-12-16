import pandas as pd
import argparse

#DATA_PATH="/home/k1462425/Documents/Research/cheaters_c_min5perauthor_above25lines_5.pkl"
DATA_PATH="/home/k1462425/Documents/Research/uf_functionsplit_combinedintoparents.pkl"
DEST_PATH="/home/k1462425/Documents/Research/"
#DEST_PATH="/home/k1462425/Documents/Research/ast_bigram_approach/data/"


def main(author_number):
    authors_and_amounts_dict = {}
    data = pd.read_pickle(DATA_PATH)

    for elem in data[2]:
        authors_and_amounts_dict[elem] = 0

    #print(authors_and_amounts_dict)

    for elem in data[2]:
        authors_and_amounts_dict[elem] = authors_and_amounts_dict[elem] + 1

    #print(authors_and_amounts_dict)

    authors = []
    amounts = []

    for elem in authors_and_amounts_dict:
        authors.append(elem)
        amounts.append(authors_and_amounts_dict[elem])

    x = 0
    y = 0
    while y < len(authors):
        x = 0
        #print(y)
        while x < len(authors)-1:
            tmp_author = authors[x]
            tmp_amount = amounts[x]
            if amounts[x] < amounts[x+1]:
                #print(x)

                amounts[x] = amounts[x+1]
                authors[x] = authors[x+1]
                amounts[x+1] = tmp_amount
                authors[x+1] = tmp_author
                #print(amounts)

            x = x + 1
        y = y + 1

    authors = authors[1:author_number+1]
    amounts = amounts[1:author_number+1]
    print(authors)
    print(amounts)

    elements = []
    x = 0
    while x < len(data[2]):
        here_author = data[2][x]

        if here_author in authors:
            triad = (data[0][x],data[1][x],data[2][x],data[3][x])
            elements.append(triad)

        x = x + 1

    df = pd.DataFrame(elements)
    pd.to_pickle(df, DEST_PATH+"uf_functionsplit_combinedintoparents_top_"+str(author_number)+".pkl")



parser = argparse.ArgumentParser(description="Choose a number of authors.")
parser.add_argument('--authors',type=int)
args = parser.parse_args()
if not args.authors:
    print("No specified author number.")
    exit(1)
main(args.authors)
