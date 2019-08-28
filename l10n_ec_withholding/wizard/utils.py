# -*- coding: utf-8 -*-

import time
import datetime

STD_FORMAT = '%Y-%m-%d'


def convertir_fecha(fecha):
    """
    fecha: '2012-12-15'
    return: '15/12/2012'
    """
    return '{0:%d/%m/%Y}'.format(fecha)


def get_date_value(date, t='%Y'):
    return ('{0:%s}' % t).format(date)
