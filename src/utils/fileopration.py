'''
实现文件/目录操作,hash操作
'''
import shutil
import os
import pathlib
from pathlib import Path
import hashlib
import xxhash
import json
import rtoml
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue
import threading
from typing import List, Dict, Sequence


def _to_path(path: str | os.PathLike) -> Path:
    """将输入路径转换为Path对象
    
    Args:
        path: 输入的路径，可以是字符串或PathLike对象
        
    Returns:
        Path: 返回转换后的Path对象
    """
    return Path(path)


def copy_file(src: str | os.PathLike, dst: str | os.PathLike, base_dir: str | os.PathLike | None = None):
    src = _to_path(src)
    dst = _to_path(dst)
    if base_dir is not None:
        src = _to_path(base_dir) / src
        dst = _to_path(base_dir) / dst
    if dst.exists():
        raise FileExistsError("Destination file already exists")
    shutil.copy(str(src), str(dst))

def overwrite_file(src: str | os.PathLike, dst: str | os.PathLike, base_dir: str | os.PathLike | None = None):
    src = _to_path(src)
    dst = _to_path(dst)
    if base_dir is not None:
        src = _to_path(base_dir) / src
        dst = _to_path(base_dir) / dst
    shutil.copy(str(src), str(dst))

def delete_file(file_path: str | os.PathLike, base_dir: str | os.PathLike | None = None):
    file_path = _to_path(file_path)
    if base_dir is not None:
        file_path = _to_path(base_dir) / file_path
    if file_path.exists():
        file_path.unlink()

def replace_file(src: str | os.PathLike, dst: str | os.PathLike, base_dir: str | os.PathLike | None = None, 
                 keep_old: bool = False, old_flag: str = ".old"):
    src = _to_path(src)
    dst = _to_path(dst)
    if base_dir is not None:
        src = _to_path(base_dir) / src
        dst = _to_path(base_dir) / dst
    if dst.exists():
        if keep_old:
            dst.rename(dst.with_suffix(dst.suffix + old_flag))
        else:
            dst.unlink()
    shutil.copy(str(src), str(dst))


