# -*- coding: utf-8 -*-
"""
Connection module

"""
from pyxmn.utils import support
# from psycopg2.pool import SimpleConnectionPool
import psycopg2.extras  # load the psycopg extras module


class Pool():
    """
    Connection Pool

    """
    settings = None
    connection = None
    pool = None

    @staticmethod
    def commit():
        (Pool.connection).commit()

    @staticmethod
    def connect(settings):
        """
        Connects to a base

        conn: host=localhost dbname=db_name user=postgres

        """
        Pool.settings = settings
        _conn_string = (
            ('host=%(HOST)s dbname=%(NAME)s user=%(USER)s ' +
             'password=%(PASSWORD)s') %
            settings.DATABASE[settings.HOSTNAME]
        )

        # Pool.conn_string = _conn_string
        Pool.connection = psycopg2.connect(
            dsn=_conn_string,
            connection_factory=psycopg2.extras.NamedTupleConnection)

    @staticmethod
    def cursor():
        cur = Pool.connection.cursor()
        dbconf = Pool.settings.DATABASE[Pool.settings.HOSTNAME]

        if 'SCHEMA' in dbconf:
            Pool.execute(cur, 'SET search_path TO ' + dbconf['SCHEMA'])
        return cur

    @staticmethod
    def execute(cursor, statement, arg=()):
        """

        """
        if Pool.settings.DEBUG:
            try:
                support.log(statement % arg)
            except:
                pass

        cursor.execute(statement, arg)
