import os.path
import sqlite3
import json
import requests
import aiohttp
import zipfile

from SharkBot import Errors, Utils

# Constants

_MANIFEST_FOLDER = "data/live/bungie/manifest"
_MANIFEST_FILE = "data/live/bungie/manifest/manifest.json"
_ZIP_TARGET = _MANIFEST_FOLDER + "/manifest.zip"
_CONTENT_FILE = _MANIFEST_FOLDER + "/manifest.content"
_BASE_URL = "https://bungie.net"
_MANIFEST_URL = _BASE_URL + "/Platform/Destiny2/Manifest"

_HASH_THRESHOLD = 2**31 - 1
_HASH_MODIFIER = 2**32

Utils.FileChecker.directory(_MANIFEST_FOLDER)

# Update Checking

def _get_current_manifest() -> dict:
    try:
        return Utils.JSON.load(_MANIFEST_FILE)
    except FileNotFoundError:
        raise Errors.Manifest.ManifestNotFoundError

def _fetch_manifest_blocking() -> dict:
    response = requests.get(_MANIFEST_URL)
    if response.ok:
        return response.json()
    else:
        raise Errors.Manifest.FetchFailedError("Manifest", response.status_code)

async def _fetch_manifest_async() -> dict:
    async with aiohttp.ClientSession() as session:
        async with session.get(_MANIFEST_URL) as response:
            if response.ok:
                return await response.json()
            else:
                raise Errors.Manifest.FetchFailedError("Manifest", response.status)

def _is_outdated_blocking() -> bool:
    try:
        current_manifest = _get_current_manifest()
    except Errors.Manifest.ManifestNotFoundError:
        return True
    new_manifest = _fetch_manifest_blocking()
    return current_manifest["Response"]["version"] != new_manifest["Response"]["version"]

async def is_outdated() -> bool:
    try:
        current_manifest = _get_current_manifest()
    except Errors.Manifest.ManifestNotFoundError:
        return True
    new_manifest = await _fetch_manifest_async()
    return current_manifest["Response"]["version"] != new_manifest["Response"]["version"]

def _unpack_manifest(content: bytes):
    with open(_ZIP_TARGET, "wb") as _outfile:
        _outfile.write(content)
    if os.path.isfile(_CONTENT_FILE):
        os.remove(_CONTENT_FILE)
    with zipfile.ZipFile(_ZIP_TARGET) as _zipfile:
        filename = _MANIFEST_FOLDER + "/" + _zipfile.namelist()[0]
        _zipfile.extractall(path=_MANIFEST_FOLDER)
    os.rename(filename, _CONTENT_FILE)
    os.remove(_ZIP_TARGET)

def _update_manifest_blocking():
    new_manifest = _fetch_manifest_blocking()
    Utils.JSON.dump(_MANIFEST_FILE, new_manifest)
    content_url = _BASE_URL + new_manifest["Response"]["mobileWorldContentPaths"]["en"]
    response = requests.get(content_url)
    if not response.ok:
        raise Errors.Manifest.FetchFailedError("mobileWorldContentPaths", response.status_code)
    else:
        _unpack_manifest(response.content)

async def update_manifest_async():
    global con
    new_manifest = await _fetch_manifest_async()
    Utils.JSON.dump(_MANIFEST_FILE, new_manifest)
    content_url = _BASE_URL + new_manifest["Response"]["mobileWorldContentPaths"]["en"]
    async with aiohttp.ClientSession() as session:
        async with session.get(content_url) as response:
            if response.ok:
                con.close()
                _unpack_manifest(await response.content.read())
                con = sqlite3.connect(_CONTENT_FILE)
            else:
                raise Errors.Manifest.FetchFailedError("mobileWorldContentPaths", response.status)


# SQLITE3 Setup

con = sqlite3.connect(_CONTENT_FILE)

def _execute(statement: str, fetch_all: bool = True):
    cur = con.cursor()
    if fetch_all:
        res = cur.execute(statement).fetchall()
    else:
        res = cur.execute(statement).fetchone()
    cur.close()
    return res


# Hash<->ID Conversion

def _hash_to_id(hash_in: str | int) -> int:
    """
    Converts a given hash to an id for lookup in the manifest.content table by converting it to a 32-bit unsigned integer.

    :param hash_in: The Hash to convert
    :return: The ID for lookup in manifest.content
    """
    hash_in = int(hash_in)
    if hash_in > _HASH_THRESHOLD:
        return hash_in - _HASH_MODIFIER
    else:
        return hash_in

def _id_to_hash(id_in: int) -> int:
    """
    Converts a given id from manifest.content to a hash table by converting it to a 32-bit signed integer.

    :param id_in: The ID to convert from manifest.content
    :return: The resulting Hash
    """
    if id_in > 0:
        return id_in
    else:
        return id_in + _HASH_MODIFIER


# Definition Fetching

DEFINITION_TYPES = [r[0] for r in _execute("SELECT name FROM sqlite_master WHERE type='table';")]

def get_definition(definition_type: str, definition_hash: str | int) -> dict:
    if definition_type not in DEFINITION_TYPES:
        raise Errors.Manifest.DefinitionTypeDoesNotExistError(definition_type)
    definition_id = _hash_to_id(definition_hash)
    result = _execute(f"SELECT * FROM {definition_type} WHERE id={definition_id}", fetch_all=False)
    if result is None:
        raise Errors.Manifest.HashNotFoundError(definition_type, definition_hash, definition_id)
    else:
        return json.loads(result[1])

def get_all_definitions(definition_type: str) -> dict[str, dict]:
    if definition_type not in DEFINITION_TYPES:
        raise Errors.Manifest.DefinitionTypeDoesNotExistError(definition_type)
    result = _execute(f"SELECT * FROM {definition_type}", fetch_all=True)
    return {str(_id_to_hash(definition_id)): json.loads(definition) for definition_id, definition in result}

def get_definitions(definition_type: str, definition_hashes: list[str | int]) -> dict[str, dict]:
    if definition_type not in DEFINITION_TYPES:
        raise Errors.Manifest.DefinitionTypeDoesNotExistError(definition_type)
    raw_result = _execute(f"SELECT * FROM {definition_type} WHERE id IN ({', '.join(str(_hash_to_id(h)) for h in definition_hashes)})", fetch_all=True)
    result = {str(_id_to_hash(definition_id)): json.loads(definition) for definition_id, definition in raw_result}
    if all([str(h) in result for h in definition_hashes]):
        return result
    else:
        missing_hashes = [h for h in definition_hashes if str(h) not in result]
        missing_ids = [_hash_to_id(h) for h in missing_hashes]
        raise Errors.Manifest.HashesNotFoundError(definition_type, missing_hashes, missing_ids)



