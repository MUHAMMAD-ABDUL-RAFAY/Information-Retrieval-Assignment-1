import os
import glob
import re
import string
from nltk.stem import PorterStemmer
import re
from flask import Flask, request, render_template,jsonify

stopwords = []
dictionary = {}

def read_stopwords(filename):
    file_read = open(filename,'r')
    content = file_read.read();
    file_read.close()
    stopwords = content.split('\n')
    return stopwords    

def tokenize(content):
    content = content.lower()
    content = content.replace("-", " ")
    content = content.replace("•"," ")
    content = content.translate(str.maketrans("", "", string.punctuation))
    words = re.split(r'\s+|\n+', content)
    stemmer = PorterStemmer()
    words = [stemmer.stem(word) for word in words]
    return words

def read_all_files(stopwords):
    
    folder_path = 'CricketReviews\Dataset'
    file_pattern = '*.txt'

    #Use glob to find all files that match the pattern in the folder
    file_list = glob.glob(os.path.join(folder_path, file_pattern))
    
    #Loop over each file in the list and read its contents
    for file_path in file_list:
        with open(file_path, 'r') as file:
            contents = file.read()
            file_name = file_path.strip("CricketReviews\\Dataset\\.txt")
            
            #tokenize takes content and stopwords as a parameter and create tokens by first lowercasing the words
            #and then removing the punctuations and removes the stopwords and returns list of tokens
            words = tokenize(contents)
            
            #this for loop creates the inverted index from list of tokens and create a key-value pair
            for pos,word in enumerate(words):
                if word not in stopwords:
                    if word not in dictionary:
                        dictionary[word] = [] 
                        dictionary[word] = {int(file_name):[int(pos)]}
                    else:
                        if int(file_name) not in dictionary[word]:
                            dictionary[word][int(file_name)] = [int(pos)]
                        else:
                            dictionary[word][int(file_name)].append(int(pos))
            file.close()

    return dictionary
            
def sort_dictionary(dictionary):
    #it accepts the dictionary and sort the dictionary
    sorted_dict = {k: dict(sorted(value.items(),key=lambda x: (x[0],sorted(x[1])))) for k, value in sorted(dictionary.items())}
    return sorted_dict

def unionAND(w1,w2):
    #it accepts the two words check if its a list or word if word then fetch its posting list and if word not in dictionary return an empty list other wise perform the AND operation on two lists and return the list of relevant docs
    result = list()
    if type(w1) != str and type(w2) != str:
        w1_postinglist = w1
        w2_postinglist = w2
    elif type(w1) != str or type(w2) != str:
        if type(w2) != str:
            if w1 not in dictionary:
                return []
            w1,w2 = w2,w1
        else:
            if w2 not in dictionary:
                return []
        w1_postinglist = w1
        w2_postinglist = list(dictionary[w2].keys())
    else:
        if w1 not in dictionary or w2 not in dictionary:
            return []
        w1_postinglist = list(dictionary[w1].keys())
        w2_postinglist = list(dictionary[w2].keys())
    i = 0
    j = 0
    while i < len(w1_postinglist) and j < len(w2_postinglist):
        if(w1_postinglist[i] == w2_postinglist[j]):
            result.append(w1_postinglist[i])
            i += 1
            j += 1
        elif w1_postinglist[i] < w2_postinglist[j]:
            i += 1
        else:
            j += 1
    return result

def processANDonlyquery(expression):   
    #it accepts the expression and extract words from it normalize it removing punctuations and stemming and pass words in pair to unionAND for processing
    num_AND = [e for e in expression if e == 'AND']
    words = [e for e in expression if e != 'AND']
    words = [word.lower() for word in words]
    translator = str.maketrans('','',string.punctuation)
    words = [word.translate(translator) for word in words]
    stemmer = PorterStemmer()
    words = [stemmer.stem(word) for word in words if word not in ['AND']]
    result = []
    word1 = words[0]
    for i in range(1,len(words)):
        word2 = words[i]
        result = unionAND(word1,word2)
        word1 = result
    return result

