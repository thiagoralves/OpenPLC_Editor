#!/usr/bin/env python
# -*- coding: utf-8 -*-

# See COPYING file for copyrights details.

from __future__ import absolute_import
import os
import time
import json
from zipfile import ZipFile

# PSK Management Data model :
# [[ID,Desc, LastKnownURI, LastConnect]]
COL_ID, COL_URI, COL_DESC, COL_LAST = range(4)
REPLACE, REPLACE_ALL, KEEP, KEEP_ALL, CANCEL = range(5)


def _pskpath(project_path):
    return os.path.join(project_path, 'psk')


def _mgtpath(project_path):
    return os.path.join(_pskpath(project_path), 'management.json')


def _ensurePSKdir(project_path):
    pskpath = _pskpath(project_path)
    if not os.path.exists(pskpath):
        os.mkdir(pskpath)
    return pskpath


def _default(ID):
    return [ID,
            '',  # default description
            None,  # last known URI
            None]  # last connection date


def _dataByID(data):
    return {row[COL_ID]: row for row in data}


def _LoadData(project_path):
    """ load known keys metadata """
    if os.path.isdir(_pskpath(project_path)):
        _path = _mgtpath(project_path)
        if os.path.exists(_path):
            return json.loads(open(_path).read())
    return []


def _filterData(psk_files, data_input):
    input_by_ID = _dataByID(data_input)
    output = []
    # go through all secret files available an build data
    # out of data recoverd from json and list of secret.
    # this implicitly filters IDs out of metadata who's
    # secret is missing
    for filename in psk_files:
        if filename.endswith('.secret'):
            ID = filename[:-7]  # strip filename extension
            output.append(input_by_ID.get(ID, _default(ID)))
    return output


def GetData(project_path):
    loaded_data = _LoadData(project_path)
    if loaded_data:
        psk_files = os.listdir(_pskpath(project_path))
        return _filterData(psk_files, loaded_data)
    return []


def DeleteID(project_path, ID):
    secret_path = os.path.join(_pskpath(project_path), ID+'.secret')
    os.remove(secret_path)


def SaveData(project_path, data):
    _ensurePSKdir(project_path)
    with open(_mgtpath(project_path), 'w') as f:
        f.write(json.dumps(data))


def UpdateID(project_path, ID, secret, URI):
    pskpath = _ensurePSKdir(project_path)
    if not os.path.exists(pskpath):
        os.mkdir(pskpath)

    secpath = os.path.join(pskpath, ID+'.secret')
    with open(secpath, 'w') as f:
        f.write(ID+":"+secret)

    # here we directly use _LoadData, avoiding filtering that could be long
    data = _LoadData(project_path)
    idata = _dataByID(data)
    dataForID = idata.get(ID, None) if data else None

    _is_new_ID = dataForID is None
    if _is_new_ID:
        dataForID = _default(ID)

    dataForID[COL_URI] = URI
    # FIXME : could store time instead os a string and use DVC model's cmp
    # then date display could be smarter, etc - sortable sting hack for now
    dataForID[COL_LAST] = time.strftime('%y/%M/%d-%H:%M:%S')

    if _is_new_ID:
        data.append(dataForID)

    SaveData(project_path, data)


def ExportIDs(project_path, export_zip):
    with ZipFile(export_zip, 'w') as zf:
        path = _pskpath(project_path)
        for nm in os.listdir(path):
            if nm.endswith('.secret') or nm == 'management.json':
                zf.write(os.path.join(path, nm), nm)


def ImportIDs(project_path, import_zip, should_I_replace_callback):
    zf = ZipFile(import_zip, 'r')
    data = GetData(project_path)

    zip_loaded_data = json.loads(zf.open('management.json').read())
    name_list = zf.namelist()
    zip_filtered_data = _filterData(name_list, zip_loaded_data)

    idata = _dataByID(data)

    keys_to_import = []
    result = None

    for imported_row in zip_filtered_data:
        ID = imported_row[COL_ID]
        existing_row = idata.get(ID, None)
        if existing_row is None:
            data.append(imported_row)
        else:
            # callback returns the selected list for merge or none if canceled
            if result not in [REPLACE_ALL, KEEP_ALL]:
                result = should_I_replace_callback(existing_row, imported_row)

            if result == CANCEL:
                return

            if result in [REPLACE_ALL, REPLACE]:
                # replace with imported
                existing_row[:] = imported_row
                # copy the key of selected
                keys_to_import.append(ID)

    for ID in keys_to_import:
        zf.extract(ID+".secret", _pskpath(project_path))

    SaveData(project_path, data)

    return data
