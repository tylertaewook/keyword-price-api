# -*- coding: utf-8 -*-
import json
import re
import pandas as pd
import numpy as np

from collections import Counter
from alive_progress import alive_bar


class Extractor:
    """class responsible for extracting keywords for the main model

    refer to [keyword-price-api/server.py] for its uses

    Attributes:
        None
    """

    def __init__(self, data):
        self.data = data
        self.init = "current_cat" not in self.data.columns

        if self.init:
            self.data["current_cat"] = ""
            self.set_current_category()
        else:
            self.feedback = pd.read_pickle("./cache/feedback.pkl")
            self.update_current_category()

    def set_current_category(self):
        """
        set [current_cat] to the lowest available category

        i.e.
            생활건강/마스크/먼지차단마스크 -> 먼지차단마스크  (ends @ cat3)
            스포츠/골프/골프백/골프백세트 -> 골프백세트  (ends @ cat4)
        """
        # ends@cat2 or 3
        self.data["current_cat"] = np.where(
            self.data["cat3"].isnull(), self.data["cat2"], self.data["cat3"]
        )
        # ends@cat3 or 4
        self.data["current_cat"] = np.where(
            self.data["cat4"].notna(), self.data["cat4"], self.data["cat3"]
        )

    def update_current_category(self):
        """
        update current category based on feedback
        """
        for idx, row in self.feedback.iterrows():
            categs = [row["categ"]] + row["sub-cats"]
            self.data["current_cat"] = np.where(
                self.data["current_cat"].isin(categs),
                categs[0],
                self.data["current_cat"],
            )

    def extract_keyword(self):
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
        if self.init:
            return self.extract_keyword_init()
        else:
            return self.extract_keyword_feedback()

    def extract_keyword_init(self, col="current_cat"):
        print("Running extract_keyword_init()...")
        categs = self.data[col].unique()

        keywords = [[] for i in range(len(categs))]
        countobjs = []
        dfobjs = []

        with alive_bar(69) as bar:  # 3028
            for categ in categs:
                df = self.data[self.data[col] == categ]
                dfobjs.append(df)
                countobj = Counter()

                for i, x in df.iterrows():
                    countobj += self.extract_split(self.preproc_txt(x["title"]))
                    bar.text("Extracting Keywords...")
                countobjs.append(countobj)

        dicts = []

        # FIXME: hard-coded now for debugging
        with alive_bar(2955) as bar:  # 648560
            for num in range(len(categs)):
                dct = {}
                grp = categs[num]
                countobj = countobjs[num]
                df = dfobjs[num]

                topfreq = countobj.most_common(len(countobj))

                keywords[num] = topfreq
                for tup in topfreq:
                    keyword = tup[0]
                    pidlist = []
                    for idx, row in df.iterrows():
                        if keyword in row.title:
                            pidlist.append(row["pid"])
                    dct[keyword] = list(set(pidlist))
                    bar.text("Organizing output files...")
                dicts.append(dct)
        print("...Done!")
        return self.generate_json(keywords, dicts, categs)

    def extract_keyword_feedback(self, col="current_cat"):
        print("Running extract_keyword_feedback()...")
        fb = self.feedback
        categs = self.data[col].unique().tolist()
        feedback_categs = fb["categ"].tolist()

        keywords = [[] for i in range(len(categs))]
        gen_countobjs = []
        sus_countobjs = []
        dfobjs = []

        with alive_bar(69) as bar:  # 3028
            for categ in categs:
                df = self.data[self.data[col] == categ]
                dfobjs.append(df)
                gen_countobj = Counter()
                sus_countobj = Counter()

                if (
                    categ in feedback_categs
                ):  # if categ is subject to applying feedbacks

                    # TEST CASE for when the given lprice/hprice is NaN
                    lprice_obj = fb[fb["categ"] == categ]["lprice"]
                    hprice_obj = fb[fb["categ"] == categ]["hprice"]
                    lprice_isnull = lprice_obj.isnull().values[0]
                    hprice_isnull = hprice_obj.isnull().values[0]

                    lprice = 0 if lprice_isnull else int(lprice_obj)
                    hprice = 9999999 if hprice_isnull else int(hprice_obj)

                    for i, x in df.iterrows():
                        price = int(x["price"])
                        if (lprice <= price) & (price <= hprice):  # gen-range
                            gen_countobj += self.extract_split(
                                self.preproc_txt(x["title"])
                            )
                        else:  # sus-range
                            sus_countobj += self.extract_split(
                                self.preproc_txt(x["title"])
                            )
                else:
                    for i, x in df.iterrows():
                        gen_countobj += Counter()  # placeholder to match idx
                        sus_countobj += self.extract_split(self.preproc_txt(x["title"]))

                # feedback_keyword()

                gen_countobjs.append(gen_countobj)
                sus_countobjs.append(sus_countobj)
                # bar.text("Extracting Keywords...")
                bar()
        dicts = []

        with alive_bar(2955) as bar:  # 648560
            for num, categ in enumerate(categs):
                dct = {}
                countobj = (
                    sus_countobjs[num] - gen_countobjs[num]
                )  # removing gen keywords from sus countobjs

                if categ in feedback_categs:
                    countobj = self.apply_feedbacks_keyword(countobj, categ)
                df = dfobjs[num]

                topfreq = countobj.most_common(len(countobj))

                keywords[num] = topfreq
                for tup in topfreq:
                    keyword = tup[0]
                    pidlist = []
                    for idx, row in df.iterrows():
                        if keyword in row.title:
                            pidlist.append(row["pid"])
                    dct[keyword] = list(set(pidlist))
                    # bar.text("Organizing output files..")
                    bar()
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
        extract keyword, appreancefreq with space split

        :return: Counter obj with keywords:count
        i.e.
            [('백인',23), ('이너백',11), ('핸드백',8)]
        """
        splitted = txt.split()
        # removing short words
        for i, v in enumerate(splitted):
            if len(v) < 2:
                splitted.pop(i)
        counter = Counter(splitted)
        return counter

    def apply_feedbacks_keyword(self, counter, categ):
        """
        deals with applying 'ignore' and 'effective' options from feedback
        """
        fb = self.feedback
        for item in fb[fb["categ"] == categ]["ignore"].values[0]:
            del counter[item]
            # ignore keywords: remove them
        for keyword in fb[fb["categ"] == categ]["effective"].values[0]:
            if keyword not in counter:
                counter[keyword] = 0
                # effective keywords: include in result even if it's null

        return counter


# for debug
if __name__ == "__main__":
    dataprice = pd.read_csv("./dataprice.csv")

    # extract keywords
    extractor = Extractor(dataprice)
    keywords = extractor.extract_keyword()
    with open("./cache/feedback.json", encoding="utf-8-sig") as json_file:
        prev_feedback = json.load(json_file)

    result = {
        "result": keywords,
        "previous-feedback": prev_feedback,
    }
    print("done!")

    with open("./cache/sample_result.json", "w", encoding="UTF-8-sig") as file:
        file.write(json.dumps(result, ensure_ascii=False))
