# -*- coding: utf-8 -*-
import pandas as pd
import os
import datetime
import re
import csv

from .Saver import Saver
from collections import Counter
from alive_progress import alive_bar
from konlpy.tag import Okt
from krwordrank.word import KRWordRank
from PyKomoran import Komoran, DEFAULT_MODEL


class Extractor:
    """class responsible for extracting keywords for the main model

    refer to [keyword-price-api/server.py] for its uses

    Attributes:
        genprods (df): ./gucci_bags.csv
        
        codeprice (dict): {CODE: averaged price}
        stopwords (dict): {CODE: list(str)}
    """

    def __init__(self, genprods):
        self.genprods = genprods
        self.codeprice = self.generate_codeprice()
        self.stopwords = self.generate_stopwords()

        # saver.dict_to_csv("stopwords.csv", self.stopwords)
        # saver.dict_to_csv("codeprice.csv", self.codeprice)

    def generate_codeprice(self):
        """
        generates a codeprice dict containing averaged genprice for every model code

        :return: dict codeprice | {CODE: averaged price}
        i.e.
            {"400249 TLK88": 4690000}
            {"652439 POSLI": 5780000}
        """
        codeprice = {}
        final_df = pd.DataFrame()

        # X = pd.read_csv('./data/gucci_bags_simp2.csv')
        X = self.genprods
        X_agg = X.groupby("CODE", as_index=False).agg({"PRICE": ["count", "sum"]})
        X_agg.columns = ["CODE", "sale_count", "selling_sum"]
        final_df = pd.concat([final_df, X_agg])
        final_df = final_df.groupby("CODE", as_index=False).agg(
            {"sale_count": "sum", "selling_sum": "sum"}
        )

        for i, row in final_df.iterrows():
            codeprice[row["CODE"]] = row["selling_sum"] / row["sale_count"]

        return codeprice

    def generate_stopwords(self):
        """
        generates a stopwords dict containing words to remove for every model code

        :return: dict codeprice | {CODE: list(str)}
        i.e.
            {"400249 TLK88": '구찌', '탑핸들백', '파이썬'}
            {"652439 POSLI": '구찌', '디오니소스', '페드락'}
        """
        stopword = {}
        simp = self.genprods
        # TITLE (ENG), LINEUP (KOR), NAME(KOR)
        for i, x in simp.iterrows():
            words = []
            for col in ["NAME(KOR)", "LINEUP(KOR)", "TITLE(ENG)"]:
                words += x[col].split()
            stopword[x.CODE] = list(dict.fromkeys(words))
        return stopword

    def extractkeyword_proc(self, data, n=None):
        """
        returns a dump-ready processed file (a, b, c, e 에서 미리 정품 구간(D 80~100)에서 쓰이는 키워드를 제외하고 리턴) 
        containing [rank, keyword, appearance, and product_list] 
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
            Group A
                {
                    "rank": (int),
                    "keyword": (str),
                    "appearance": (int),
                    "product_list": list(int)
                }
            -----------------------------------
        """
        groups = ["a", "b", "c", "d", "e"]

        keywords = [[] for i in range(4)]
        countobjs = []
        dfobjs = []

        print("Running extractkeyword_proc()...")
        with alive_bar(len(data)) as bar:  # 31390
            for num in range(5):
                grp = groups[num]
                df = data[data["group"] == grp]
                dfobjs.append(df)
                countobj = Counter()

                for i, x in df.iterrows():
                    countobj += self.extract_split(self.preproc_row(x))
                    bar(f"Extracting Keywords...")
                countobjs.append(countobj)

        dicts = []

        with alive_bar(156300) as bar:  # len(data) * 5
            for num in [0, 1, 2, 4]:
                dct = {}
                grp = groups[num]
                countobj = countobjs[num]
                df = dfobjs[num]

                countobj = countobj - countobjs[3]  # remove keywords from group D
                comnum = n if n != None else len(countobj)  # checking if n is given
                topfreq = countobj.most_common(comnum)

                num = 3 if num == 4 else num  # prevent list out of range error
                keywords[num] = topfreq

                for tup in topfreq:
                    keyword = tup[0]
                    pidlist = []
                    for idx, row in df.iterrows():
                        if keyword in row.title:
                            pidlist.append(row.pid)
                        bar("Organizing output files...")
                    dct[keyword] = list(set(pidlist))
                dicts.append(dct)
        print("...Done!")
        return self.generate_final_dict(keywords, dicts)

    def extractkeyword_raw(self, data, n=None):
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
            Group A
                {
                    "rank": (int),
                    "keyword": (str),
                    "appearance": (int),
                    "product_list": list(int)
                }
            -----------------------------------
        """
        groups = ["a", "b", "c", "d", "e"]

        keywords = [[] for i in range(5)]
        countobjs = []
        dfobjs = []

        print("Running extractkeyword_raw()...")
        with alive_bar(len(data)) as bar:  # 31390
            for num in range(5):
                grp = groups[num]
                df = data[data["group"] == grp]
                dfobjs.append(df)
                countobj = Counter()

                for i, x in df.iterrows():
                    countobj += self.extract_split(self.preproc_row(x))
                    bar(f"Extracting Keywords...")
                countobjs.append(countobj)

        dicts = []

        with alive_bar(len(data) * 10) as bar:
            for num in range(5):
                dct = {}
                grp = groups[num]
                countobj = countobjs[num]
                df = dfobjs[num]

                comnum = n if n != None else len(countobj)  # checking if n is given
                topfreq = countobj.most_common(comnum)

                keywords[num] = topfreq

                for tup in topfreq:
                    keyword = tup[0]
                    pidlist = []
                    for idx, row in df.iterrows():
                        if keyword in row.title:
                            pidlist.append(row.pid)
                        bar("Organizing output files...")
                    dct[keyword] = list(set(pidlist))
                dicts.append(dct)
        print("...Done!")
        return self.generate_final_dict(keywords, dicts)

    def generate_final_dict(self, keywords, dicts):
        """
        converts two final dictionaries from extractkeyword method(s) into
        a compressed file ready to be dumped as .json file

        :input: keywords | list(counter(keywords))
        i.e. 
            [('백인',23), ('이너백',12), ('핸드백',5)]
        :input: dicts | list(dict[keyword]: list(pid))
        i.e.
            {"400249 TLK88": [12345678, 12345678, 12345678]}
            "652439 POSLI": [12345678, 12345678, 12345678]}

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
        groupmap = ["a", "b", "c", "d", "e"]
        final = []
        for i in range(len(keywords)):
            groupDict = {"group": groupmap[i], "keywords": []}
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

    def preproc_row(self, row):
        """
        returns a string with special characters removed given a rowSeries

        :param row: rowSeries
        :return: str result
        """

        code = row["code"]
        remcode = self.search_code(row["title"], full=False)
        # remove special characters
        title = re.sub("[/{}()\[\]\b\d+\b]", "", row["title"])
        title = re.sub("\u200b", "", title)
        title = re.sub("\xa0", "", title)
        title = re.sub("[ㄱ-ㅎㅏ-ㅣ]+", "", title)
        title = re.sub("[-=+,#/\?:^$.@*\"※~&%ㆍ!』\\‘|\(\)\[\]\<\>`'…》]", "", title)
        # remove 6digit remcode
        title = title.replace(remcode, "")

        stopwords = ["gucci", "구찌", "마몬트", "디오니소스", "마몽트"]
        stopwords += self.stopwords[code]
        # TODO: improve method of removing stopwords, disregarding space
        querywords = title.split()

        resultwords = [word for word in querywords if word.lower() not in stopwords]
        result = " ".join(
            resultwords
        )  # this also replaces multiple whitespace characters into ' '

        # FIXME this workaround causing performance issues
        for word in stopwords:
            result = result.replace(word, "")

        return result

    def preproc_list(self, textlist):
        """
        returns a list of preprocessed strings given a list(str)
        :param textlist: list(str)
        :return: list(str) with special characters removed
        """
        finallist = []
        for item in textlist:
            code = self.search_code(item)
            # remove special characters
            item = re.sub("[/{}()\[\]\b\d+\b]", "", item)
            item = re.sub("\u200b", "", item)
            item = re.sub("\xa0", "", item)
            item = re.sub("[ㄱ-ㅎㅏ-ㅣ]+", "", item)
            item = re.sub("[-=+,#/\?:^$.@*\"※~&%ㆍ!』\\‘|\(\)\[\]\<\>`'…》]", "", item)

            stopwords = ["gucci", "구찌"]
            stopwords += self.stopwords[code]
            querywords = item.split()

            resultwords = [word for word in querywords if word.lower() not in stopwords]
            result = " ".join(resultwords)

            finallist.append(result)
        return finallist

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

    def search_code(self, text, full=True):
        """
        searches for modelcode in given text
        full=True: 655658 17QDT
        full=False: 655658
        """
        if full:
            temp = re.search("\d{6} [\dA-Z]{5}", text)
        else:
            temp = re.search("\d{% s}" % 6, text)
        res = temp.group(0) if temp else ""
        return str(res)
