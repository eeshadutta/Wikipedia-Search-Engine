import sys
import re
import os
import time
import xml.sax
from nltk.corpus import stopwords
import Stemmer
from collections import defaultdict

pageCount = 0
fileCount = 0
offset = 0
titleDict = {}
indexDict = defaultdict(list)
pageBreak = 25000
wordBreak = 100000

wikiDumpFolder = None
indexFolder = None
indexStatFile = None

stopWords = set(stopwords.words("english"))
stemmer = Stemmer.Stemmer("english")


def processText(title, text):
    title = title.lower()
    text = text.lower()

    categories = []
    links = []
    references = []

    data = text.split("==references==")
    if (len(data) == 1):
        data = text.split("== references ==")
    if (len(data) == 1):
        data = text.split("== references==")
    if (len(data) == 1):
        data = text.split("==references ==")

    title = processTitle(title)
    body = processBody(data[0])
    infobox = processInfobox(data[0])

    if (len(data) > 1):
        categories = processCategories(data[1])
        links = processLinks(data[1])
        references = processReferences(data[1])

    return title, body, infobox, categories, links, references


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


def processTitle(text):
    data = preprocess(text)

    return data


def processBody(text):
    data = re.sub(r'\{\{.*\}\}', r' ', text)
    data = preprocess(data)

    return data


def processInfobox(text):
    data = text.split("\n")
    flag = 0
    lines = []
    numLines = len(data)

    for i in range(numLines):
        if (flag % 2 == 0 and re.search(r'\{\{infobox', data[i])):
            flag = 1
            lines.append(re.sub(r'\{\{infobox', '', data[i]))
        elif (flag % 2 == 1):
            if (data[i] == "}}"):
                flag = flag + 1
            else:
                lines.append(data[i])
        elif (flag == 0):
            if ((100 * i)/numLines > 50):
                break

    lines = " ".join(lines)
    data = preprocess(lines)

    return data


def processCategories(text):
    data = re.findall(r'\[\[category:.*\]\]', text)
    categories = []
    numCategories = len(data)

    for i in range(numCategories):
        categories.append(data[i][11:len(data[i]) - 1])

    categories = " ".join(categories)
    data = preprocess(categories)

    return data


def processLinks(text):
    data = text.split("==external links==")
    if (len(data) == 1):
        data = text.split("== external links ==")
    if (len(data) == 1):
        data = text.split("== external links==")
    if (len(data) == 1):
        data = text.split("==external links ==")

    if (len(data) == 1):
        return []

    data = re.findall(r'\*\s*\[.*\]', data[1])
    links = []
    numLinks = len(data)

    for i in range(numLinks):
        links.append(data[i][2:len(data[i]) - 1])

    links = " ".join(links)
    data = preprocess(links)

    return data


def processReferences(text):
    data = re.findall(r'\|\s*title[^\|]*', text)
    references = []
    numReferences = len(data)

    for i in range(numReferences):
        references.append(data[i][data[i].find("=") + 1:len(data[i]) - 1])

    references = " ".join(references)
    data = preprocess(references)

    return data


def countWords(text, textDict, words):
    for word in text:
        textDict[word] += 1
        words[word] += 1


def createIndex(title, body, infobox, categories, links, references):
    global pageCount
    global fileCount
    global offset
    global titleDict
    global indexDict

    words = defaultdict(int)
    nameDict = defaultdict(int)
    bodyDict = defaultdict(int)
    infoboxDict = defaultdict(int)
    categoriesDict = defaultdict(int)
    linksDict = defaultdict(int)
    referencesDict = defaultdict(int)

    countWords(title, nameDict, words)
    countWords(body, bodyDict, words)
    countWords(infobox, infoboxDict, words)
    countWords(categories, categoriesDict, words)
    countWords(links, linksDict, words)
    countWords(references, referencesDict, words)

    for word in words.keys():
        temp = "d" + str(pageCount)
        if (nameDict[word]):
            temp += "t" + str(nameDict[word])
        if (bodyDict[word]):
            temp += "b" + str(bodyDict[word])
        if (infoboxDict[word]):
            temp += "i" + str(infoboxDict[word])
        if (categoriesDict[word]):
            temp += "c" + str(categoriesDict[word])
        if (linksDict[word]):
            temp += "l" + str(linksDict[word])
        if (referencesDict[word]):
            temp += "r" + str(referencesDict[word])

        indexDict[word].append(temp)

    pageCount += 1

    if (pageCount % pageBreak == 0):
        writeToFiles()


