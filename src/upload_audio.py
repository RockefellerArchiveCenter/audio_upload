#!/usr/bin/env python3

import logging
import tarfile
from os import getenv
from pathlib import Path
from shutil import rmtree

import bagit
import boto3
from aws_assume_role_lib import assume_role

logging.basicConfig(
    level=logging.INFO,
    format='%(filename)s::%(funcName)s::%(lineno)s %(message)s')
logging.getLogger("bagit").setLevel(logging.ERROR)


def main(refid, aws_role_arn, aws_bucket_name, root_dir):
    """Main method which calls all other submethods."""

    package_root_path = Path(root_dir, refid)

    if package_root_path.is_dir():
        logging.info(f"Processing package {refid} located at {package_root_path}")
        remove_unwanted_files(package_root_path)
        create_bag(str(package_root_path))
        tarball_path = create_tarball(package_root_path)
        upload_package(tarball_path, aws_bucket_name, aws_role_arn)
    else:
        logging.info(f"Package {refid} does not exist at {package_root_path}, skipping")


def remove_unwanted_files(dir_path):
    """Removes unwanted files from directory.

    Args:
        dir_path (pathlib.Path): directory from which files should be removed.
    """
    for fp in dir_path.rglob("*"):
        if fp.name in ["Thumbs.db", ".DS_Store"]:
            fp.unlink()
    logging.info(f"Unwanted files removed from {dir_path}")


def create_bag(dir):
    """Creates BagIt bag from directory.

    Args:
        dir (str): Path to directory to be bagged
    """
    bagit.make_bag(dir)
    logging.info(f"Bag created for package {dir}")


def create_tarball(dir_path):
    """Create tarball from bagged path.

    Args:
        dir_path (pathlib.Path): path of digital object to tarball

    Returns:
        tar_path (pathlib.Path): path to tarball
    """
    tar_path = dir_path.with_name(f"{dir_path.name}.tar.gz")
    with tarfile.open(tar_path, "w:gz") as tf:
        tf.add(dir_path, arcname=dir_path.name)
    rmtree(dir_path)
    logging.info(f"Tarball created at {tar_path}")
    return tar_path


def upload_package(tarball_path, aws_bucket_name, aws_role_arn):
    """Uploads package to S3 bucket.

    Args:
        tarball_path (pathlib.Path): Path of file to upload.
        aws_bucket_name (str): name of S3 bucket to upload files to
        aws_role_arn (str): Name of AWS role to assume in session
    """
    session = boto3.Session()
    assumed_role_session = assume_role(session, aws_role_arn)
    s3_client = assumed_role_session.client('s3', region_name='us-east-1')
    s3_client.upload_file(str(tarball_path), aws_bucket_name, tarball_path.name)
    logging.info(f"Package {tarball_path} uploaded to {aws_bucket_name}")


if __name__ == '__main__':
    refid = getenv('REFID')
    aws_role_arn = getenv('AWS_ROLE_ARN')
    aws_bucket_name = getenv('AWS_BUCKET_NAME')
    root_dir = getenv('ROOT_DIR')
    main(
        refid,
        aws_role_arn,
        aws_bucket_name,
        root_dir)
