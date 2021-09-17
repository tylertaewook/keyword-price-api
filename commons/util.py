# -*- coding: utf-8 -*-
import pandas as pd
import pickle
import re
import csv
import os
from konlpy.tag import Okt
from collections import Counter

# region EDA


def classify(data, digit_match):
    """
    Classifies items in data into three distinct groups and returns the lists of corresponding ITEM_NOs

    :DataFrame data: df obj read from results
    :dict digit_match: dictionary that maps ITEM_NO -> [(LINEUP, NAME)]

    :return:
    - a: list(ITEM_NO) of 상품명에 name/lineup/code 모두 포함한 상품
    - b: list(ITEM_NO) of 상품명에 상기 3가지 모두 포함했으나 3가지 정보가 일치하지 않는 제품
    - c: list(ITEM_NO) of 상품명에 상기 3가지 중 2가지 이하의 정보만 포함하는 제품
    - trash: list(ITEM_NO) of 상품명의 codes는 존재하지만 gucci_bags1.csv에 포함되지 않는 제품
    """
    a, b, c, trash = ([] for i in range(4))

    for i, row in data.iterrows():
        title = row["title"]
        # extracting 5digit code with regex
        foundcode = search_code_ext(title)
        if foundcode in digit_match.keys():
            a.append(row["productId"])
        else:
            trash.append(row["productId"])

    length = [len(a), len(b), len(c)]
    length_ext = [len(trash)]
    print(f"Sample length: {len(data)}")
    print(f"groups[a,b,c]: {length}, sum: {sum(length)}")
    print(f"trash(es): {length_ext}, sum: {sum(length_ext)}")
    print(f"Do they sum up? -> {sum(length) + sum(length_ext) == len(data)}")
    print("")

    return a, b, c, trash


def search_code(text):
    """
    6-digit code type (i.e. 400249)
    """
    temp = re.search("\d{% s}" % 6, text)
    res = temp.group(0) if temp else ""
    return str(res)


def search_code_ext(text):
    """
    two group code type (i.e. 655658 17QDT)
    """
    temp = re.search("\d{6} [\dA-Z]{5}", text)
    res = temp.group(0) if temp else ""
    return str(res)


def manual_review(data, var, digit_match):
    passing = {}

    for i in var:
        title = str(data.loc[data["ITEM_NO"] == i]["TITLE"])
        temp = re.search("\d{% s}" % 5, title)
        res = temp.group(0) if temp else ""
        foundcode = str(res)

        print(f"TITLE: {i}||||{title}")
        print(f"CODE: {foundcode}")
        print(
            f"LINEUP: {digit_match[foundcode][0] if foundcode in digit_match.keys() else 0}"
        )
        print(
            f"NAME: {digit_match[foundcode][1] if foundcode in digit_match.keys() else 0}"
        )
        print("======================================================")

        ans = input("1 for pass, 2 for fail: ")
        if ans == 1:
            passing.append(i)
    return passing


def preprocessing(textlist):
    finallist = []
    for item in textlist:
        item = re.sub("[/{}()\[\]\b\d+\b]", "", item)
        item = re.sub("\u200b", "", item)
        item = re.sub("\xa0", "", item)
        item = re.sub("[ㄱ-ㅎㅏ-ㅣ]+", "", item)
        item = re.sub("[-=+,#/\?:^$.@*\"※~&%ㆍ!』\\‘|\(\)\[\]\<\>`'…》]", "", item)

        stopwords = [
            "gucci",
            "구찌",
            "다이애나",
            "홀스빗",
            "재키",
            "마몽",
            "마몬트",
            "디오니서스",
            "디오니소스",
            "오피디아",
            "패들락",
            "실비",
            "주미",
            "더블G",
            "미디엄",
            "미듐",
        ]
        querywords = item.split()

        resultwords = [word for word in querywords if word.lower() not in stopwords]
        result = " ".join(resultwords)

        finallist.append(result)
    return finallist


# endregion

# region print


def itemprint(data, obj, digit_match):
    """
    A convenient method that prints out TITLE,CODE,LINEUP, and NAME of ITEM_NOs in obj

    :DataFrame data: df obj read from results
    :list obj: list to traverse
    :dict digit_match: dictionary that maps ITEM_NO -> [(LINEUP, NAME)]
    """
    for i in obj:
        title = str(data.loc[data["ITEM_NO"] == i]["TITLE"])
        fullcode = search_code(title)
        foundcode = (
            fullcode[:5] + " " + fullcode[-5:] if fullcode[-5:] != "GUCCI" else ""
        )

        print(f"TITLE: {title}||||{i}")
        print(f"CODE: {foundcode}")
        print(
            f"LINEUP: {digit_match[foundcode][0] if foundcode in digit_match.keys() else 0}"
        )
        print(
            f"NAME: {digit_match[foundcode][1] if foundcode in digit_match.keys() else 0}"
        )
        print("======================================================")


def countprint(data, obj, digit_match):
    """
    A convenient method that prints out how many times each CODE appeared

    :DataFrame data: df obj read from results
    :list obj: list to traverse
    :dict digit_match: dictionary that maps ITEM_NO -> [(LINEUP, NAME)]
    """
    a_codes = []
    for i, row in data.iterrows():
        if row["productId"] in obj:
            a_codes.append(search_code(row["title"]))
    container = Counter(a_codes)
    checker = {}
    for k, v in container.items():
        print(k, ": ", v)
        checker[k] = v
    print("===================")
    print(f"{len(checker)} / {len(digit_match)} Keys Appeared")
    print("Total Sum = ", sum(checker.values()))


# endregion

# region utility


def save_var(var, file):
    """
    Saves the given variables to a file in current directory

    :list var: 2D list
    :str file: filename including extension
    """
    with open("saved_vars/" + file, "wb") as f:
        pickle.dump(var, f)


def generate_codeprice(genprods):
    codeprice = {}
    final_df = pd.DataFrame()

    # X = pd.read_csv('./data/gucci_bags_simp2.csv')
    X = genprods
    X_agg = X.groupby("CODE", as_index=False).agg({"PRICE": ["count", "sum"]})
    X_agg.columns = ["CODE", "sale_count", "selling_sum"]
    final_df = pd.concat([final_df, X_agg])
    final_df = final_df.groupby("CODE", as_index=False).agg(
        {"sale_count": "sum", "selling_sum": "sum"}
    )

    for i, row in final_df.iterrows():
        codeprice[row["CODE"]] = row["selling_sum"] / row["sale_count"]

    return codeprice


def mkdir_save(basedir, percent, filename, dic):
    iterdir = os.path.join(basedir, "{:.2f}".format(percent))
    os.makedirs(iterdir, exist_ok=True)

    with open(os.path.join(iterdir, filename), "w") as csv_file:
        writer = csv.writer(csv_file)
        for key, value in dic.items():
            writer.writerow([key, value])
    print(f"Successfully extracted and saved as {os.path.join(iterdir, filename)}")


# endregion

okt = Okt()


def extractOkt(txt, minfreq=3):
    """
     :return: Counter obj with keywords:count
    """
    noun = okt.nouns(txt)
    for i, v in enumerate(noun):
        if len(v) < 2:
            noun.pop(i)
    return Counter(noun)


def extractOkt_list(textlist):
    """
     :return: list(tuples) of (word, rank) sorted by most commons appearance frequency
    """
    final_counter = Counter()

    for string in textlist:
        final_counter.update(extractOkt(string))

    return final_counter.most_common()