def writeToFiles():
    global indexDict
    global titleDict
    global fileCount
    global offset

    data = []

    for word in sorted(indexDict.keys()):
        postings = indexDict[word]
        entry = word + " "
        entry += " ".join(postings)
        data.append(entry)

    with open(indexFolder + "/index" + str(fileCount) + ".txt", "w+") as f:
        f.write("\n".join(data))

    dataOffset = []
    data = []
    prevOffset = offset

    for key in sorted(titleDict):
        dataOffset.append(str(prevOffset))
        entry = str(key) + " " + titleDict[key].strip()
        data.append(entry)
        prevOffset += len(entry) + 1

    with open(indexFolder + "/title.txt", "a") as f:
        f.write("\n".join(data))
        f.write("\n")

    with open(indexFolder + "/titleOffset.txt", "a") as f:
        f.write("\n".join(dataOffset))
        f.write("\n")

    fileCount += 1
    offset = prevOffset
    titleDict = {}
    indexDict = defaultdict(list)


def mergeFiles():
    global fileCount
    global indexFolder

    print("Merging...", fileCount, "files")

    fileFlag = [0] * fileCount
    fileDescriptor = {}
    currLine = {}
    currEntry = {}
    offsetSize = 0
    currCount = 0
    totalCount = 0
    data = defaultdict(list)
    sortedWordArray = list()

    for i in range(fileCount):
        fileDescriptor[i] = open(
            indexFolder + "/index" + str(i) + ".txt", "r")
        currLine[i] = fileDescriptor[i].readline().strip()
        if (len(currLine[i]) == 0):
            fileDescriptor[i].close()
            os.remove(indexFolder + "/index" + str(i) + ".txt")
            continue

        currEntry[i] = currLine[i].split()
        currWord = currEntry[i][0]
        if (currWord not in sortedWordArray):
            sortedWordArray.append(currWord)

        fileFlag[i] = 1

    sortedWordArray.sort()

    while any(fileFlag) and len(sortedWordArray):
        currCount += 1
        currWord = sortedWordArray[0]
        sortedWordArray.pop(0)

        if (currCount % wordBreak == 0):
            temp = totalCount
            totalCount, offsetSize = createFinalIndex(
                data, totalCount, offsetSize)
            if (temp != totalCount):
                data = defaultdict(list)

        for i in range(fileCount):
            if (fileFlag[i] == 1):
                if (currEntry[i][0] == currWord):
                    currLine[i] = fileDescriptor[i].readline()
                    data[currWord].extend(currEntry[i][1:])
                    currLine[i] = currLine[i].strip()

                    if (len(currLine[i]) == 0):
                        fileDescriptor[i].close()
                        fileFlag[i] = 0
                        os.remove(indexFolder + "/index" + str(i) + ".txt")
                    else:
                        currEntry[i] = currLine[i].split()
                        firstWord = currEntry[i][0]
                        if (firstWord not in sortedWordArray):
                            sortedWordArray.append(firstWord)
                            sortedWordArray.sort()

    totalCount, offsetSize = createFinalIndex(data, totalCount, offsetSize)


