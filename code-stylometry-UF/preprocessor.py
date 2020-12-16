#Preprocessing pipeline to generate vectors including game hacking domain specific features.
#These features:
#Language of comments
#Code words which indicate the game being hacked
#Number of calls to malloc

from joern.all import JoernSteps
import subprocess
import pandas as pd
import os
import random
import argparse
import pickle
import copy
import math
import re
from shutil import rmtree

JOERN_INPUT_PATH = "/home/k1462425/Documents/Research/ast_bigram_approach/joern/"
JOERN_JAR_PATH = "/home/k1462425/Documents/Research/StylometryFramework/joern-0.3.1/bin/joern.jar"
NEO4J_BIN_PATH = "/home/k1462425/neo4j-community-2.1.8/bin/neo4j"

pd.options.mode.chained_assignment = None  # default='warn'. suppresses copy warnings
transIndex = 0
transIndex2 = 0
global_node_types = ['ParameterList', 'SizeofOperand', 'Argument', 'MemberAccess', 'CompoundStatement', 'BlockStarter', 'Sizeof', 'Expression', 'IdentifierDecl', 'ForInit', 'Callee', 'UnaryExpression', 'ElseStatement', 'SwitchStatement', 'IdentifierDeclType', 'Parameter', 'OrExpression', 'UnaryOp', 'DoStatement', 'PrimaryExpression', 'ConditionalExpression', 'CallExpression', 'IdentifierDeclStatement', 'Statement', 'InclusiveOrExpression', 'InitializerList', 'WhileStatement', 'MultiplicativeExpression', 'UnaryOperator', 'IfStatement', 'CastTarget', 'CastExpression', 'ArgumentList', 'ArrayIndexing', 'Label', 'EqualityExpression', 'BitAndExpression', 'ForStatement', 'PtrMemberAccess', 'BreakStatement', 'AndExpression', 'ContinueStatement', 'AdditiveExpression', 'SizeofExpr', 'ReturnType', 'Identifier', 'Condition', 'IncDecOp', 'RelationalExpression', 'ParameterType', 'ShiftExpression', 'ExclusiveOrExpression', 'ExpressionStatement', 'IncDec', 'AssignmentExpr', 'GotoStatement', 'ReturnStatement']

call_of_duty_keywords = ['mw2','mw3','call of duty','cod','infinity ward','treyarch']
arma_keywords = ['arma','dayz','bohemia']
warrock_keywords = ['warrock']
trove_keywords = ['trove']
counterstrike_keywords = ['csgo','counterstrike','counter strike']
crossfire_keywords = ['crossfire']
combatarms_keywords = ['combat arms','combatarms']
tutorial_keywords = ['tutorial']

important_keywords = ['arma','dayz','bohemia','warfare','warrock','trove','csgo','counterstrike','crossfire','combat arms','tutorial','firstperson','quaternion','fire_rate','firerate','gun','sword','zombie','knife','health','weapon','reticle','draw','trigger','rifle','pistol','attack','socket','raycast','die','dead','hook','random']

