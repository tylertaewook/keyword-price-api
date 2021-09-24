# -*- coding: utf-8 -*-
import pandas as pd
import re

from collections import Counter
from alive_progress import alive_bar


class Extractor:
    """class responsible for extracting keywords for the main model

    refer to [keyword-price-api/server.py] for its uses

    Attributes:
        None
    """

    def __init__(self):
        print("initialized")

        # self.codeprice = self.generate_codeprice()
        # self.stopwords = self.generate_stopwords()

        # saver.dict_to_csv("stopwords.csv", self.stopwords)
        # saver.dict_to_csv("codeprice.csv", self.codeprice)

    def extract_keyword(self, data, col="cat4", n=None):
        """
        returns a dump-ready raw file containing 
        [rank, keyword, appearance, and product_list] 
        for each keyword, for each group

        :data: pandas DataFrame obj
        :freqnum: deal with top 'n' most common keywords (default=10)
        :aik_mode: whether to remove keywords from 'D' range or not

        :semireturn: keywords | list(counter(keywords))
        i.e. 
            [('백인',23), ('이너백',12), ('핸드백',5)]
        :semireturn: dict | list(dict[keyword]: list(pid))
        i.e.
            {"400249 TLK88": [12345678, 12345678, 12345678]}
            {"652439 POSLI": [12345678, 12345678, 12345678]}

        :return: file ready to be dumped to .json
            -----------------------------------
            Category(lowest)
                {
                    "rank": (int),
                    "keyword": (str),
                    "appearance": (int),
                    "product_list": list(int)
                }
            -----------------------------------
        """
        categs = data[col].dropna().unique()

        keywords = [[] for i in range(len(categs))]
        countobjs = []
        dfobjs = []

        print("Extracting Keywords...")
        with alive_bar(3028) as bar:  # 3028
            for categ in categs:
                df = data[data[col] == categ]
                dfobjs.append(df)
                countobj = Counter()

                for i, x in df.iterrows():
                    countobj += self.extract_split(self.preproc_txt(x["title"]))
                    bar(f"Extracting Keywords...")
                countobjs.append(countobj)

        dicts = []

        kw_count = 14099

        # TODO: hard-coded now for debugging
        with alive_bar(648560) as bar:  # 648560
            for num in range(len(categs)):
                dct = {}
                grp = categs[num]
                countobj = countobjs[num]
                df = dfobjs[num]

                comnum = n if n != None else len(countobj)  # checking if n is given
                topfreq = countobj.most_common(comnum)

                keywords[num] = topfreq
                kw_count = len(topfreq)
                for tup in topfreq:
                    keyword = tup[0]
                    pidlist = []
                    for idx, row in df.iterrows():
                        if keyword in row.title:
                            pidlist.append(row["pid"])
                        bar("Organizing output files...")
                    dct[keyword] = list(set(pidlist))
                dicts.append(dct)
        print("...Done!")
        return self.generate_json(keywords, dicts, categs)

    def generate_json(self, keywords, dicts, categs):
        """
        converts two final difctionaries from extractkeyword method(s) into
        a compressed file ready to be dumped as .json file

        :input: keywords | list(counter(keywords))
        i.e. 
            [('백인',23), ('이너백',12), ('핸드백',5)]
        :input: dicts | list(dict[keyword]: list(pid))
        i.e.
            {"400249 TLK88": [12345678, 12345678, 12345678]}
            "652439 POSLI": [12345678, 12345678, 12345678]}
        :input: categs | list(str)
        i.e.
            ['골프장갑', '우산', '생활용품', ..., '마스크']

        :result: file ready to be dumped
            -----------------------------------
            Group A
                {
                    "rank": (int),
                    "keyword": (str),
                    "appearance": (int),
                    "product_list": list(int)
                }
            -----------------------------------
        """
        final = []
        for i in range(len(keywords)):  # 46
            groupDict = {"categ": categs[i], "keywords": []}
            for rank, tup in enumerate(keywords[i]):
                word = tup[0]
                freq = tup[1]
                dct = dicts[i]
                wordDict = {
                    "rank": rank + 1,
                    "keyword": word,
                    "appearance": freq,
                    "product_list": dct[word] if word in dct.keys() else "",
                }
                groupDict["keywords"].append(wordDict)
            final.append(groupDict)
        return final

    def preproc_txt(self, title):
        """
        returns a string with special characters removed given a rowSeries

        :param str: title
        :return: str result
        """

        # remove special characters
        title = re.sub(re.compile("<.*?>"), "", title)  # html tags
        title = re.sub("[/{}()\[\]\b]", "", title)
        title = re.sub("\u200b", "", title)
        title = re.sub("\xa0", "", title)
        title = re.sub("[ㄱ-ㅎㅏ-ㅣ]+", "", title)
        title = re.sub("[-=+,#/\?:^$.@*\"※~&%ㆍ!』\\‘|\(\)\[\]\<\>`'…》]", "", title)

        # remove stopwords

        # stopwords = []
        # querywords = title.split()

        # resultwords = [word for word in querywords if word.lower() not in stopwords]
        # result = " ".join(resultwords)
        # for word in stopwords:
        #     result = result.replace(word, "")

        return title  # change to result if above block is uncommented

    def extract_split(self, txt):
        """
        extract keyword, appreancefreq with Komoran() for 조사 removal and space split

        :return: Counter obj with keywords:count
        i.e.
            [('백인',23), ('이너백',11), ('핸드백',8)]
        """
        # FIXME: java heap memory error

        # komoran = Komoran(DEFAULT_MODEL["LIGHT"])
        # josas = komoran.get_morphes_by_tags(txt, tag_list=["JX", "JK", "JC"])
        # for josa in josas:
        #     txt = txt.replace(josa, "")
        splitted = txt.split()

        for i, v in enumerate(splitted):
            if len(v) < 2:  # checking for too short words
                splitted.pop(i)
        return Counter(splitted)
