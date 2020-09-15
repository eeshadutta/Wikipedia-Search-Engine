import sys
import re
import os
import time
import math
import Stemmer
from nltk.corpus import stopwords
from collections import defaultdict

indexFolder = "./inverted_index/"
# indexFolder = "./inverted_index_small/"
# indexFolder = "./data/"
queryFile = ""
queryOutputFile = open("queries_op.txt", "w+")

titleOffset = list()
titleFile = ""
offset = list()
vocabFile = ""
numFiles = 0
defaultFieldFactor = {"t": 0.30, "b": 0.25,
                      "i": 0.20, "c": 0.10, "l": 0.05, "r": 0.05}

indexDict = defaultdict(list)

stopWords = set(stopwords.words("english"))
stemmer = Stemmer.Stemmer("english")


def tokenize(text):
    text = text.strip().encode("ascii", errors="ignore").decode()
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


def readIndexFiles():
    global indexFolder
    global titleOffset
    global titleFile
    global offset
    global vocabFile
    global numFiles

    with open(indexFolder + "/titleOffset.txt", "r") as f:
        for line in f:
            temp = int(line.strip())
            titleOffset.append(temp)

    titleFile = open(indexFolder + "/title.txt", "r")

    with open(indexFolder + "/offset.txt", "r") as f:
        for line in f:
            temp = int(line.strip())
            offset.append(temp)

    vocabFile = open(indexFolder + "/vocab.txt", "r")

    with open(indexFolder + "/fileNumbers.txt", "r") as f:
        numFiles = int(f.read().strip())

    return


def findFileNum(low, high, offset, word, fd, typ):
    while low < high:
        mid = int((low + high) / 2)
        fd.seek(offset[mid])
        wordPtr = fd.readline().strip().split()

        if (typ == 1):
            word = int(word)
            wordPtr[0] = int(wordPtr[0])

        if (word == wordPtr[0]):
            return wordPtr[1:], mid
        elif (word < wordPtr[0]):
            high = mid
        else:
            low = mid + 1

    return [], -1


def findDocs(filename, fileNum, field, word, fieldFile):
    global indexFolder

    fieldOffset = list()
    docFreq = list()

    with open(indexFolder + "/offset_" + field + fileNum + ".txt") as f:
        for line in f:
            temp = line.strip().split()
            fieldOffset.append(int(temp[0]))
            docFreq.append(int(temp[1]))

    docList, mid = findFileNum(
        0, len(fieldOffset), fieldOffset, word, fieldFile, 0)
    return docList, docFreq[mid]


def processSimpleQuery(tokens):
    global offset
    global vocabFile
    global indexFolder

    fields = ["t", "b", "i", "c", "l", "r"]
    docFreq = {}
    docList = defaultdict(dict)

    for token in tokens:
        docs, _ = findFileNum(0, len(offset), offset, token, vocabFile, 0)
        if (len(docs) > 0):
            fileNum = docs[0]
            docFreq[token] = docs[1]
            for field in fields:
                filename = indexFolder + "/" + field + str(fileNum) + ".txt"
                fieldFile = open(filename, "r")
                docList[token][field], _ = findDocs(
                    filename, fileNum, field, token, fieldFile)

    return docList, docFreq


def processFieldQuery(tokens, fields):
    global offset
    global vocabFile
    global indexFolder

    docFreq = {}
    docList = defaultdict(dict)

    for field, token in zip(fields, tokens):
        docs, _ = findFileNum(0, len(offset), offset, token, vocabFile, 0)
        if (len(docs) > 0):
            fileNum = docs[0]
            filename = indexFolder + "/" + field + str(fileNum) + ".txt"
            fieldFile = open(filename, "r")
            docList[token][field], docFreq[token] = findDocs(
                filename, fileNum, field, token, fieldFile)

    return docList, docFreq