def unionOR(w1,w2):
    #it accepts the two words check if its a list or word if word then fetch its posting list and if word not in dictionary return posting list of the non empty word other wise perform the OR operation on two lists and return the list of relevant docs
    result = list()
    if type(w1) != str and type(w2) != str:
        w1_postinglist = w1
        w2_postinglist = w2
    elif type(w1) != str or type(w2) != str:
        if type(w2) != str:
            if w1 not in dictionary:
                return w2
            w1,w2 = w2,w1
        else:
            if w2 not in dictionary:
                return w1
        w1_postinglist = w1
        w2_postinglist = list(dictionary[w2].keys())
    else:
        if w1 not in dictionary and w2 not in dictionary:
            return []
        elif w1 not in dictionary:
            return list(dictionary[w2].keys())
        elif w2 not in dictionary:
            return list(dictionary[w1].keys())
        w1_postinglist = list(dictionary[w1].keys())
        w2_postinglist = list(dictionary[w2].keys())
    i = 0
    j = 0
    while i < len(w1_postinglist) and j < len(w2_postinglist):
        if(w1_postinglist[i] == w2_postinglist[j]):
            result.append(w1_postinglist[i])
            i += 1
            j += 1
        elif w1_postinglist[i] < w2_postinglist[j]:
            result.append(w1_postinglist[i])
            i += 1
        else:
            result.append(w2_postinglist[j])
            j += 1
    if i < len(w1_postinglist):
        while i < len(w1_postinglist):
            result.append(w1_postinglist[i])
            i += 1
    if j < len(w2_postinglist):
        while j < len(w2_postinglist):
            result.append(w2_postinglist[j])
            j += 1
    return result
def processORonlyquery(expression):
    #it accepts the expression and extract words from it normalize it removing punctuations and stemming and pass words in pair to unionOR for processing 
    num_OR = [e for e in expression if e == 'OR']
    words = [e for e in expression if e != 'OR']
    words = [word.lower() for word in words]
    translator = str.maketrans('','',string.punctuation)
    words = [word.translate(translator) for word in words]
    stemmer = PorterStemmer()
    words = [stemmer.stem(word) for word in words if word not in ['OR']]

    result = []
    word1 = words[0]
    for i in range(1,len(words)):
        word2 = words[i]
        result = unionOR(word1,word2)
        word1 = result
    return result

def unionNOT(word):
        #it checks if the word is a string or list and on that basis performs the negate operation if word fetch it posting list and negate
        result = []
        if type(word) != str:
            for i in range (1,31):
                if(i not in word):
                    result.append(i)
        else:
            if word not in dictionary:
                return [i for i in range(1,31)]
            word_postinglist = list(dictionary[word].keys())
            i = 1
            for doc in word_postinglist:
                while i < doc:
                    result.append(i)
                    i += 1
                i += 1
            if i < 30:
                while i <= 30:
                    result.append(i)
                    i += 1
        return result 
def processNOTonlyquery(expression):
    #it accepts the expression and extract words from it normalize it removing punctuations and stemming and pass to unionNOT for processing
    num_NOT = [e for e in expression if e == 'NOT']
    words = [e for e in expression if e != 'NOT']
    words = [word.lower() for word in words]
    translator = str.maketrans('','',string.punctuation)
    words = [word.translate(translator) for word in words]
    stemmer = PorterStemmer()
    words = [stemmer.stem(word) for word in words if word not in ['NOT']]
    result = []
    result = unionNOT(words[0])
    return result