class FileHash:
    """文件哈希计算类，提供多种哈希算法来计算文件或目录的哈希值"""

    DEFAULT_CHUNK_SIZE = -1
    _hash_type = "sha256"

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
        """初始化FileHash实例
            
        Args:
            hash_type: 哈希算法类型，默认为"sha256"
            
        Raises:
            ValueError: 当hash_type不在支持的算法列表中时抛出异常
        """
        if hash_type not in self._HASH_ALGO.keys():
            raise ValueError(f"hash_type must be {self._HASH_ALGO.keys()}")
        else:
            self._hash_type = hash_type

    def hash_file(self, file_path: str | os.PathLike, base_dir: str | os.PathLike | None = None, 
                  hash_type = _hash_type , chunk_size=DEFAULT_CHUNK_SIZE) -> str:
        """计算单个文件的哈希值
            
        Args:
            file_path: 文件路径
            base_dir: 基础目录路径，可选
            hash_type: 哈希算法类型
            chunk_size: 读取块大小，默认为-1表示全部读取
            
        Returns:
            str: 计算出的哈希值的十六进制字符串表示
        """
        hash_obj = self._HASH_ALGO[hash_type]()
        file_path = _to_path(file_path)
        if base_dir is not None:
            file_path = _to_path(base_dir) / file_path
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(chunk_size), b""):
                hash_obj.update(chunk)
        return hash_obj.hexdigest()

    def stream_hash_many(self,
                         paths: List[str]|List[os.PathLike]|str|os.PathLike,
                         hash_type = _hash_type,
                         chunk_size=DEFAULT_CHUNK_SIZE
                         ) -> str|Dict[str, str]:
        """批量计算多个文件或整个目录的哈希值，顺序读取方式
            
        Args:
            paths: 文件路径列表或目录路径，当传入str或PathLike时视为目录路径并计算整个目录哈希；
                   当传入列表时视为多个文件路径并分别计算哈希
            hash_type: 哈希算法类型
            chunk_size: 读取块大小
            
        Returns:
            str|Dict[str, str]: 如果输入为目录路径，返回目录的整体哈希值；
                               如果输入为文件路径列表，返回文件路径到哈希值的字典
        """
        # 检查是否为单一路径（字符串或PathLike），如果是则调用文件夹哈希逻辑
        if isinstance(paths, (str, os.PathLike)):
            dir_path = _to_path(paths)
            hash_obj = self._HASH_ALGO[hash_type]()
            for root, dirs, files in os.walk(str(dir_path)):
                for file in sorted(files):
                    file_path = Path(root) / file
                    hash_obj.update(self.hash_file(file_path, Path(''), hash_type, chunk_size).encode())
            return hash_obj.hexdigest()
        
        # 否则按单独的文件哈希逻辑处理
        paths = [Path(path).resolve() for path in paths]
        hash_obj = self._HASH_ALGO[hash_type]()
        result = {}
        for path in paths:
            result[str(path)] = self.hash_file(path, None, hash_type, chunk_size)
        return result

    def threaded_hash_many(
            self,
            paths: List[str]|List[os.PathLike]|str|os.PathLike,
            hash_type = _hash_type,
            chunk_size=DEFAULT_CHUNK_SIZE,
            max_workers=4,
            white_list: str | List[str] | None = None
            ) -> str|Dict[str, str]:
        """批量计算多个文件或整个目录的哈希值，多线程并发方式
            
        Args:
            paths: 文件路径列表或目录路径，当传入str或PathLike时视为目录路径并计算整个目录哈希；
                   当传入列表时视为多个文件路径并分别计算哈希
            hash_type: 哈希算法类型
            chunk_size: 读取块大小
            max_workers: 最大线程数，默认为4
            white_list: 白名单，指定哪些文件需要被忽略，支持正则表达式或文件名列表
            
        Returns:
            str|Dict[str, str]: 如果输入为目录路径，返回目录的整体哈希值；
                               如果输入为文件路径列表，返回文件路径到哈希值的字典
        """
        # 检查是否为单一路径（字符串或PathLike），如果是则调用文件夹哈希逻辑
        if isinstance(paths, (str, os.PathLike)):
            dir_path = _to_path(paths)
            if isinstance(white_list, str):
                regex = re.compile(white_list)
            elif isinstance(white_list, list):
                regex = None
            elif white_list is None:
                white_list = []
                regex = None
            else:
                raise ValueError("white_list must be a string, list or None")
            hash_obj = self._HASH_ALGO[hash_type]()
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures_to_file = {}
                results = {}
                for root, dirs, files in os.walk(str(dir_path)):
                    for file in files:
                        if regex:
                            if not regex.match(file):
                                continue
                        elif file in white_list:
                            continue
                        file_path = Path(root) / file
                        futures_to_file[executor.submit(self.hash_file, file_path, None, hash_type, chunk_size)] = str(file_path)
                for future in as_completed(futures_to_file):
                    results[futures_to_file[future]] = future.result().encode()
                for file in sorted(results.keys()):
                    hash_obj.update(results[file])
            return hash_obj.hexdigest()
        
        # 否则按单独的文件哈希逻辑处理
        paths = [Path(path).resolve() for path in paths]
        if isinstance(white_list, str):
            regex = re.compile(white_list)
        elif isinstance(white_list, list):
            regex = None
        elif white_list is None:
            white_list = []
            regex = None
        else:
            raise ValueError("white_list must be a string, list or None")
        hash_obj = self._HASH_ALGO[hash_type]()
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures_to_file = {}
            results = {}
            for path in paths:
                file_name = path.name # type: ignore
                if regex:
                    if not regex.match(file_name):
                        continue
                elif file_name in white_list:
                    continue
                futures_to_file[executor.submit(self.hash_file, path, None, hash_type, chunk_size)] = str(path)
            for future in as_completed(futures_to_file):
                results[futures_to_file[future]] = future.result()
        return results
    
    def stream_hash_folder(self,
                           dir_path: str | os.PathLike,
                           base_dir: str | os.PathLike | None = None,
                           hash_type = _hash_type,
                           chunk_size=DEFAULT_CHUNK_SIZE
                           ) -> str:
        """计算整个目录的哈希值，顺序读取方式
            
        Args:
            dir_path: 目录路径
            base_dir: 基础目录路径，可选
            hash_type: 哈希算法类型
            chunk_size: 读取块大小
            
        Returns:
            str: 计算出的目录整体哈希值
        """
        # 调用更新后的stream_hash_many方法
        if base_dir is not None:
            dir_path = _to_path(base_dir) / dir_path
        return self.stream_hash_many(dir_path, hash_type, chunk_size)  # type: ignore
    
    def threaded_hash_folder(
            self,
            dir_path: str | os.PathLike,
            base_dir: str | os.PathLike | None = None,
            hash_type = _hash_type,
            chunk_size=DEFAULT_CHUNK_SIZE,
            max_workers=4,
            white_list: str | List[str] | None = None
            ) -> str:
        """计算整个目录的哈希值，多线程并发方式
            
        Args:
            dir_path: 目录路径
            base_dir: 基础目录路径，可选
            hash_type: 哈希算法类型
            chunk_size: 读取块大小
            max_workers: 最大线程数，默认为4
            white_list: 白名单，指定哪些文件需要被忽略，支持正则表达式或文件名列表
            
        Returns:
            str: 计算出的目录整体哈希值
        """
        # 调用更新后的threaded_hash_many方法
        if base_dir is not None:
            dir_path = _to_path(base_dir) / dir_path
        return self.threaded_hash_many(dir_path, hash_type, chunk_size, max_workers, white_list)  # type: ignore
