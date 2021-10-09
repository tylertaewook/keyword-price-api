# -*- coding: utf-8 -*-
import pandas as pd
import json
from flask import Flask, request

from commons.Extractor import Extractor
from commons.Visualizer import Visualizer

app = Flask(__name__)


@app.route("/", methods=["GET"])
def check_status():
    # TODO: replace with telegram bot function
    return "STATUS: ONLINE"


# receive genprods, dataprice JSON
@app.route("/api/v1/feedback", methods=["POST"])
def read_feedback():
    """read user's feedback and save as json files for later access"""

    request_data = request.get_json()

    df = pd.json_normalize(request_data)
    df.to_pickle("./cache/feedback.pkl")

    with open("./cache/feedback.json", "w", encoding="UTF-8-sig") as file:
        file.write(json.dumps(request_data, ensure_ascii=False))

    return "received feedback"


# return raw.json
@app.route("/api/v1/results/keyword", methods=["GET"])
def get_keywords():
    """
    return keywords/frequency/list of product as json

    - clean data to product final.pkl
    - look for available feedback and perform keyword extraction
    """
    # access db (csv for now)
    dataprice = pd.read_csv("./dataprice.csv")

    # check for available feedback

    # extract keywords
    extractor = Extractor(dataprice)
    keywords = extractor.extract_keyword()
    with open("./cache/feedback.json", encoding="utf-8-sig") as json_file:
        prev_feedback = json.load(json_file)

    result = {
        "result": keywords,
        "previous-feedback": prev_feedback,
    }
    return json.dumps(result, ensure_ascii=False, indent=4)


# return proc.json
@app.route("/api/v1/results/price-spread", methods=["GET"])
def get_pricespread():
    """
    return price spread information

    :return: linktab - json of {category : img-link}
            -----------------------------------
            {
                "골프장갑": 'https://fkz-web-images.cdn.ntruss.com/price-spread/xxx.png',
                "마스크": 'https://fkz-web-images.cdn.ntruss.com/price-spread/xxx.png',
                "생활용품": 'https://fkz-web-images.cdn.ntruss.com/price-spread/xxx.png',
            }
            -----------------------------------
        
    """
    viz = Visualizer(col="cat4")
    linktab = viz.generate_dict()

    result = {}

    return json.dumps(linktab, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    # access with http://175.106.99.99:16758/
    app.run(host="192.168.1.100", debug=True, port=16758)
