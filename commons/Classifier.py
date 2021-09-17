import pandas as pd
import re

from alive_progress import alive_bar

lineup_map = {
    "구찌 다이애나": ["다이애나"],
    "재키 1961": ["재키", "1961"],
    "구찌 1955 홀스빗": ["홀스빗", "1955"],
    "구찌 홀스빗 1955": ["홀스빗", "1955"],
    "GG 마몽": ["마몽", "마몬트", "마몽"],
    "디오니서스": ["디오니서스", "디오니소스", "디오니수스"],
    "오피디아": ["오피디아"],
    "실비": ["실비"],
    "구찌 주미": ["주미"],
    "패들락": ["패들락", "패드락", "페들락", "페드락"],
    "더블G": ["더블G"],
}


class Classifier:
    """class responsible for cleaning, classifying, and prepping original data

    refer to [price-text/classifier.py] for its uses

    Attributes:
        home (str): directory of repository home
        genprods (df): ./gucci_bags.csv
        genprods_simp (df): ./gucci_bags_simp2.csv
        sample (df): ./gucci_data_price.csv
        transliter (obj): object from hangul_romanizer
        soundex (obj): soundex object
        digitmatch (dict): {CODE: tuple(lineup_alt, split_titles)}
    """

    def __init__(self, genprods):
        self.genprods = genprods
        # {CODE: tuple(lineup_alt, split_titles)}
        self.digitmatch = self.generate_titles()

    def classify_by_keywords(self, data):
        """
        Classifies items in data into three distinct groups and returns the lists of corresponding ITEM_NOs

        :DataFrame data: df obj read from results
        :dict digit_match: dictionary that maps ITEM_NO -> [(LINEUP, NAME)]
        i.e.
            {"400249 TLK88": ['디오니소스', '토킨백']}
            {"652439 POSLI": ['페드락', '토트백']}

        :return: dct | dict(MODELCODE) 상품명에 name/lineup/code 중 하나 포함한 상품
        i.e.
            {"400249 TLK88": [12345678, 12345678, 12345678, 12345678]}
            {"652439 POSLI": [12345678, 12345678, 12345678, 12345678]}
        """
        idx = []
        idx3 = []
        dct = {}
        dm = self.digitmatch  # for easier reference

        with alive_bar(len(data)) as bar:
            for i, row in data.iterrows():
                title = row["TITLE"]
                code = self.search_code(title)
                # full code exists in title
                if code in self.digitmatch.keys():
                    idx.append(row["PID"])
                    if code not in dct.keys():
                        dct[code] = []
                    dct[code].append(row["PID"])
                # can't rely on model code
                else:
                    # partial (6dig) codes
                    pcode = self.search_code(title, full=False)
                    plist = [
                        fullcode for fullcode in dm.keys() if fullcode[:6] == pcode
                    ]
                    # for all code with the same first 6 digits
                    for code in plist:
                        # if includes one of model name
                        if any(model_alt in title for model_alt in dm[code][0]):
                            # if includes all of product keywords
                            if all(prod_name in title for prod_name in dm[code][1]):
                                idx.append(row["PID"])
                                if code not in dct.keys():
                                    dct[code] = []
                                dct[code].append(row["PID"])
                                break
                bar("classifying by keywords...")
        # sort remaining items to idx3 (heavy compute load; uncomment when needed)
        # with alive_bar(len(data)) as bar:
        #     for i, row in data.iterrows():
        #         if row["productId"] not in idx and row["productId"] not in idx2:
        #             idx3.append(row["productId"])
        #         bar()

        print(f"Usable Data: {len(idx)} / {len(data)}")
        print(f"Unusable Data: {len(idx3)} / {len(data)}")
        print("")

        return dct

    def classify_by_price(self, data, dct, codeprice):
        """
        Classifies items in data into five groups and return the cleaned DataFrame object.

        :DataFrame data: df obj
        :dict dct: 
        :dict codeprice: 

        :return: DataFrame final | columns=["pid", "title", "price", "code", "group"]
        i.e.
            |  pid  | title | price |     code     | group |
            | 12345 | "bla" | 12345 | 400249 TLK88 |   a   |
            | 67890 | "bla" | 12345 | 654249 ASD99 |   b   |
            | 12323 | "bla" | 12345 | 654249 ASD99 |   c   |
        """

        colnames = ["pid", "title", "price", "code", "group"]
        final = pd.DataFrame(columns=colnames)
        # final.set_index("pid")
        with alive_bar(len(dct)) as bar:
            for model in dct.keys():
                genprice = codeprice[model]
                for pid in dct[model]:
                    series = data.loc[data["PID"] == pid]
                    title = series["TITLE"].to_string(index=False)
                    price = int(series.PRICE)

                    # price range
                    if price < genprice * 0.25:
                        group = "a"
                    elif price < genprice * 0.5:
                        group = "b"
                    elif price < genprice * 0.80:
                        group = "c"
                    elif price < genprice:
                        group = "d"
                    else:
                        group = "e"

                    rowDict = {
                        "pid": pid,
                        "title": title,
                        "price": price,
                        "code": model,
                        "group": group,
                    }
                    rowSeries = pd.Series(rowDict, name=pid)

                    final = final.append(rowSeries)
                bar("classifying by price...")
        return final

    def generate_titles(self):
        """
        generates dict titles containing alternative lineup names and space-splitted product names

        :return: dict titles | {CODE: tuple(lineup_alt, split_titles)}
        - lineup_alt: acceptable alternatives to lineup(마몽, 마몬트, etc)
        - split_titles: NAME(KOR).split()
        i.e.
            {621220 92TCG: (['홀스빗', '1955'], ['스몰', '탑', '핸들백'])}
        """
        titles = {}
        simp = self.genprods
        # TITLE (ENG), LINEUP (KOR), NAME(KOR)
        for i, x in simp.iterrows():
            titles[x.CODE] = (lineup_map[x["LINEUP(KOR)"]], x["NAME(KOR)"].split())
        return titles

    def search_code(self, text, full=True):
        """
        searches for code in given text
        full=True: 655658 17QDT
        full=False: 655658
        """
        if full:
            temp = re.search("\d{6} [\dA-Z]{5}", text)
        else:
            temp = re.search("\d{% s}" % 6, text)
        res = temp.group(0) if temp else ""
        return str(res)

