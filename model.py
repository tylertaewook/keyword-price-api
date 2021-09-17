# -*- coding: utf-8 -*-
import pandas as pd
import os

from commons.Classifier import Classifier
from commons.Extractor import Extractor


def generate_final(genprods, dataprice):
    classifier = Classifier(genprods)
    extractor = Extractor(genprods)
    print("Generating final.pkl file...")
    dct = classifier.classify_by_keywords(dataprice)
    final = classifier.classify_by_price(dataprice, dct, extractor.codeprice)
    return final


def extract(genprods, final, raw=False, keyword_num=10):
    extractor = Extractor(genprods)
    if raw:
        result_raw = extractor.extractkeyword_raw(final, n=keyword_num)
        return result_raw
    else:
        result_proc = extractor.extractkeyword_proc(final, n=keyword_num)
        return result_proc
