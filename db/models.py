# -*- coding: utf-8 -*-
"""
Models module

"""
from datetime import datetime
from copy import deepcopy as copy

import re
import psycopg2
import traceback

# internal
from pyxmn.db.conn import Pool
from pyxmn.utils import support
from unidecode import unidecode


def convert_to_db(db_type, value):
    """

    """
    def _str(_value):
        return _value.strip() if _value != '' else None

    def _float(_value):
        if _value == 'NaN':
            _value = ''
        return float(_value.replace(',', '.')) if _value != '' else None

    def _int(_value):
        if _value == 'NaN':
            _value = ''
        return int(_value) if _value != '' else None

    def _datetime(_value):
        _value = _value.replace('-', '/')
        return (datetime.strptime(_value, '%Y/%m/%d %H:%M:%S')
                if _value != '' else None)

    _convert = {
        'double precision': _float,
        'integer': _int,
        'character varying': _str,
        'text': _str,
        'bytea': Binary,
        'timestamp without time zone': _datetime
    }

    return _convert[db_type](value)


class Model(object):
    """
    Generic Model

    """
    def __init__(self, **args):
        # reflection mode
        if (
            self.__class__.Meta.reflection
        ):
            cur = Pool.cursor()

            Pool.execute(
                cur,
                " SELECT tc.table_schema, tc.table_name, kc.column_name" +
                " FROM" +
                "     information_schema.table_constraints tc," +
                "     information_schema.key_column_usage kc" +
                " WHERE" +
                "     tc.constraint_type = 'PRIMARY KEY'" +
                "     AND kc.table_name = tc.table_name" +
                "     AND kc.table_schema = tc.table_schema" +
                "     AND kc.constraint_name = tc.constraint_name" +
                "     AND kc.table_name =%s;",
                (str(self.__class__.Meta.db_table),)
            )

            _pkey = []
            for _pk in cur.fetchall():
                _pkey.append(_pk.column_name)

            Pool.execute(
                cur,
                " SELECT column_name, data_type" +
                " FROM information_schema.columns" +
                " WHERE table_name = %s",
                (self.__class__.Meta.db_table,)
            )

            for f_name, f_type in cur:
                _pk = True if f_name in _pkey else False

                setattr(
                    self.__class__, f_name,
                    Field(name=f_name, type_field=f_type, pkey=_pk)
                )

            cur.close()

        # create the object structure
        for attr in self.__class__.__dict__:
            # skip if attr is not a Field
            if not isinstance(self.__class__.__dict__[attr], Field):
                continue

            # copy the static structure field to the new instance
            self.__dict__[attr] = copy(self.__class__.__dict__[attr])
            # apply the default value
            self.__dict__[attr].value = self.__dict__[attr].default_value

        # set the parameters value
        for attr in args:
            if (
                attr not in self.__class__.__dict__ and
                attr not in self.__dict__
            ):
                raise AttributeError("A instance has no attribute '%s'" % attr)
            # set the value to the field
            self.__dict__[attr].value = args[attr]

    @classmethod
    def load(cls, _id):
        """
        This static method selects all fields from data table and return a new
        Model object populated

        @return: Model object
        @rtype: Model
        """
        cur = Pool.cursor()
        cur.execute(
            ' SELECT * FROM ' + cls.Meta.db_table + ' WHERE id=%s',
            (_id,)
        )
        one = cur.fetchone()
        data = one._asdict() if one else {}

        cur.close()

        return cls(**(data))

    @classmethod
    def search(cls, **filters):
        """
        Generic Search using filters parameters.

        @param filters: filter dictionary
        @type filters: dictionary
        @return: a list containing a vehicle data founded
        @rtype: list

        """
        cur = Pool.cursor()

        # standards fields to return
        default_fields = '*' if 'default-fields' not in filters else \
                         filters['default-fields']

        fields = (default_fields if 'fields' not in filters else
                  filters['fields'])

        # clear whitespace
        fields = re.sub('\s+', '', fields)

        distinct = (' DISTINCT ' if 'distinct' in filters and
                    filters['distinct'] is True else '')

        # where clause
        # where='' if 'where' not in filters else ' WHERE ' + filters['where']
        where = (
            '' if 'where' not in filters or not filters['where'] else
            ' WHERE ' + ' AND '.join(
                map(lambda v: '%s=%s' % (v, filters['where'][v]),
                    filters['where']))
        )

        inner = ('' if not cls.Meta.inner_join else
                 ' INNER JOIN ' + ' INNER JOIN '.join(cls.Meta.inner_join))

        left = ('' if not cls.Meta.left_join else
                ' LEFT JOIN ' + ' LEFT JOIN '.join(cls.Meta.left_join))

        # find the times interval of all sensors in the acquisition
        Pool.execute(
            cur,
            ' SELECT ' + distinct + fields +
            ' FROM ' + str(cls.Meta.db_table) + ' ' +
            inner + left + where, ())

        registers = cur.fetchall()

        cur.close()

        return registers

    def save(self):
        """
        Saves class data

        @return: id of the data stored
        @rtype: integer

        """
        if self.id.value:
            return self.update()
        else:
            return self.insert()

    def insert(self):
        """
        Saves class data

        @return: id of the data stored
        @rtype: integer

        """
        cur = Pool.cursor()

        fields = ''
        separator = ''
        values_s = ''
        values_v = []
        # for item in self.__class__.__dict__.keys():
        # for item in self.__dict__.keys():
        for item in self.__class__.__dict__.keys():
            # skip internal attributes and Meta class
            if (
                item not in self.__dict__ or
                not isinstance(self.__dict__[item], Field)
            ):
                continue

            fields += separator + item
            if (item != 'id' or
                    (item == 'id' and
                     self.__dict__[item].value is not None)):
                values_s += separator + '%s'
                values_v.append(self.__dict__[item].val())
            else:
                values_s += separator + 'DEFAULT'

            separator = ','

        Pool.execute(
            cur,
            ' INSERT INTO ' + self.Meta.db_table + ' (' +
            '   ' + fields + ')' +
            ' VALUES(' + values_s + ')'
            ' RETURNING id',
            tuple(values_v))

        # get the vehicle ID of the new vehicle inserted
        _id = cur.fetchone()[0]

        Pool.commit()
        cur.close()

        return _id

    def update(self):
        """
        Update model data

        @return: id of the data stored
        @rtype: integer

        """
        cur = Pool.cursor()

        separator = ''
        field_set = ''
        field_value_set = []
        pkey_name_set = []
        pkey_value_set = []

        for item in self.__class__.__dict__.keys():
            # skip internal attributes and Meta class
            if (
                item not in self.__dict__ or
                not isinstance(self.__dict__[item], Field)
            ):
                continue
            # catch the pkey field
            if self.__dict__[item].pkey:
                pkey_name_set.append(self.__dict__[item].db_name + '=%s')
                pkey_value_set.append(self.__dict__[item].val())
                continue

            field_set += separator + item + '=%s'
            field_value_set.append(self.__dict__[item].val())

            separator = ','

        Pool.execute(
            cur,
            ' UPDATE ' + self.Meta.db_table +
            ' SET ' + field_set +
            ' WHERE ' + ' AND '.join(pkey_name_set),
            tuple(field_value_set + pkey_value_set))

        Pool.commit()
        cur.close()

        return self.id

    class Meta:
        """

        """
        db_table = ''
        reflection = False
        inner_join = []
        left_join = []


