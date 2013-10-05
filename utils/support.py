# -*- coding: utf-8 -*-
from collections import defaultdict
from matplotlib.ticker import EngFormatter

import matplotlib.pyplot as plt
import json
import string
import datetime
import unicodedata


def log(text):
    """
    Write into logfile

    """
    try:
        open('./log/log.txt', 'a').write(text + '\n')
    except:
        pass


def remove_accents(data):
    return ''.join(
        x for x in unicodedata.normalize('NFKD', data)
        if x in string.ascii_letters or x == '_'
    ).lower()


def image_string(data, field):
    """

    @param data:
    @param field:
    @return: string JSON

    """
    try:
        if isinstance(data[0], tuple):
            return str(data[0]._asdict()[field])
        else:
            return str(data[0][field])
    except:
        return None


def googlechart_json(wimdata, sensors=None, quality=100):
    """

    @param wimdata:
    @param sensors:
    @param quality:
    @return: string JSON

    """
    # Chart Header
    graphic = {'cols': [], 'rows': []}
    graphic['cols'].append({"id": "", "label": "Time", "type": "number"})

    for x in range(1, 32):
        graphic['cols'].append(
            {"id": "", "label": "Sensor %s: " % x, "type": "number"}
        )

    xs = []
    linea = []
    tempo_captado = False

    for sensor in wimdata.data.dict():
        ys = []
        step = int(100 / quality)
        # Analyze sensor acquisition by time
        for acq_time in sorted(wimdata.data.dict()[sensor].keys()[::step]):
            if not tempo_captado:
                xs.append(len(xs) * step)
            ys.append(wimdata.data.dict()[sensor][acq_time])

        if not tempo_captado:
            linea.append(xs)

        linea.append(ys)
        tempo_captado = True

    graphic['rows'] = map(lambda l: {'c': [{'v': v} for v in l]}, zip(*linea))
    return graphic


def chart_dict(wimdata):
    """

    @param wimdata: data dictionary
    @return: string JSON

    """
    # Chart Header
    graphic = defaultdict(list)

    for sensor in wimdata:
        # Analyze sensor acquisition by time
        for acq_time in sorted(wimdata[sensor].keys()):
                graphic[sensor].append(wimdata[sensor][acq_time])

    return graphic


def plot(wimdata, sensors=None):
    """

    @param wimdata:
    @param sensors:
    """
    # Chart configuration
    formatter = EngFormatter(unit='s', places=1)
    plt.grid(True)

    # Charge data plot
    wimdata.data.array()
    ax = plt.subplot(111)
    ax.xaxis.set_major_formatter(formatter)
    ax.plot(wimdata.data.array())
    plt.show()


def db_to_json(db_list):
    """

    @param db_list: list with db data
    @type db_list: list
    @return: list in JSON format
    @rtype: list
    """
    json_list = []
    for l in db_list:
        record = (l if not isinstance(l, tuple) else l._asdict())
        for key, value in record.items():
            if isinstance(value, datetime.datetime):
                record[key] = str(value)
        json_list.append(record)

    return json.dumps(json_list)