def createFinalIndex(data, totalCount, offsetSize):
    global indexFolder

    print("Writing to final Index files...")

    title = defaultdict(dict)
    body = defaultdict(dict)
    infobox = defaultdict(dict)
    categories = defaultdict(dict)
    links = defaultdict(dict)
    references = defaultdict(dict)

    distinctWords = []
    offset = []

    for key in sorted(data.keys()):
        temp = []
        docs = data[key]
        numDocs = len(docs)

        entry = key + " " + str(totalCount) + " " + str(numDocs)
        distinctWords.append(entry)
        offset.append(str(offsetSize))
        offsetSize += len(entry) + 1

        for i in range(numDocs):
            postings = docs[i]
            docID = re.sub(r'.*d([0-9]*).*', r'\1', postings)

            temp = re.sub(r'.*t([0-9]*).*', r'\1', postings)
            if (temp != postings):
                title[key][docID] = float(temp)

            temp = re.sub(r'.*b([0-9]*).*', r'\1', postings)
            if (temp != postings):
                body[key][docID] = float(temp)

            temp = re.sub(r'.*i([0-9]*).*', r'\1', postings)
            if (temp != postings):
                infobox[key][docID] = float(temp)

            temp = re.sub(r'.*c([0-9]*).*', r'\1', postings)
            if (temp != postings):
                categories[key][docID] = float(temp)

            temp = re.sub(r'.*l([0-9]*).*', r'\1', postings)
            if (temp != postings):
                links[key][docID] = float(temp)

            temp = re.sub(r'.*r([0-9]*).*', r'\1', postings)
            if (temp != postings):
                references[key][docID] = float(temp)

    titleData = list()
    titleOffset = list()
    prevTitle = 0

    bodyData = list()
    bodyOffset = list()
    prevBody = 0

    infoboxData = list()
    infoboxOffset = list()
    prevInfobox = 0

    categoriesOffset = list()
    categoriesData = list()
    prevCategories = 0

    linksData = list()
    linksOffset = list()
    prevLinks = 0

    referencesOffset = list()
    referencesData = list()
    prevReferences = 0

    for key in sorted(data.keys()):
        if key in title:
            string = key + " "
            docs = sorted(title[key], key=title[key].get, reverse=True)
            numDocs = len(docs)
            for i in range(numDocs):
                string += docs[i] + " " + str(title[key][docs[i]]) + " "
            titleData.append(string)
            titleOffset.append(str(prevTitle) + " " + str(numDocs))
            prevTitle += len(string) + 1

        if key in body:
            string = key + " "
            docs = sorted(body[key], key=body[key].get, reverse=True)
            numDocs = len(docs)
            for i in range(numDocs):
                string += docs[i] + " " + str(body[key][docs[i]]) + " "
            bodyData.append(string)
            bodyOffset.append(str(prevBody) + " " + str(numDocs))
            prevBody += len(string) + 1

        if key in infobox:
            string = key + " "
            docs = sorted(infobox[key], key=infobox[key].get, reverse=True)
            numDocs = len(docs)
            for i in range(numDocs):
                string += docs[i] + " " + str(infobox[key][docs[i]]) + " "
            infoboxData.append(string)
            infoboxOffset.append(str(prevInfobox) + " " + str(numDocs))
            prevInfobox += len(string) + 1

        if key in categories:
            string = key + " "
            docs = sorted(categories[key],
                          key=categories[key].get, reverse=True)
            numDocs = len(docs)
            for i in range(numDocs):
                string += docs[i] + " " + str(categories[key][docs[i]]) + " "
            categoriesData.append(string)
            categoriesOffset.append(str(prevCategories) + " " + str(numDocs))
            prevCategories += len(string) + 1

        if key in links:
            string = key + " "
            docs = sorted(links[key], key=links[key].get, reverse=True)
            numDocs = len(docs)
            for i in range(numDocs):
                string += docs[i] + " " + str(links[key][docs[i]]) + " "
            linksData.append(string)
            linksOffset.append(str(prevLinks) + " " + str(numDocs))
            prevLinks += len(string) + 1

        if key in references:
            string = key + " "
            docs = sorted(references[key],
                          key=references[key].get, reverse=True)
            numDocs = len(docs)
            for i in range(numDocs):
                string += docs[i] + " " + str(references[key][docs[i]]) + " "
            referencesData.append(string)
            referencesOffset.append(str(prevReferences) + " " + str(numDocs))
            prevReferences += len(string) + 1

    with open(indexFolder + "/t" + str(totalCount) + ".txt", "w") as f:
        f.write("\n".join(titleData))
    with open(indexFolder + "/offset_t" + str(totalCount) + ".txt", "w") as f:
        f.write("\n".join(titleOffset))

    with open(indexFolder + "/b" + str(totalCount) + ".txt", "w") as f:
        f.write("\n".join(bodyData))
    with open(indexFolder + "/offset_b" + str(totalCount) + ".txt", "w") as f:
        f.write("\n".join(bodyOffset))

    with open(indexFolder + "/i" + str(totalCount) + ".txt", "w") as f:
        f.write("\n".join(infoboxData))
    with open(indexFolder + "/offset_i" + str(totalCount) + ".txt", "w") as f:
        f.write("\n".join(infoboxOffset))

    with open(indexFolder + "/c" + str(totalCount) + ".txt", "w") as f:
        f.write("\n".join(categoriesData))
    with open(indexFolder + "/offset_c" + str(totalCount) + ".txt", "w") as f:
        f.write("\n".join(categoriesOffset))

    with open(indexFolder + "/l" + str(totalCount) + ".txt", "w") as f:
        f.write("\n".join(linksData))
    with open(indexFolder + "/offset_l" + str(totalCount) + ".txt", "w") as f:
        f.write("\n".join(linksOffset))

    with open(indexFolder + "/r" + str(totalCount) + ".txt", "w") as f:
        f.write("\n".join(referencesData))
    with open(indexFolder + "/offset_r" + str(totalCount) + ".txt", "w") as f:
        f.write("\n".join(referencesOffset))

    with open(indexFolder + "/vocab.txt", "a") as f:
        f.write("\n".join(distinctWords))
        f.write("\n")

    with open(indexFolder + "/offset.txt", "a") as f:
        f.write("\n".join(offset))
        f.write("\n")

    totalCount += 1

    return totalCount, offsetSize


