# -*- coding:utf-8 -*-
import boto3
from pymongo import MongoClient

# Prerequisite : pymongo, boto3

Target_DB = {
    "url": "mongodb://price_text1:Faikerz2960!#@7l6bj.vpc.mg.naverncp.com:17017/collected_items?replicaSet=fkz-img001",
    "port": 17017,
    "DB": "collected_items",
    "collection": "raw_products",
}


def sample_get_one():
    condition = {"name": "sample"}
    res = get_one(condition, Target_DB)
    print(res)


# DB_connect
def get_one(condition, Target_DB):
    client = MongoClient(Target_DB["url"])
    db = client[Target_DB["DB"]]
    res = db[Target_DB["collection"]].find_one(condition)
    return res


# ----

Storage_info = {
    "service_name": "s3",
    "endpoint_url": "https://kr.object.ncloudstorage.com",
    "region_name": "kr-standard",
    "access_key": "vExXlht5OiV0B1S24MMa",
    "secret_key": "GONb09KMyl5hwrydlTQYbCLo2DRhaIU2eEF9NFlH",
    "bucket_name": "web-images",
}


def sample_upload_one():
    image_path = "./test2.png"
    object_path = "price-spread/test2.png"
    upload_file(object_path, image_path, Storage_info)
    print("done:")


# storage_handler
def upload_file(object_path, file_path, Storage_info):
    s3 = boto3.client(
        Storage_info["service_name"],
        endpoint_url=Storage_info["endpoint_url"],
        aws_access_key_id=Storage_info["access_key"],
        aws_secret_access_key=Storage_info["secret_key"],
    )
    bucket_name = Storage_info["bucket_name"]

    s3.upload_file(file_path, bucket_name, object_path)


if __name__ == "__main__":
    sample_upload_one()
    ## uploaded file's URL = https://fkz-web-images.cdn.ntruss.com/price-spread/xxx.png
    ## uploaded files are accessible by ncp account desginated by admin (we will do this at later stage)
    ## But since the bucket itself is opened to the public, you can check if uploaded files are inside the bucket or not using 'https://kr.object.ncloudstorage.com/web-images/'

    sample_get_one()  # currently giving timeout error
    ## this code will work only on your ncp server as I allowed access from that server to cloud MongoDB
    ## checked out the code works well in the server.
    ## to directly access to mongo db, use mongo shell client (4.x) and mongodb:// address above from your server.
