# -*- coding: utf-8 -*-
import pandas as pd
import json

from commons.Classifier import Classifier
from commons.Extractor import Extractor


def generate_final(genprods, dataprice):
    classifier = Classifier(genprods)
    extractor = Extractor()
    print("Generating final.pkl file...")
    dct = classifier.classify_by_keywords(dataprice)
    final = classifier.classify_by_price(dataprice, dct, extractor.codeprice)
    return final


def extract(dp):
    """
    generate extractor and extract_keyword()
    """
    extractor = Extractor()
    result = extractor.extract_keyword_init(dp)
    return result


if __name__ == "__main__":

    dataprice = pd.read_csv("./dataprice.csv")
    result_json = extract("placeholder", dataprice)

    with open("result.json", "w", encoding="UTF-8-sig") as file:
        file.write(json.dumps(result_json, ensure_ascii=False))

    # with open("./test-json/parsed.json") as f:
    #     parsed = json.load(f)
    # genprods = pd.json_normalize(parsed["genprods"])  # df obj
    # dataprice = pd.json_normalize(parsed["dataprice"])

    # final = generate_final(genprods, dataprice)

    # final.to_pickle("./test-json/final.pkl")
    # genprods.to_pickle("./test-json/gp.pkl")