def unionphrasalquery(word1,word2,proximity):
    #it accepts the two params word1,word2 and checks there type if string checks it in dictionary and fetch its posting list else not in dictionary return empty list
    result = dict()
    if type(word1) != str:

        w1_postinglist = list(word1.keys())
        w1_positional_postinglist = list(word1.values())
        
        w2_postinglist = list(dictionary[word2].keys())
        w2_positional_postinglist = list(dictionary[word2].values())
        i = 0
        j = 0
        #it checks first words must exist in same doc if yes then checks the proximity if lies within the proximity then adds to the result
        while i < len(w1_postinglist) and j < len(w2_postinglist):
            if(w1_postinglist[i] == w2_postinglist[j]):
                k = 0
                l = 0
                while k < len(w1_positional_postinglist[i]) and l < len(w2_positional_postinglist[j]):
                    if abs(w1_positional_postinglist[i][k] - w2_positional_postinglist[j][l]) <= proximity:
                        if w1_positional_postinglist[i][k] < w2_positional_postinglist[j][l]:
                            if w1_postinglist[i] not in result:
                                result[w1_postinglist[i]] = [w2_positional_postinglist[j][l]]
                            else:
                                result[w1_postinglist[i]].append(w2_positional_postinglist[j][l])
                        else:
                            if w1_positional_postinglist[i] not in result:
                                result[w1_postinglist[i]] = [w1_positional_postinglist[i][k]]
                            else:
                                result[w1_postinglist[i]].append(w1_positional_postinglist[i][k])
                        l += 1
                        k += 1
                        
                    elif w1_positional_postinglist[i][k] < w2_positional_postinglist[j][l]:
                        k += 1
                    else:
                        l += 1
                i += 1
                j += 1
            elif w1_postinglist[i] < w2_postinglist[j]:
                i += 1
            else:
                j += 1
    else:
        
        w1_postinglist = list(dictionary[word1].keys())
        w2_postinglist = list(dictionary[word2].keys())
        w1_positional_postinglist = list(dictionary[word1].values())
        w2_positional_postinglist = list(dictionary[word2].values())
        i = 0
        j = 0
        while i < len(w1_postinglist) and j < len(w2_postinglist):
            if(w1_postinglist[i] == w2_postinglist[j]):
                k = 0
                l = 0
                while k < len(w1_positional_postinglist[i]) and l < len(w2_positional_postinglist[j]):
                    if abs(w1_positional_postinglist[i][k] - w2_positional_postinglist[j][l]) <= proximity:
                        if w1_positional_postinglist[i][k] < w2_positional_postinglist[j][l]:
                            if w1_postinglist[i] not in result:
                                result[w1_postinglist[i]] = []
                                result[w1_postinglist[i]].append(w2_positional_postinglist[j][l])
                            else:
                                result[w1_postinglist[i]].append(w2_positional_postinglist[j][l])
                            
                        else:
                            if w1_postinglist[i] not in result:
                                result[w1_postinglist[i]] = []
                                result[w1_postinglist[i]].append(w1_positional_postinglist[i][k])
                            else:
                                result[w1_postinglist[i]].append(w1_positional_postinglist[i][k])
                            
                        l += 1
                        k += 1
                        
                    elif w1_positional_postinglist[i][k] < w2_positional_postinglist[j][l]:
                        k += 1
                    else:
                        l += 1
                i += 1
                j += 1
            elif w1_postinglist[i] < w2_postinglist[j]:
                i += 1
            else:
                j += 1
    return result

def processphrasalquery(expression,proximity):
    #it checks if user entered a proximity if yes then it takes user entered proximity otherwise considers a phrase query and do all normalizing ,punctuation removal and stemming and send words in loop to unionphrasalquery in pairs along with proximity
    if(not proximity):
        proximity = 1
    else:
        proximity = int([e for e in expression if re.search(r"^/\d+$", e)][0][1:])
    stemmer = PorterStemmer()
    words = [e for e in expression if not re.search(r"^/\d+$", e)]
    words = [word.lower() for word in words]
    translator = str.maketrans('','',string.punctuation)
    words = [word.translate(translator) for word in words]
    words = [stemmer.stem(word) for word in words if not re.search(r"^/\d+$",word)]
    word1 = words[0]
    if not (all(word in dictionary for word in words)):
        return []
    for i in range(1,len(words)):
        word2 = words[i]
        result = unionphrasalquery(word1,word2,proximity)
        word1 = result
    return list(result.keys())

def singlewordquery(word):
    #it takes word and normalize and removing punctutaion and stemming checks if it exists in dictionary if yes returns the posting list of the word other wise return empty array means no relevant docs found
    word = word[0]
    word = word.lower()
    translator = str.maketrans('','',string.punctuation)
    word = word.translate(translator)
    stemmer = PorterStemmer()
    word = stemmer.stem(word)
    if word not in dictionary:
        return []
    word_postinglist = list(dictionary[word].keys())
    return word_postinglist
    