class WikiHandler(xml.sax.ContentHandler):
    def __init__(self):
        self.tag = ""
        self.title = ""
        self.text = ""
        self.id = ""
        self.idFlag = 0

    def startElement(self, name, attrs):
        self.tag = name

    def characters(self, content):
        if (self.tag == "title"):
            self.title += content

        elif (self.tag == "text"):
            self.text += content

        elif (self.tag == "id" and self.idFlag == 0):
            self.id = content
            self.idFlag = 1

    def endElement(self, name):
        global pageCount
        global titleDict

        if (name == "page"):
            self.title = self.title.strip().encode("ascii", errors="ignore").decode()
            titleDict[pageCount] = self.title

            title, body, infobox, categories, links, references = processText(
                self.title, self.text)

            createIndex(title, body, infobox, categories, links, references)

            self.currTag = ""
            self.title = ""
            self.text = ""
            self.id = ""
            self.idFlag = 0


def main():
    global wikiDumpFolder
    global indexFolder
    global indexStatFile
    global pageCount

    startTime = time.clock()

    wikiDumpFolder = sys.argv[1]
    indexFolder = sys.argv[2]
    indexStatFile = sys.argv[3]

    indexFolder = os.path.dirname(indexFolder)
    if (not os.path.exists(indexFolder)):
        os.makedirs(indexFolder)

    parser = xml.sax.make_parser()
    parser.setFeature(xml.sax.handler.feature_namespaces, False)

    handler = WikiHandler()

    parser.setContentHandler(handler)

    fileNum = 1
    for dumpFile in os.listdir(wikiDumpFolder):
        print("Processing file", fileNum, "started...")
        filename = os.path.join(wikiDumpFolder, dumpFile)
        parser.parse(filename)
        print("File", fileNum, "done")
        fileNum += 1

    with open(indexFolder + "/fileNumbers.txt", "w") as f:
        f.write(str(pageCount))

    writeToFiles()
    
    mergeFiles()

    endTime = time.clock()
    print("Time Elapsed:", round(endTime - startTime, 2), "seconds")


if __name__ == "__main__":
    main()