class Pipeline:

    def __init__(self,  ratio, root, source_path):
        self.source_code_input = source_path
        self.ratio = ratio
        self.root = root
        self.sources = None
        self.sources_for_layout = None
        self.sources_for_lexical = None
        self.sources_for_wordunigrams = None
        self.sources_for_syntactical = None
        self.train_file_path = None
        self.dev_file_path = None
        self.test_file_path = None
        self.size = None
        self.corpo = None


    def parse_source(self, output_file, option):

        def produce_nodes_string():

            def queryParent(j,nodeId):
                j.connectToDatabase()
                parent = j.runGremlinQuery('g.v('+str(nodeId)+').parents()')
                return parent

            def getStringForNode(node,nodes_and_parents):
                global global_node_types
                parent = nodes_and_parents[node]

                code = str(parent[0].properties['code']).replace(',','')
                code = code.replace('¬','')
                parentString = parent[0].properties['type']+","+code+","+str(parent[0].properties['functionId'])+","+str(parent[0].properties['childNum'])
                parent_identifier = hash(tuple(parentString))
                code = str(node.properties['code']).replace(',','')
                code = code.replace('¬','')
                nodeString = node.properties['type']+","+code+","+str(node.properties['functionId'])+","+str(node.properties['childNum'])
                node_identifier = hash(tuple(nodeString))

                addition_string = str(node_identifier)+","+str(node.properties['type'])+","+str(node.properties['code'])+","+str(node.properties['functionId'])+","+str(node.properties['childNum'])+","+str(parent_identifier)+"¬"
                #global_node_types.add(node.properties['type'])
                return addition_string

            syntactical_features = []
            #max_depth_ast = get_max_depth_ast()
            #ast_node_types_tfs = get_node_types_tfs()
            #ast_node_types_tfidfs = get_node_types_tfidfs()
            #ast_node_type_avg_depths = get_node_type_avg_depth()
            #keywords_term_frequency = get_keywords_term_frequency()

            global global_node_types

            ast_features = [0]*57

            all_nodes_string = ""
            j = JoernSteps()
            j.setGraphDbURL('http://localhost:7474/db/data/')
            j.connectToDatabase()
            root_nodes = j.runGremlinQuery('queryNodeIndex("type:FunctionDef")')
            all_ast_nodes = j.runGremlinQuery('queryNodeIndex("type:FunctionDef").astNodes()')
            ast_parents = j.runGremlinQuery('queryNodeIndex("type:FunctionDef").astNodes().parents()')
            nodes_and_parents = {}

            for node in all_ast_nodes:
                nodes_and_parents[node] = queryParent(j,node._id)

            for node in all_ast_nodes:
                if not node in root_nodes:
                    all_nodes_string += getStringForNode(node,nodes_and_parents)

            for ast_node in all_ast_nodes:
                x = 0
                while x < len(global_node_types):
                    if global_node_types[x] == ast_node.properties['type']:
                        ast_features[x] += 1
                        x = x + 1
                        continue
                    else:
                        x = x + 1

            #print(ast_features)
            #print(all_nodes_string)

            return all_nodes_string, ast_features

        def getLnNumTabs(code):
            lnNumTabs = 0
            tabcount = code.count("\t")
            try:
                lnNumTabs = math.log(tabcount/len(code))
            except Exception as e:
                pass
            #print(lnNumTabs)
            return lnNumTabs

        def getLnNumSpaces(code):
            lnNumSpaces = 0
            numSpaces = code.count(" ")
            try:
                lnNumSpaces = math.log(numSpaces/len(code))
            except Exception as e:
                pass
            #print(lnNumSpaces)
            return lnNumSpaces

        def getLnEmptyLines(code):
            lnEmptyLines = 0
            numEmptyLines = code.count("\n\n")
            try:
                lnEmptyLines = math.log(numEmptyLines/len(code))
            except Exception as e:
                pass
            return lnEmptyLines

        def getWhiteSpaceRatio(code):
            whiteSpaceRatio = 0
            whiteSpaceCount = code.count(" ")+code.count("\n")+code.count("\t")
            whiteSpaceRatio = whiteSpaceCount/(len(code)-whiteSpaceCount)
            #print(whiteSpaceRatio)
            return whiteSpaceRatio

        def getNewLineB4OpenBrace(code):
            newLineB4OpenBrace = 2
            countPos = 0
            countNeg = 0
            x = 1
            while x < len(code):
                if code[x] == "{" or code[x] == "}":
                    if code[x-1] == "\n":
                        countPos += 1
                    else:
                        countNeg += 1
                x = x + 1
            if countPos > countNeg:
                newLineB4OpenBrace = 1
            elif countNeg > countPos:
                newLineB4OpenBrace = 0
            else:
                newLineB4OpenBrace = 2
            #print(newLineB4OpenBrace)
            return newLineB4OpenBrace

        def getTabsLeadLines(code):
            tabsLeadLines = 2
            countTabs = 0
            countSpaces = 0
            x = 0
            while x < len(code)-1:
                if code[x] == "\n":
                    if code[x+1] == " ":
                        countSpaces += 1
                    elif code[x+1] == "\t":
                        countTabs += 1
                x = x + 1
            if countSpaces > countTabs:
                tabsLeadLines = 0
            elif countTabs > countSpaces:
                tabsLeadLines = 1
            #print(tabsLeadLines)
            return tabsLeadLines


        def get_layout_feature_counts(code):
            layout_feature_counts = []

            if len(code) > 0:
                lnNumTabs = getLnNumTabs(code)
                #print("numtabs")
                lnNumSpaces = getLnNumSpaces(code)
                #print("numspaces")
                lnEmptyLines = getLnEmptyLines(code)
                whiteSpaceRatio = getWhiteSpaceRatio(code)
                #print("ratio")
                newLineB4OpenBrace = getNewLineB4OpenBrace(code)
                #print("newline")
                tabsLeadLines = getTabsLeadLines(code)
                #print("tabs")

                layout_feature_counts.append(lnNumTabs)
                layout_feature_counts.append(lnNumSpaces)
                layout_feature_counts.append(lnEmptyLines)
                layout_feature_counts.append(whiteSpaceRatio)
                layout_feature_counts.append(newLineB4OpenBrace)
                layout_feature_counts.append(tabsLeadLines)

            return layout_feature_counts

        def getLnKeywordIf(code):
            lnKeyword = 0
            count = code.count(" if ")+code.count(" if(")
            try:
                lnKeyword = math.log(count/len(code))
            except Exception as e:
                pass
            return lnKeyword

        def getLnKeywordDo(code):
            lnKeyword = 0
            count = code.count(" do ")+code.count(" do{")
            try:
                lnKeyword = math.log(count/len(code))
            except Exception as e:
                pass
            return lnKeyword

        def getLnKeywordElseif(code):
            lnKeyword = 0
            count = code.count("else if ")+code.count("else if(")
            try:
                lnKeyword = math.log(count/len(code))
            except Exception as e:
                pass
            return lnKeyword

        def getLnKeywordElse(code):
            lnKeyword = 0
            count = code.count("else {")+code.count("else{")+code.count("else\n{")
            try:
                lnKeyword = math.log(count/len(code))
            except Exception as e:
                pass
            return lnKeyword

        def getLnKeywordSwitch(code):
            lnKeyword = 0
            count = code.count("switch(")+code.count("switch (")+code.count("switch\n(")
            try:
                lnKeyword = math.log(count/len(code))
            except Exception as e:
                pass
            return lnKeyword

        def getLnKeywordFor(code):
            lnKeyword = 0
            count = code.count(" for (")+code.count(" for(")
            try:
                lnKeyword = math.log(count/len(code))
            except Exception as e:
                pass
            return lnKeyword

        def getLnKeywordWhile(code):
            lnKeyword = 0
            count = code.count(" while (")+code.count(" while(")
            try:
                lnKeyword = math.log(count/len(code))
            except Exception as e:
                pass
            return lnKeyword

        def getLnNumTernary(code):
            lnNumTernary = 0
            count = code.count(" ? ")
            try:
                lnNumTernary = math.log(count/len(code))
            except Exception as e:
                pass
            return lnNumTernary

        def getLnNumTokens(code):
            lnNumTokens = 0
            codesplit = code.split(" ")
            count = len(codesplit)
            try:
                lnNumTokens = math.log(count/len(code))
            except Exception as e:
                pass
            return lnNumTokens

        def getLnNumComments(code):
            lnNumComments = 0
            count = code.count("/*")
            try:
                lnNumComments = math.log(count/len(code))
            except Exception as e:
                pass
            return lnNumComments

        def getLnNumLiterals(code):
            lnNumLiterals = 0
            count = code.count(" int ")+code.count(" String ")+code.count(" char ")+code.count(" double ")+code.count(" long ")
            try:
                lnNumLiterals = math.log(count/len(code))
            except Exception as e:
                pass
            return lnNumLiterals

        def getLnNumKeywords(code):
            lnNumKeywords = 0
            keywords = [' asm ',' auto ',' bool ',' break ',' case ',' catch ',' char ',' class ',' const ',' continue ',' default ',' delete ',' do ',' double ',' else ',' enum ',' explicit ',' export ',' extern ',' false ',' float ',' for ',' friend ',' goto ',' if ',' inline ',' int ',' long ',' mutable ',' namespace ',' new ',' operator ',' private ',' protected ',' public ',' register ',' return ',' short ',' signed ',' sizeof ',' static ',' struct ',' switch ',' template ',' this ',' throw ',' true ',' try ',' typedef ',' typeid ',' typename ',' union ',' unsigned ',' using ',' virtual ',' void ',' volatile ',' wchar_t ',' while ']
            count = 0
            for word in keywords:
                count += code.count(word)
            try:
                lnNumKeywords = math.log(count/len(code))
            except Exception as e:
                pass
            return lnNumKeywords

        def getLnNumFunctions(code): #this is supposed to get functions. This requires fuzzy parsing.
            lnNumFunctions = 0
            count = code.count(" int ")+code.count(" String ")+code.count(" char ")+code.count(" double ")+code.count(" long ")
            try:
                lnNumFunctions = math.log(count/len(code))
            except Exception as e:
                pass
            return lnNumFunctions

        def getLnNumMacros(code): #this is supposed to get preprocessor directives. I strip these from the code to aid in fuzzy parsing.
            lnNumTernary = 0
            count = code.count(" int ")+code.count(" String ")+code.count(" char ")+code.count(" double ")+code.count(" long ")
            try:
                lnNumTernary = math.log(count/len(code))
            except Exception as e:
                pass
            return lnNumTernary

        def getNestingDepth(code):
            count = 0

            def maxDepth(S):
                current_max = 0
                max = 0
                n = len(S)
                # Traverse the input string
                for i in range(n):
                    if S[i] == '{':
                        current_max += 1

                        if current_max > max:
                            max = current_max
                    elif S[i] == '}':
                        if current_max > 0:
                            current_max -= 1
                        else:
                            return -1
                # finally check for unbalanced string
                if current_max != 0:
                    return -1

                return max

            count = maxDepth(code)

            return count

        def getAvgLineLength(code):
            avgLineLength = 0
            codesplit = code.split("\n")
            lengths = []
            sumLengths = 0
            for line in codesplit:
                lengths.append(len(line))
                sumLengths += len(line)

            avgLineLength = sumLengths/len(lengths)

            return avgLineLength

        def getStdDevLineLength(code):
            avgLineLength = 0
            codesplit = code.split("\n")
            lengths = []
            sumLengths = 0
            for line in codesplit:
                lengths.append(len(line))
                sumLengths += len(line)

            avgLineLength = sumLengths/len(lengths)
            intermed = [None]*len(lengths)
            x = 0
            while x < len(lengths):
                intermed[x] = (lengths[x] - avgLineLength)**2
                x = x + 1

            stdDev = 0
            sumIntermeds = 0
            for elem in intermed:
                sumIntermeds += elem
            stdDev = sumIntermeds/len(intermed)

            return stdDev

        def getLnNumFunctions(code):
            lnNumFunctions = 0
            instances = re.findall("(void|int|char|short|long|float|double)\s+(\w+)\s*\([^)]*\)\s*;",str(code))
            #for instance in instances:  #debugging purposes
            #    print(instance)
            count = len(instances)
            try:
                lnNumFunctions = math.log(count/len(code))
            except Exception as e:
                pass
            return lnNumFunctions

        def getImportantKeywordCounts(code):
            global important_keywords
            keyword_counts = [0]*len(important_keywords)
            x = 0
            while x < len(important_keywords):
                if important_keywords[x] in code:
                    keyword_counts[x] = code.count(important_keywords[x])
                x = x + 1

            return keyword_counts


        def get_lexical_feature_counts(code):
            lexical_feature_counts = []

            if len(code) > 0:

                #word unigram frequency is missing. implement this somewhere else I think

                lnKeywordIf = getLnKeywordIf(code)
                lnKeywordDo = getLnKeywordDo(code)
                lnKeywordElseif = getLnKeywordElseif(code)
                lnKeywordElse = getLnKeywordElse(code)
                lnKeywordSwitch = getLnKeywordSwitch(code)
                lnKeywordFor = getLnKeywordFor(code)
                lnKeywordWhile = getLnKeywordWhile(code)

                lnNumTernary = getLnNumTernary(code)
                lnNumTokens = getLnNumTokens(code)
                lnNumComments = getLnNumComments(code)
                lnNumLiterals = getLnNumLiterals(code)
                lnNumKeywords = getLnNumKeywords(code)
                lnNumFunctions = getLnNumFunctions(code) #use the ast for this
                #lnNumMacros = getLnNumMacros(code) #use the ast for this
                nestingDepth = getNestingDepth(code)
                #branchingFactor = getBranchFactor(code) #use the ast for this
                #avgParams = getAvgParams(code) #use the ast for this
                #stdDevNumParams = getStdDevNumParams(code) #use the ast for this
                avgLineLength = getAvgLineLength(code)
                stdDevLineLength = getStdDevLineLength(code)
                important_keyword_counts = getImportantKeywordCounts(code)

                lexical_feature_counts.append(lnKeywordIf)
                lexical_feature_counts.append(lnKeywordDo)
                lexical_feature_counts.append(lnKeywordElseif)
                lexical_feature_counts.append(lnKeywordElse)
                lexical_feature_counts.append(lnKeywordSwitch)
                lexical_feature_counts.append(lnKeywordFor)
                lexical_feature_counts.append(lnKeywordWhile)

                lexical_feature_counts.append(lnNumTernary)
                lexical_feature_counts.append(lnNumTokens)
                lexical_feature_counts.append(lnNumComments)
                lexical_feature_counts.append(lnNumLiterals)
                lexical_feature_counts.append(lnNumKeywords)
                lexical_feature_counts.append(lnNumFunctions)
                #lexical_feature_counts.append(lnNumMacros)
                lexical_feature_counts.append(nestingDepth)
                #lexical_feature_counts.append(branchingFactor)
                #lexical_feature_counts.append(avgParams)
                #lexical_feature_counts.append(stdDevNumParams)
                lexical_feature_counts.append(avgLineLength)
                lexical_feature_counts.append(stdDevLineLength)
                #lexical_feature_counts = lexical_feature_counts + important_keyword_counts

            return lexical_feature_counts

        def calculate_tfs(list_of_type_counts):
            tfs = [0] * len(list_of_type_counts)
            total_number_of_terms_in_document = 1
            for item in list_of_type_counts:
                total_number_of_terms_in_document += item
            x = 0
            while x < len(list_of_type_counts):
                tfs[x] = list_of_type_counts[x]/total_number_of_terms_in_document
                x = x + 1
            return tfs

        def calculate_idfs(list_of_type_counts,number_of_documents_with_nodetype,number_of_documents):
            idfs = [0]*len(list_of_type_counts)
            x = 0
            while x < len(list_of_type_counts):
                if number_of_documents_with_nodetype[x] == 0:
                    idfs[x] = 0
                else:
                    idfs[x] = math.log(number_of_documents/number_of_documents_with_nodetype[x])
                x = x + 1

            return idfs

        def calculate_nodetype_tfidf(source_for_node_types):
            number_of_documents_with_nodetype = [0]*57
            number_of_nodetypes = 57
            j = 0
            while j < number_of_nodetypes:
                i = 0
                while i < len(source_for_node_types):
                    if source_for_node_types['code'][i][j] > 0:
                        number_of_documents_with_nodetype[j] += 1
                    i = i + 1
                j = j + 1

            number_of_documents = len(source_for_node_types)
            x = 0
            while x < len(source_for_node_types):
                tfs = calculate_tfs(source_for_node_types['code'][x])
                idfs = calculate_idfs(source_for_node_types['code'][x],number_of_documents_with_nodetype,number_of_documents)
                tfidfs = [0]*len(source_for_node_types['code'][x])
                y = 0
                while y < len(tfs):
                    tfidfs[y] = tfs[y]*idfs[y]
                    y = y + 1
                source_for_node_types['code'][x] = tfidfs
                x = x + 1
            return source_for_node_types


        def populate_word_unigrams(source_for_wordunigrams):
            word_unigrams = set([])

            y = 0
            while y < len(source_for_wordunigrams['code']):
                code = source_for_wordunigrams['code'][y]
                #print(len(code))

                string = str(code)
                firstDelPos=string.find("/*") # get the position of */
                secondDelPos=string.find("*/") # get the position of */
                code = string.replace(string[firstDelPos+1:secondDelPos], "")

                codesplit = code.split(" ")

                for elem in codesplit:
                    word_unigrams.add(elem)

                y = y + 1

            return word_unigrams

        path = self.root+output_file
        source_for_layout = []
        source_for_lexical = []
        source_for_syntactical = []
        source_for_node_types = []
        if os.path.exists(path) and option == 'existing':
            source = pd.read_pickle(path)
            source_for_layout = copy.deepcopy(source)
            source_for_layout.columns = ['id', 'code', 'label', 'filename']
            source_for_lexical = copy.deepcopy(source)
            source_for_lexical.columns = ['id','code','label','filename']
            source_for_wordunigrams = copy.deepcopy(source)
            source_for_wordunigrams.columns = ['id','code','label','filename']
            source_for_syntactical = copy.deepcopy(source)
            source_for_syntactical.columns = ['id','code','label','filename']

            print("Getting layout features...")
            y = 0
            while y < len(source_for_layout['code']):
                #print(y)
                layout_feature_counts = get_layout_feature_counts(source_for_layout['code'][y])
                source_for_layout['code'][y] = layout_feature_counts
                if(y % 100 == 0):
                    print(y)
                y = y + 1
            print("Done.")

            print("Getting lexical features...")
            y = 0
            while y < len(source_for_lexical['code']):
                #print(y)
                lexical_feature_counts = get_lexical_feature_counts(source_for_lexical['code'][y])
                source_for_lexical['code'][y] = lexical_feature_counts
                if(y % 100 == 0):
                    print(y)
                y = y + 1
            print("Done.")

            source.columns = ['id', 'code', 'label', 'filename']

            word_unigrams = []
            word_unigrams = populate_word_unigrams(source_for_wordunigrams)
            source.to_pickle(path)
            layout_data_path = "/home/k1462425/Documents/Research/ast_bigram_approach/data/source_for_layout.pkl"
            source_for_layout.to_pickle(layout_data_path)
            lexical_data_path = "/home/k1462425/Documents/Research/ast_bigram_approach/data/source_for_lexical.pkl"
            source_for_lexical.to_pickle(lexical_data_path)
            wordunigrams_data_path = "/home/k1462425/Documents/Research/ast_bigram_approach/data/source_for_wordunigrams.pkl"
            source_for_wordunigrams.to_pickle(wordunigrams_data_path)
        else:
            source = pd.read_pickle(self.root+self.source_code_input)
            source_for_layout = copy.deepcopy(source)
            source_for_layout.columns = ['id', 'code', 'label','filename']
            source_for_lexical = copy.deepcopy(source)
            source_for_lexical.columns = ['id','code','label','filename']
            source_for_wordunigrams = copy.deepcopy(source)
            source_for_wordunigrams.columns = ['id','code','label','filename']
            source_for_syntactical = copy.deepcopy(source)
            source_for_syntactical.columns = ['id','code','label','filename']
            source_for_node_types = copy.deepcopy(source)
            source_for_node_types.columns = ['id','code','label','filename']
            source_for_nodetype_tfidf = copy.deepcopy(source)
            source_for_nodetype_tfidf.columns = ['id','code','label','filename']

            print("Getting layout features...")
            y = 0
            while y < len(source_for_layout['code']):
                #print(y)
                layout_feature_counts = get_layout_feature_counts(source_for_layout['code'][y])
                source_for_layout['code'][y] = layout_feature_counts
                if(y % 100 == 0):
                    print(y)
                y = y + 1
            print("Done.")

            print("Getting lexical features...")
            y = 0
            while y < len(source_for_lexical['code']):
                #print(y)
                lexical_feature_counts = get_lexical_feature_counts(source_for_lexical['code'][y])
                source_for_lexical['code'][y] = lexical_feature_counts
                if(y % 100 == 0):
                    print(y)
                y = y + 1
            print("Done.")

            source.columns = ['id', 'code', 'label','filename']

            word_unigrams = []
            word_unigrams = populate_word_unigrams(source_for_wordunigrams)

            print("Getting AST features...")
            import time
            x = 0
            while x < len(source['code']):

                if os.path.exists(JOERN_INPUT_PATH+"program.cpp"):
                    os.remove(JOERN_INPUT_PATH+"program.cpp")
                if os.path.exists(JOERN_INPUT_PATH+".joernIndex"):
                    rmtree(JOERN_INPUT_PATH+".joernIndex")

                filename = JOERN_INPUT_PATH+"program.cpp"
                with open(filename,'w+') as fp:
                    fp.write(source['code'][x])
                    fp.close()

                #print(source['code'][x])

                subprocess.call(['java', '-jar', JOERN_JAR_PATH, JOERN_INPUT_PATH],cwd=JOERN_INPUT_PATH)
                subprocess.call([NEO4J_BIN_PATH,'start-no-wait'])
                time.sleep(6)
                all_nodes_string, ast_features = produce_nodes_string()
                subprocess.call([NEO4J_BIN_PATH,'stop'])
                subprocess.call(['rm', '-r', JOERN_INPUT_PATH+".joernIndex"])
                subprocess.call(['rm', '-r', JOERN_INPUT_PATH+"program.cpp"])

                source_for_node_types['code'][x] = ast_features

                source['code'][x] = all_nodes_string
                #if(x % 100 == 0):
                print(x)
                x = x + 1
            print("Done.")

            source_for_nodetype_tfidf = calculate_nodetype_tfidf(source_for_node_types)
            print(source_for_nodetype_tfidf)

            x = 0
            while x < len(source_for_nodetype_tfidf):
                source_for_nodetype_tfidf['code'][x] = source_for_nodetype_tfidf['code'][x] + source_for_node_types['code'][x]
                x = x + 1

            source.to_pickle(path)
            layout_data_path = "/home/k1462425/Documents/Research/ast_bigram_approach/data/source_for_layout.pkl"
            source_for_layout.to_pickle(layout_data_path)
            lexical_data_path = "/home/k1462425/Documents/Research/ast_bigram_approach/data/source_for_lexical.pkl"
            source_for_lexical.to_pickle(lexical_data_path)
            wordunigrams_data_path = "/home/k1462425/Documents/Research/ast_bigram_approach/data/source_for_wordunigrams.pkl"
            source_for_wordunigrams.to_pickle(wordunigrams_data_path)
            syntactical_data_path = "/home/k1462425/Documents/Research/ast_bigram_approach/data/source_for_nodetype_tfidf.pkl"
            source_for_nodetype_tfidf.to_pickle(syntactical_data_path)
            #with open('/home/k1462425/Documents/Research/ast_bigram_approach/data/ast_node_types.pkl', 'wb') as f:
            #    pickle.dump(global_node_types, f)

        self.sources_for_layout = source_for_layout
        self.sources_for_lexical = source_for_lexical
        self.sources_for_wordunigrams = source_for_wordunigrams
        self.sources_for_syntactical = source_for_nodetype_tfidf
        self.sources = source

        return source

    # split data for training, developing and testing
    def split_data(self):
        data_path = self.root+'/'
        data = self.sources
        data_num = len(data)
        ratios = [int(r) for r in self.ratio.split(':')]
        train_split = int(ratios[0]/sum(ratios)*data_num)
        val_split = train_split + int(ratios[1]/sum(ratios)*data_num)

        data = data.sample(frac=1, random_state=666)
        train = data.iloc[:train_split]
        dev = data.iloc[train_split:val_split]
        test = data.iloc[val_split:]

        def check_or_create(path):
            if not os.path.exists(path):
                os.mkdir(path)
        train_path = data_path+'train/'
        check_or_create(train_path)
        self.train_file_path = train_path+'train_.pkl'
        train.to_pickle(self.train_file_path)

    # construct dictionary and train word embedding
    def dictionary_and_embedding(self, input_file, size):

        # Function to convert a char list to a string
        def listToString(s):
            str1 = ""
            for ele in s:
                str1 += ele
            return str1

        def findChildren(node,entry):
            nodeSplit = node.split(",")
            children = []
            node_identifier = nodeSplit[0]
            entry_split = entry.split("¬")
            for entry_x in entry_split:
                node_split = entry_x.split(",")
                if node_split[-1] == node_identifier:
                    children.append(entry_x)
            return children

        def find_parent(node, all_nodes_string):
            all_nodes_split = all_nodes_string.split('¬')
            node_split = node.split(',')
            parent_identifier = node_split[-1]
            parent = ""
            for nod in all_nodes_split:
                nod_split = nod.split(',')
                if nod_split[0] == parent_identifier:
                    parent = nod
            return parent

        self.size = size
        if not input_file:
            input_file = self.train_file_path
        trees = pd.read_pickle(input_file)
        if not os.path.exists(self.root+'train/embedding'):
            os.mkdir(self.root+'train/embedding')

        def preprocess_trees(code):
            global transIndex2
            trees1 = []

            if transIndex2 % 10 == 0:
                print(transIndex2)

            code_split = code.split('¬')
            code = []
            for elem in code_split:
                if len(elem) > 0:
                    node_split = elem.split(',')
                    new_node = node_split[1] #gets rid of node identifier and node depth and parent identifier
                    new_node_string = ''
                    for info in new_node:
                        if info != '' and '.' not in info:
                            code.append(info)

            transIndex2 = transIndex2 + 1

            return code

        def preprocess_trees_bigrams(code):
            global transIndex
            bigrams = []
            code_split = code.split('¬')
            #print(code)
            if transIndex % 10 == 0:
                print(transIndex)

            for elem in code_split:
                if len(elem) > 0:
                    #print(elem)
                    #print(len(elem))
                    elem_truncated = elem.split(',')[1]
                    if not elem_truncated in nodesDone:
                        bigram = get_bigram(elem,code)
                        if len(bigram) > 1:
                            nodesDone.append(bigram[0])
                            nodesDone.append(bigram[1])
                            bigram[0] = tuple(bigram[0])
                            bigram[1] = tuple(bigram[1])
                            bigram = tuple(bigram)
                            bigram = hash(bigram)
                            bigrams.append(str(bigram))

            transIndex = transIndex + 1

            return bigrams

        def get_token(node):
            return node.split(',')[1]

        def get_bigram(node,entry):
            children = findChildren(node,entry)
            bigram = []
            nodeSplit = node.split(',')
            newNode = nodeSplit[1]
            new_node_string = ''
            code = []
            if len(newNode) > 0:
                code.append(newNode)

            bigram.append(code)

            code = []
            if len(children) != 0:
                nodeSplit = children[0].split(',')
                newNode = nodeSplit[1]
                new_node_string = ''
                if len(newNode) > 0:
                    code.append(newNode)

                bigram.append(code)

            return bigram

        nodesDone = []

        print("Making copy of trees...")
        trees_copy = copy.deepcopy(trees['code'])
        print("Done.")
        print("Applying preprocessing...")
        corpus = trees_copy.apply(preprocess_trees_bigrams)
        print("After preprocessing trees bigrams:")
        print(corpus)
        tosave = []

        x = 0
        while x < len(corpus):
            if len(corpus[x]) == 0:
                tosave.append(str(x))
            x = x + 1

        print("To save:")
        print(tosave)

        with open("/home/k1462425/Documents/Research/ast_bigram_approach/data/empty_ast_entries.txt",'w') as fp:
            fp.writelines(tosave)

        print("Done.")
        self.corpo = corpus
        #print("Applying preprocessing 2...")
        #orig_corpus = trees['code'].apply(preprocess_trees)
        #print("Done.")
        trees.to_csv(self.root+'train/programs_ns.tsv')

        from gensim.models.word2vec import Word2Vec
        w2v = Word2Vec(corpus, size=size, workers=16, sg=1, min_count=3)
        w2v.save(self.root+'train/embedding/node_w2v_' + str(size))

    # generate block sequences with index representations
    def generate_block_seqs(self,data_path,part):
        from prepare_data_clang_rewritten import get_blocks as func
        from gensim.models.word2vec import Word2Vec
        global transIndex, transIndex2
        word2vec = Word2Vec.load(self.root+'train/embedding/node_w2v_' + str(self.size)).wv
        vocab = word2vec.vocab
        max_token = word2vec.syn0.shape[0]
        nodesDone = []
        transIndex = 0
        transIndex2 = 0

        def findChildren(node,entry):
            nodeSplit = node.split(",")
            children = []
            node_identifier = nodeSplit[0]
            entry_split = entry.split("¬")
            for entry_x in entry_split:
                node_split = entry_x.split(",")
                if node_split[-1] == node_identifier:
                    children.append(entry_x)
            return children

        def get_bigram(node,entry):
            children = findChildren(node,entry)
            bigram = []
            nodeSplit = node.split(',')
            if len(nodeSplit) > 1:
                #print(nodeSplit)
                newNode = nodeSplit[1]
                new_node_string = ''
                code = []
                if len(newNode) > 0:
                    code.append(newNode)

                bigram.append(code)
                code = []
                if len(children) != 0:
                    nodeSplit = children[0].split(',')
                    newNode = nodeSplit[1]
                    new_node_string = ''
                    if len(newNode) > 0:
                        code.append(newNode)

                    bigram.append(code)

            return bigram


        def tree_to_index(node):
            token = node.token
            result = [vocab[token].index if token in vocab else max_token]
            children = node.children
            for child in children:
                result.append(tree_to_index(child))
            return result

        def preprocess_trees_bigrams(code):
            bigrams = []
            code_split = code.split('¬')


            for elem in code_split:
                if len(elem) > 0:
                    elem_truncated = elem.split(',')[1]
                    if not elem_truncated in nodesDone:
                        bigram = get_bigram(elem,code)
                        if len(bigram) > 1:
                            nodesDone.append(bigram[0])
                            nodesDone.append(bigram[1])
                            bigram[0] = tuple(bigram[0])
                            bigram[1] = tuple(bigram[1])
                            bigram = tuple(bigram)
                            bigram = hash(bigram)
                            tokenNumber = vocab[str(bigram)].index if str(bigram) in vocab else max_token
                            bigrams.append(tokenNumber)

            return bigrams

        def get_token(node):
            return node.split(',')[1]

        trees = pd.read_pickle(data_path)
        print("BEFORE:")
        print(trees['code'])

        print("Hashing bigrams...")
        trees['code'] = trees['code'].apply(preprocess_trees_bigrams)
        #trees['code'] = self.corpo
        print("Done.")
        print("AFTER:")
        print(trees['code'])

        print("Number of bigrams: "+str(max_token))

        bigram_hashes_and_indices = {}
        for elem in vocab:
            bigram_hashes_and_indices[elem] = vocab[elem].index

        x = 0
        while x < len(trees['code']):
            lexical_feature_counts = self.sources_for_lexical['code'][x]
            y = 0
            while y < len(lexical_feature_counts):
                trees['code'][x] = [lexical_feature_counts[y]]+trees['code'][x]
                y = y + 1
            x = x + 1

        x = 0
        while x < len(trees['code']):
            layout_feature_counts = self.sources_for_layout['code'][x]
            y = 0
            while y < len(layout_feature_counts):
                trees['code'][x] = [layout_feature_counts[y]]+trees['code'][x]
                y = y + 1
            x = x + 1

        print("SOURCES FOR SYNTACTICAL:")
        ids_of_zeroed = []
        serial_indices_of_zeroed = []
        x = 0
        while x < len(self.sources_for_syntactical['code']):
            vector = self.sources_for_syntactical['code'][x]
            nonzero = False
            for elem in vector:
                if elem != 0.0:
                    nonzero = True
            if nonzero == False:
                ids_of_zeroed.append(self.sources_for_syntactical['id'][x])
                serial_indices_of_zeroed.append(x)
            x = x + 1


        print(self.sources_for_syntactical)

        print("Ids of zeroed")
        print(ids_of_zeroed)

        print("Serial indices of zeroed")
        print(serial_indices_of_zeroed)
        x = 0
        while x < len(trees['code']):
            syntactical_feature_counts = self.sources_for_syntactical['code'][x]
            y = 0
            while y < len(syntactical_feature_counts):
                trees['code'][x] = [syntactical_feature_counts[y]]+trees['code'][x]
                y = y + 1
            x = x + 1


        corpus = self.sources_for_wordunigrams['code']

        #print("Length of contextual vector:")
        #print(len(self.sources_for_contextual['code'][0]))

        print("Length of syntactical (minus bigrams) vector:")
        print(len(self.sources_for_syntactical['code'][0]))

        print("Length of layout vector:")
        print(len(self.sources_for_layout['code'][0]))

        print("Length of lexical vector:")
        print(len(self.sources_for_lexical['code'][0]))

        w2v2 = Word2Vec(corpus, size=128, workers=16, sg=1, min_count=3)
        w2v2.save(self.root+'train/embedding/wu_w2v_128')
        w2v2 = Word2Vec.load(self.root+'train/embedding/wu_w2v_128').wv
        vocab2 = w2v2.vocab
        max_token_wu = w2v2.syn0.shape[0]

        def get_wu_token_numbers(code):
            tokens = []
            for elem in code:
                tokens.append((vocab2[elem].index + max_token) if elem in vocab2 else (max_token_wu + max_token))
            return tokens

        print("Hashing word unigrams...")
        corpus = corpus.apply(get_wu_token_numbers)
        print("Done.")
        print("WU TOKENS:--------------------")
        print(corpus)
        print("Number of word unigrams: "+str(max_token_wu))

        x = 0
        while x < len(corpus):
            per_sample_wu = corpus[x]
            y = 0
            while y < len(per_sample_wu):
                trees['code'][x].append(per_sample_wu[y])
                y = y + 1
            x = x + 1


        with open('./data/bigram_hashes_and_indices.pkl', 'wb') as handle:
            pickle.dump(bigram_hashes_and_indices, handle, protocol=pickle.HIGHEST_PROTOCOL)

        print("Trees that will be pickled:")
        print(trees)
        for elem in serial_indices_of_zeroed:
            trees = trees.drop(elem)
        print("Trees after removing zeros:")
        print(trees)


        trees.to_pickle(self.root+part+'/blocks.pkl')


    # run for processing data to train
    def run(self):
        print('parse source code...')
        self.parse_source(output_file='ast.pkl',option='existing')
        print('split data...')
        self.split_data()
        print('train word embedding...')
        self.dictionary_and_embedding(None,128)
        print('generate block sequences...')
        self.generate_block_seqs(self.train_file_path, 'train')


parser = argparse.ArgumentParser(description="Specify the source code pickle file.")
parser.add_argument('--source')
args = parser.parse_args()
if not args.source:
    print("No specified source code pickle file.")
    exit(1)
ppl = Pipeline('1:0:0', 'data/', args.source)
ppl.run()
