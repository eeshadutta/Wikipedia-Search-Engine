import sys
import re
import os
import time
import xml.sax
from nltk.corpus import stopwords
from nltk.stem import SnowballStemmer
from collections import defaultdict

pageCount = 0
titleDict = {}
indexDict = defaultdict(list)

stopWords = set(stopwords.words('english'))
stemmer = SnowballStemmer('english')


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
    stemmedWords = []
    for word in words:
        word = stemmer.stem(word)
        stemmedWords.append(word)

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

    lines = ' '.join(lines)
    data = preprocess(lines)

    return data


def processCategories(text):
    data = re.findall(r'\[\[category:.*\]\]', text)
    categories = []
    numCategories = len(data)

    for i in range(numCategories):
        categories.append(data[i][11:len(data[i]) - 1])

    categories = ' '.join(categories)
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

    links = ' '.join(links)
    data = preprocess(links)

    return data


def processReferences(text):
    data = re.findall(r'\|\s*title[^\|]*', text)
    references = []
    numReferences = len(data)

    for i in range(numReferences):
        references.append(data[i][data[i].find("=") + 1:len(data[i]) - 1])

    references = ' '.join(references)
    data = preprocess(references)

    return data


def countWords(text, textDict, words):
    for word in text:
        textDict[word] += 1
        words[word] += 1


def createIndex(title, body, infobox, categories, links, references):
    global pageCount

    words = defaultdict(int)
    titleDict = defaultdict(int)
    bodyDict = defaultdict(int)
    infoboxDict = defaultdict(int)
    categoriesDict = defaultdict(int)
    linksDict = defaultdict(int)
    referencesDict = defaultdict(int)

    countWords(title, titleDict, words)
    countWords(body, bodyDict, words)
    countWords(infobox, infoboxDict, words)
    countWords(categories, categoriesDict, words)
    countWords(links, linksDict, words)
    countWords(references, referencesDict, words)

    for word in words.keys():
        temp = "d" + str(pageCount)
        if (titleDict[word]):
            temp += "t" + str(titleDict[word])
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


def writeToFiles():
    global indexDict, titleDict
    data = []

    for word in sorted(indexDict.keys()):
        postings = indexDict[word]
        entry = word + ' '
        entry += ' '.join(postings)
        data.append(entry)

    with open("20171104/invertedindex/" + "index.txt", "w+") as f:
        f.write("\n".join(data))

    data = []

    for docID in sorted(titleDict.keys()):
        entry = str(docID) + ' ' + titleDict[docID]
        data.append(entry)

    with open("20171104/invertedindex/" + "titles.txt", "w+") as f:
        f.write("\n".join(data))

    with open("20171104/invertedindex_stat.txt", "w+") as f:
        f.write(str(len(indexDict)))

    titleDict = {}
    indexDict = defaultdict(list)


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
        if (name == 'page'):
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
    wikiDumpFile = sys.argv[1]
    # indexFolder = sys.argv[2]
    # indexStatFile = sys.argv[3]

    parser = xml.sax.make_parser()
    parser.setFeature(xml.sax.handler.feature_namespaces, False)

    handler = WikiHandler()

    parser.setContentHandler(handler)
    parser.parse(wikiDumpFile)

    writeToFiles()


if __name__ == '__main__':
    main()
