# -*- coding: utf-8 -*-
import pandas as pd
import os
import datetime
import json
import csv


class Saver:
    """
    class responsible for creating directory and save result files

    Attributes:
        home (str): directory of repository home
        rundir (str): directory of results folder for this run
    """

    def __init__(self):
        """creates YYYY-MM-DD_HH-MM-SS results folder"""
        # self.home = "/Users/tylerkim/Documents/GitHub/price-text"
        self.home = os.getcwd()
        # os.chdir(self.home)
        self.rundir = os.path.join(
            self.home, "results", datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        )
        if not os.path.exists(self.rundir):
            os.mkdir(self.rundir)

    def mkdir_save(self, title, filename, df, emptA, emptB):
        """
        creates 'title' directory and saves a DataFrame as filename.csv
        """
        iterdir = os.path.join(self.rundir, title)
        os.makedirs(iterdir, exist_ok=True)

        df.to_csv(os.path.join(iterdir, filename))
        self.list_to_txt(iterdir, "emptyA.txt", emptA)
        self.list_to_txt(iterdir, "emptyB.txt", emptB)
        print(f"saved as {os.path.join(iterdir, filename)}")

    def dict_to_csv(self, filename, dic):
        with open(os.path.join(self.rundir, filename), "w") as csv_file:
            writer = csv.writer(csv_file)
            for key, value in dic.items():
                writer.writerow([key, value])
        print(f"saved as {os.path.join(self.rundir, filename)}")

    def df_to_csv(self, filename, df):
        df.to_csv(os.path.join(self.rundir, filename))
        print(f"saved as {os.path.join(self.rundir, filename)}")

    def list_to_txt(self, iterdir, filename, ls):
        with open(os.path.join(iterdir, filename), "w") as listfile:
            for element in ls:
                listfile.write(element + "\n")
        print(f"saved as {os.path.join(iterdir, filename)}")

    def dump_json(self, filename, data):
        with open(os.path.join(self.rundir, filename), "w", encoding="UTF-8") as f:
            json.dump(data, f, ensure_ascii=False)
        print(f"file dumped as {filename}")
