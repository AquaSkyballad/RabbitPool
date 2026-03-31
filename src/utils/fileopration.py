'''
实现文件/目录操作,json操作
'''
import shutil
import os
import pathlib
import hashlib
import xxhash
import json
import rtoml
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue
import threading
from typing import Union, List, Tuple, Dict


def copy_file(src, dst, base_dir=None):
    if base_dir is not None:
        src = os.path.join(base_dir, src)
        dst = os.path.join(base_dir, dst)
    if os.path.exists(dst):
        raise FileExistsError("Destination file already exists")
    shutil.copy(src, dst)

def overwrite_file(src, dst, base_dir=None):
    if base_dir is not None:
        src = os.path.join(base_dir, src)
        dst = os.path.join(base_dir, dst)
    shutil.copy(src, dst)

def delete_file(file_path, base_dir=None):
    if base_dir is not None:
        file_path = os.path.join(base_dir, file_path)
    if os.path.exists(file_path):
        os.remove(file_path)

def replace_file(src, dst, base_dir=None, keep_old=False, old_flag=".old"):
    if base_dir is not None:
        src = os.path.join(base_dir, src)
        dst = os.path.join(base_dir, dst)
    if os.path.exists(dst):
        if keep_old:
            shutil.move(dst, dst + old_flag)
        else:
            os.remove(dst)
    shutil.copy(src, dst)


class FileHash:

    _HASH_ALGO = {
        # hashlib
        "sha512": hashlib.sha512,
        "sha256": hashlib.sha256,
        "sha1": hashlib.sha1,
        "md5": hashlib.md5,
        # xxhash
        "xxh128": xxhash.xxh128,
        "xxh64": xxhash.xxh64,
        "xxh32": xxhash.xxh32,
        "xxh3_128": xxhash.xxh3_128,
        "xxh3_64": xxhash.xxh3_64,

    }
    def __init__(self, hash_type="sha256") -> None:
            if hash_type not in self._HASH_ALGO.keys():
                    raise ValueError(f"hash_type must be {self._HASH_ALGO.keys()}")
            else:
                self._hash_type = hash_type

    def hash_file(self, file_path, base_dir=None, chunk_size=8192) -> str:
        hash_obj = self._HASH_ALGO[self._hash_type]()
        if base_dir is not None:
            file_path = os.path.join(base_dir, file_path)
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(chunk_size), b""):
                hash_obj.update(chunk)
        return hash_obj.hexdigest()

    def stream_hash_folder(self, dir_path, base_dir=None, chunk_size=8192) -> str:
        if base_dir is not None:
            dir_path = os.path.join(base_dir, dir_path)
        hash_obj = self._HASH_ALGO[self._hash_type]()
        for root, dirs, files in os.walk(dir_path):
            for file in sorted(files):
                file_path = os.path.join(root, file)
                hash_obj.update(self.hash_file(file_path, '', chunk_size).encode())
        return hash_obj.hexdigest()

    def threaded_hash_folder(
            self,
            dir_path,
            base_dir=None,
            chunk_size=8192,
            max_workers=4,
            white_list: Union[str, List[str], None] = None
            ) -> str:
        if base_dir is not None:
            dir_path = os.path.join(base_dir, dir_path)
        if isinstance(white_list, str):
            regex = re.compile(white_list)
        elif isinstance(white_list, list):
            regex = None
        elif white_list is None:
            white_list = []
            regex = None
        else:
            raise ValueError("white_list must be a string, list or None")
        hash_obj = self._HASH_ALGO[self._hash_type]()
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures_to_file = {}
            results = {}
            for root, dirs, files in os.walk(dir_path):
                for file in files:
                    if regex:
                        if not regex.match(file):
                            continue
                    elif file in white_list:
                        continue
                    file_path = os.path.join(root, file)
                    futures_to_file[executor.submit(self.hash_file, file_path, None, chunk_size)] = file
            for future in as_completed(futures_to_file):
                results[futures_to_file[future]] = future.result().encode()
            for file in sorted(results.keys()):
                hash_obj.update(results[file])
        return hash_obj.hexdigest()