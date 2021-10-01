import pandas as pd
import numpy as np
import seaborn
import boto3
import matplotlib.pyplot as plt


class Visualizer:
    """
    class responsible for visualizing categories' price range, upload to s3 obj. storage, and generate json file

    Attributes:
        dataprice (DataFrame): csv data
        categs (list): list of categories(str)
        storage_info (dict): information about s3 obj storage
    """

    def __init__(self, col):
        """place holder"""
        self.dataprice = pd.read_csv("./dataprice.csv")
        self.col = col
        self.categs = self.dataprice[col].dropna().unique()
        # FIXME: preventing exception caused by link in price column
        self.categs = self.categs[self.categs != "골프의류"]

        self.storage_info = {
            "service_name": "s3",
            "endpoint_url": "https://kr.object.ncloudstorage.com",
            "region_name": "kr-standard",
            "access_key": "vExXlht5OiV0B1S24MMa",
            "secret_key": "GONb09KMyl5hwrydlTQYbCLo2DRhaIU2eEF9NFlH",
            "bucket_name": "web-images",
        }

    def generate_graph(self, categ):
        """
        generates vertical boxplot of price range(s)
        """
        df = self.dataprice[self.dataprice[self.col] == categ]

        plt.figure(figsize=(10, 15))
        seaborn.set(
            font="AppleGothic", rc={"axes.unicode_minus": False}, style="darkgrid"
        )

        bp = seaborn.boxplot(y=df["price"].astype(int))
        bp.set_xlabel(categ, fontsize=20)

        plt.savefig(f"./imgs/{categ}.png")

    def upload_file(self, categ):
        """
        generate & upload img file to s3 objective storage and return link
        """

        file_path = f"./imgs/{categ}.png"
        object_path = f"price-spread/{categ}.png"

        s3 = boto3.client(
            self.storage_info["service_name"],
            endpoint_url=self.storage_info["endpoint_url"],
            aws_access_key_id=self.storage_info["access_key"],
            aws_secret_access_key=self.storage_info["secret_key"],
        )
        bucket_name = self.storage_info["bucket_name"]

        s3.upload_file(file_path, bucket_name, object_path)

        img_link = "https://fkz-web-images.cdn.ntruss.com/" + object_path
        return img_link

    def generate_dict(self):
        """
        generate ready-to-json-dump dictionary of img links

        :return: imgDict | {category : link}
        i.e.
            {
                "골프장갑": 'https://fkz-web-images.cdn.ntruss.com/price-spread/xxx.png',
                "마스크": 'https://fkz-web-images.cdn.ntruss.com/price-spread/xxx.png',
                "생활용품": 'https://fkz-web-images.cdn.ntruss.com/price-spread/xxx.png',
            }
        """
        imgDict = {}

        for categ in self.categs:
            categ = categ.replace("/", "_")
            self.generate_graph(categ)

            imgDict[categ] = self.upload_file(categ)

        return imgDict
