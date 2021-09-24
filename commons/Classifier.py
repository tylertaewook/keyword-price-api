import pandas as pd
import re

from alive_progress import alive_bar


class Classifier:
    """class responsible for cleaning, classifying, and prepping original data


    Attributes:
        home (str): directory of repository home
    """

    def __init__(self, genprods):
        raise NotImplementedError

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
        idx2 = []
        dct = {}

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
        print(f"Ignoring Data: {len(idx2)} / {len(data)}")
        print("")

        return dct

    def classify_by_price(self, data, cat="cat4"):
        """
        Classifies items in data into five groups and return the cleaned DataFrame object.

        :DataFrame data: df obj
        :dict dct: 
        :dict codeprice: 

        :return: DataFrame final | columns=["pid", "title", "price", "cat", "group"]
        i.e.
            |  pid  | title | price |  cat   | group |
            | 12345 | "bla" | 12345 | 자동우산 |   a   |
            | 67890 | "bla" | 12345 | 손목장갑 |   b   |
            | 12323 | "bla" | 12345 | 골프잡화 |   c   |
        """

        colnames = ["pid", "title", "price", "code", "group"]
        final = pd.DataFrame(columns=colnames)

        categs = data.cat.dropna().unique()

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

