import sys
import re
import os
import time
import Stemmer
from nltk.corpus import stopwords
from collections import defaultdict


indexDict = defaultdict(list)

stopWords = set(stopwords.words('english'))
stemmer = Stemmer.Stemmer('english')


def readIndexFiles(indexFolder):
    global indexDict

    with open(indexFolder + "/index.txt", "r") as f:
        data = f.readlines()

        for line in data:
            tokens = line.split(' ', 1)
            word = tokens[0]
            postings = tokens[1].split("\n")[0]

            indexDict[word] = postings

    return


def tokenize(text):
    text = text.strip().encode("ascii", errors="ignore").decode()
    # text = re.sub(r'http[^\ ]*\ ', r' ', text)
    text = re.sub(
        r'&nbsp;|&lt;|&gt;|&amp;|&quot;|&apos;|&cent;|&pound;|&yen;|&euro;|&copy;|&reg;', r' ', text)
    text = re.sub(
        r'\`|\~|\!|\@|\#|\$|\%|\^|\&|\*|\(|\)|\-|\_|\=|\+|\\|\||\]|\[|\}|\{|\;|\:|\'|\"|\/|\?|\.|\>|\,|\<|\n|\|\/"', r' ', text)

    tokens = text.split()
    tokens = [token.strip() for token in tokens]

    return tokens


def removeStopwords(words):
    return [word for word in words if not word in stopWords]


def stem(words):
    stemmedWords = stemmer.stemWords(words)

    return stemmedWords


def preprocess(text):
    data = tokenize(text)
    data = removeStopwords(data)
    data = stem(data)

    return data


def getPostings(word):
    if (word in indexDict):
        return indexDict[word]
    return []


def parse(query):
    query = query.lower()
    isFieldQuery = False
    if (':' in query):
        isFieldQuery = True

    if (not isFieldQuery):
        tokens = preprocess(query)
        for token in tokens:
            postings = getPostings(token)
            print(token, ":", postings)
    else:
        fieldDict = {"t": "", "b": "", "i": "", "c": "", "l": "", "r": ""}

        temp = query.split(":", 1)
        field = temp[0].strip()
        query = temp[1].strip()
        while (":" in query):
            temp = query.split(":", 1)
            query = temp[0].strip()
            temp = temp[1].strip()

            queryLen = len(query)
            nextField = query[queryLen - 1:]
            query = query[0:queryLen - 2]

            fieldDict[field] += query + " "

            field = nextField
            query = temp

        fieldDict[field] += query + " "

        for key in fieldDict.keys():
            if (fieldDict[key] != ""):
                tokens = preprocess(fieldDict[key])
                for token in tokens:
                    postings = getPostings(token)
                    if (key in postings):
                        print(token, ":", postings)
                    else:
                        print(token, ":", [])

    return


def main():
    startTime = time.clock()

    indexFolder = sys.argv[1]
    query = sys.argv[2]

    indexFolder = os.path.dirname(indexFolder)
    readIndexFiles(indexFolder)

    parse(query)

    endTime = time.clock()
    print("\nTime Elapsed:", round(endTime - startTime, 2), "seconds")


if __name__ == "__main__":
    main()
