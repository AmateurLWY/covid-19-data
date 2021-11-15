"""Most logic from:
https://github.com/owid/walden/blob/master/owid/walden/owid_cache.py
"""

import os
import tempfile
from os import path
from typing import Optional, Type, Union
import logging

import pandas as pd
import boto3
from botocore.exceptions import ClientError


SPACES_ENDPOINT = "https://nyc3.digitaloceanspaces.com"


def df_to_s3(
    df: pd.DataFrame,
    relative_path: Union[str, list],
    bucket_name: str = "covid-19",
    public: bool = False,
    extension: str = "csv",
    **kwargs,
) -> Optional[str]:
    with tempfile.TemporaryDirectory() as f:
        output_path = os.path.join(f, f"file.{extension}")
        if extension == "csv":
            df.to_csv(output_path, index=False, **kwargs)
        elif extension == "xlsx":
            df.to_excel(output_path, index=False, engine="xlsxwriter", **kwargs)
        else:
            raise ValueError(f"Unknown extension {extension}. Only use csv or xlsx!")
        upload_to_s3(output_path, relative_path, bucket_name, public)


def upload_to_s3(
    filename: Union[str, list], relative_path: Union[str, list], bucket_name: str = "covid-19", public: bool = False
) -> Optional[str]:
    """
    Upload file to Walden.
    Args:
        local_path (str): Local path to file. It can be a list of paths, should match `s3_path`'s length.
        s3_path (str): Path where to store the file in the S3 bucket. It can be a list of paths, should match
                        `local_path`'s length.
        bucket_name (str): Name of the S3 bucket. Defaults to "covid-19".
        public (bool): Set to True to expose the file to the public (read only). Defaults to False.
    """
    print("Uploading to S3…")
    # Checks
    if type(filename) is not type(relative_path):
        raise TypeError("`filename` and `relative_path` should be of the same type")
    if isinstance(filename, list):
        if len(filename) == len(relative_path):
            raise TypeError("`filename` and `relative_path` should be of same length")
    elif not isinstance(filename, str):
        raise TypeError("`filename` and `relative_path` should be of type str or list")

    extra_args = {"ACL": "public-read"} if public else {}

    client = connect()
    try:
        client.upload_file(filename, bucket_name, relative_path, ExtraArgs=extra_args)
    except ClientError as e:
        logging.error(e)
        raise UploadError(e)

    return None


def connect(profile_name="default"):
    "Return a connection to Walden's DigitalOcean space."
    check_for_default_profile()

    session = boto3.Session(profile_name=profile_name)
    client = session.client(
        service_name="s3",
        endpoint_url=SPACES_ENDPOINT,
    )
    return client


def check_for_default_profile():
    filename = path.expanduser("~/.aws/config")
    if not path.exists(filename) or "[default]" not in open(filename).read():
        raise FileExistsError(
            """you must set up a config file at ~/.aws/config
            it should look like:
            [default]
            aws_access_key_id = ...
            aws_secret_access_key = ...
            """
        )


class UploadError(Exception):
    pass
