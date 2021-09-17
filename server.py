# -*- coding: utf-8 -*-

import pandas as pd
import os
import json
from model import generate_final, extract
from flask import Flask, request


app = Flask(__name__)


@app.route("/", methods=["GET"])
def check_status():
    return "STATUS: ONLINE"


# receive genprods, dataprice JSON
@app.route("/v1/resources/data", methods=["POST", "GET"])
def read_jsons():
    request_data = request.get_json()
    genprods = pd.json_normalize(request_data["genprods"])  # df obj
    dataprice = pd.json_normalize(request_data["dataprice"])  # df obj

    final = generate_final(genprods, dataprice)  # TODO: part that takes a long time

    final.to_pickle("./test-json/final.pkl")
    genprods.to_pickle("./test-json/genprod.pkl")

    return "success"


# return raw.json
@app.route("/v1/resources/result/raw", methods=["GET"])
def result_raw():
    final = pd.read_pickle("./test-json/final.pkl")
    genprods = pd.read_pickle("./test-json/gcbag.pkl")

    result_raw = extract(genprods, final, raw=True)
    return json.dumps(result_raw, ensure_ascii=False, indent=4)


# return proc.json
@app.route("/v1/resources/result/proc", methods=["GET"])
def result_proc():
    final = pd.read_pickle("./test-json/final.pkl")
    genprods = pd.read_pickle("./test-json/genprod.pkl")
    print(type(final))
    print(type(genprods))

    result_proc = extract(genprods, final)
    return json.dumps(result_proc, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    # access with http://175.106.99.99:16758/
    app.run(host="192.168.1.100", debug=True, port=16758)