class Field():
    """
    Field class to create stereotype fields

    """
    type = None
    name = None
    db_name = None
    label = None
    maxlen = 0
    default_value = None
    value = None
    pkey = False
    db_format = None

    def __init__(
        self, type_field=None, name=None, db_name=None, label=None,
        maxlen=0, default_value=None, db_format=None, pkey=False
    ):
        """

        """
        self.type = type_field
        self.name = name
        self.db_name = db_name
        self.label = label
        self.maxlen = maxlen
        self.default_value = default_value
        self.db_format = db_format if db_format else '%s'
        self.pkey = pkey

        # required
        if self.name is None:
            raise Exception('The name attribute is required')
        # default
        if self.db_name is None:
            self.db_name = self.name
        if self.label is None:
            self.label = self.name

    def __str__(self):
        """
        """
        return self.value

    def __eq__(self, other):
        return self.value == other

    def val(self):
        """
        Database value formatted

        """
        if not self.value:
            return self.value

        tp = self.type
        return (
            float(str(self.value).replace(',', '.')) if tp == 'float' else
            int(self.value) if tp == 'integer' else
            psycopg2.Binary(self.value) if tp == 'bytea' else
            str(self.value)
        )

    def set(self, value):
        """
        Database value formatted

        """
        self.value = value


class RawModel(Model):
    """

    """
    @classmethod
    def load(cls, data):
        """

        """
        cur = Pool.cursor()
        cur.execute(
            " SELECT column_name, data_type" +
            " FROM information_schema.columns" +
            " WHERE table_name = '%s'" % str(cls.Meta.db_table)
        )

        struct = {}
        for i in cur:
            struct.update({i.column_name: i.data_type})

        header = []
        for h in data[0]:
            hfield = h.lower().replace(' ', '_').replace('-', '_')
            header.append(unidecode(hfield.decode('utf-8')))

        for fields in data[1:]:
            insert_fields = []
            insert_values = []

            for k, v in enumerate(fields):
                # prepares data considering the data type
                insert_fields.append(header[k])
                insert_values.append(
                    convert_to_db(
                        struct[header[k]], v))

            # insert new record
            sql = (
                'INSERT INTO %s(%s) VALUES (%s)' %
                (str(cls.Meta.db_table),
                 ','.join(insert_fields),
                 ','.join(['%s'] * len(insert_fields))))
            try:
                cur.execute(sql, insert_values)
                Pool.commit()
            except:
                support.log(traceback.format_exc())

        cur.close()

        return True

    @classmethod
    def delete(cls, **filters):
        """

        """
        cur = Pool.cursor()
        cur.execute(
            " DELETE FROM %s" % str(cls.Meta.db_table)
        )

        cur.close()
        return True

Binary = psycopg2.Binary