def rank(results, docFreq, fieldFactor):
    global numFiles

    queryIDF = {}
    docs = defaultdict(float)

    for key in docFreq:
        queryIDF[key] = math.log(
            (float(numFiles) - float(docFreq[key]) + 0.5) / (float(docFreq[key]) + 0.5))
        docFreq[key] = math.log(float(numFiles) / float(docFreq[key]))

    for word in results:
        postings = results[word]
        for field in postings:
            postingList = postings[field]
            for i in range(0, len(postingList), 2):
                docs[postingList[i]] += float(fieldFactor[word][field] * (
                    1 + math.log(float(postingList[i+1]))) * docFreq[word])

    return docs


def parse(K, query):
    global titleOffset
    global defaultFieldFactor

    fieldFactor = defaultdict(dict)

    query = query.lower().strip()
    isFieldQuery = False
    if (":" in query):
        isFieldQuery = True

    if (not isFieldQuery):
        tokens = preprocess(query)
        results, docFreq = processSimpleQuery(tokens)

        for token in tokens:
            fieldFactor[token] = defaultFieldFactor

        results = rank(results, docFreq, fieldFactor)

    else:
        tokens = list()
        fields = list()

        miniQueries = re.findall(r'[t|b|c|i|l|r]:([^:]*)(?!\S)', query)
        tempFields = re.findall(r'([t|b|c|i|l|r]):', query)

        for words, field in zip(miniQueries, tempFields):
            for word in words.split():
                word = preprocess(word)
                if (len(word) > 0 and len(word[0]) > 0):
                    word = word[0]
                    tokens.append(word)
                    fields.append(field)

        # results, docFreq = processFieldQuery(tokens, fields)
        results, docFreq = processSimpleQuery(tokens)

        for token, field in zip(tokens, fields):
            # fieldFactor[token] = defaultFieldFactor
            # fieldFactor[token][field] *= 10
            if (field == "t"):
                fieldFactor[token] = {"t": 1, "b": 0.20,
                                      "i": 0.10, "c": 0.10, "l": 0.05, "r": 0.05}
            if (field == "b"):
                fieldFactor[token] = {"t": 0.20, "b": 1,
                                      "i": 0.10, "c": 0.10, "l": 0.05, "r": 0.05}
            if (field == "i"):
                fieldFactor[token] = {"t": 0.20, "b": 0.20,
                                      "i": 1, "c": 0.10, "l": 0.05, "r": 0.05}
            if (field == "c"):
                fieldFactor[token] = {"t": 0.20, "b": 0.20,
                                      "i": 0.10, "c": 1, "l": 0.05, "r": 0.05}
            if (field == "l"):
                fieldFactor[token] = {"t": 0.20, "b": 0.20,
                                      "i": 0.10, "c": 0.05, "l": 1, "r": 0.05}
            if (field == "r"):
                fieldFactor[token] = {"t": 0.20, "b": 0.20,
                                      "i": 0.10, "c": 0.05, "l": 0.05, "r": 1}

        results = rank(results, docFreq, fieldFactor)

    if (len(results) > 0):
        results = sorted(results, key=results.get, reverse=True)
        results = results[:K]
        for result in results:
            title, _ = findFileNum(
                0, len(titleOffset), titleOffset, result, titleFile, 1)

            queryOutputFile.write(str(result) + ", " + " ".join(title) + "\n")

    return


def processQueries():
    global queryFile

    f = open(queryFile, "r")
    while True:
        line = f.readline()
        if not line:
            break

        startTime = time.time()

        line = line.strip().split(",")
        K = int(line[0].strip())
        query = line[1]
        parse(K, query)

        endTime = time.time()

        totalTime = endTime - startTime

        queryOutputFile.write(str(round(totalTime, 2)) +
                              ", " + str(round(totalTime / K, 2)) + "\n")
        queryOutputFile.write("\n")

    return


def main():
    global queryFile
    global indexFolder

    indexFolder = os.path.dirname(indexFolder)
    readIndexFiles()

    queryFile = sys.argv[1]
    processQueries()

    queryOutputFile.close()


if __name__ == "__main__":
    main()