def convertexpressiontopostfix(words):
    #using stack to convert the user entered query to postfix expression
    precedence = {'(': 0, 'NOT': 1, 'AND': 2, 'OR': 3}
    stack = []
    output = []

    for word in words:
        if word in ['NOT', 'AND', 'OR']:
            while stack and stack[-1] != '(' and precedence[word] <= precedence[stack[-1]]:
                output.append(stack.pop())
            stack.append(word)
        elif word == '(':
            stack.append(word)
        elif word == ')':
            while stack and stack[-1] != '(':
                output.append(stack.pop())
            if stack and stack[-1] == '(':
                stack.pop()
        else:
            output.append(word)

    while stack:
        output.append(stack.pop())
    return ' '.join(output)

def evaluatepostfixexpression(expression):
    #evaluting the postfix expression using operators precedences
    stack = []
    operators = {'AND', 'OR', 'NOT'}
    for word in expression.split(' '):
        if word not in operators:
            stack.append(word)
        else:
            if word == 'NOT':
                element = stack.pop()
                result = unionNOT(element)
            else:
                word1 = stack.pop()
                word2 = stack.pop()
                if word == 'AND':
                    result = unionAND(word1,word2)
                else:
                    result = unionOR(word1,word2)
            stack.append(result)
    return stack.pop()

def processcomplexquery(expression):
    #converting string into array of words
    words = [e for e in expression]
    #converting each word into lowercase except AND,OR,NOT
    words = [word.lower() if word not in ['AND','OR','NOT'] else word for word in words]
    #removing punctuations from words
    translator = str.maketrans('','',string.punctuation)
    words = [word.translate(translator) if word not in ['(',')'] else word for word in words]
    stemmer = PorterStemmer()
    #stemming the query words
    words = [stemmer.stem(word) if word not in ['(',')','AND','OR','NOT'] else word for word in words]
    # convertexpressiontopostfix function takes the list of words and return the postfix expression which is solved by using evaluatepostfixexpression
    postfix = convertexpressiontopostfix(words)
    result = evaluatepostfixexpression(postfix)
    return result


app = Flask(__name__)
app.debug = True
@app.route('/')
def index():
    #returning the index.html page on '/' request
    return render_template('/index.html')
    

@app.route('/evalexpression',methods=["POST"])
def evalexpression():
    #taking query from front-end
    data = request.get_json()
    expression = data['expression'].strip()
    #splitting query on spaces
    expression = expression.split(' ')
    boolean_operator = [e for e in expression if e in ['AND','OR','NOT']]
    #checking if user entered an empty string as query
    if len(expression) == 1 and expression[0] == '':
        answer = 'empty query'
    #checking if user entered a single word as query
    elif len(expression) == 1:
        expression = [e for e in expression if e not in ['(',')']]
        answer = singlewordquery(expression)
    #checking if query only consists of AND operator only
    elif len(boolean_operator) == boolean_operator.count('AND') and len(boolean_operator) != 0:
        expression = [e for e in expression if e not in ['(',')']]
        answer = processANDonlyquery(expression)
    #checking if query only consists of OR operator only
    elif len(boolean_operator) == boolean_operator.count('OR') and len(boolean_operator) != 0:
        expression = [e for e in expression if e not in ['(',')']]
        answer = processORonlyquery(expression)
    #checking if query only contains NOT operator only
    elif boolean_operator.count('NOT') == 1 and len(boolean_operator) == 1:
        expression = [e for e in expression if e not in ['(',')']]
        answer = processNOTonlyquery(expression)
    #checking if query is a proximity query 
    elif len(boolean_operator) == 0 and any(re.search(r"^/\d+$", element) for element in expression):
        answer = processphrasalquery(expression,True)
    #checking if query is a phrase query
    elif len(boolean_operator) == 0 and not any(re.search(r"^/\d+$", element) for element in expression):
        answer = processphrasalquery(expression,False)
    #query is a complex query combination of AND,OR,NOT
    else:
        answer = processcomplexquery(expression)
    #sending results back to front-end to display to user
    response_data = {'message': answer}
    return jsonify(response_data)

if __name__ == '__main__':

    #reading stopwords from stopwords file
    #read_stopwords function takes filename as an input and return the list of stopwords
    stopwords = read_stopwords('Stopword-List.txt')

    #read_all_files takes the stopwords as a parameter and reads all the files in the folder with a .txt extension and call tokenize method
    dictionary = read_all_files(stopwords)
    
    #dictionary is sorted first on keys and then on document id's
    dictionary = sort_dictionary(dictionary)
    
    #starting the app
    app.run(debug=True)