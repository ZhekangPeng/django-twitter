from django_hbase.models import HbaseField, TimestampField, IntegerField
from django_hbase.client import HbaseClient
from django.conf import settings


class BadRowKeyError(Exception):
    pass


class EmptyColumnError(Exception):
    pass


class HBaseModel:

    class Meta:
        table_name = None
        row_key = None

    def __init__(self, **kwargs):
        for key, field in self.get_field_hash().items():
            value = kwargs.get(key)
            setattr(self, key, value)

    @classmethod
    def get_field_hash(cls):
        field_hash = {}
        for field_key in cls.__dict__:
            field_obj = getattr(cls, field_key)
            if isinstance(field_obj, HbaseField):
                field_hash[field_key] = field_obj
        return field_hash

    @classmethod
    def get_table_name(cls):
        if not cls.Meta.table_name:
            raise NotImplementedError('Missing table_name in HBaseModel Meta class')
        if settings.TESTING:
            return 'test_{}'.format(cls.Meta.table_name)
        return cls.Meta.table_name

    @classmethod
    def get_table(cls):
        conn = HbaseClient.get_connection()
        return conn.table(cls.get_table_name())

    @classmethod
    def drop_table(cls):
        if not settings.TESTING:
            raise Exception("You are not allowed to drop tables in Prod")
        conn = HbaseClient.get_connection()
        conn.delete_table(cls.get_table_name(), True)

    @classmethod
    def create_table(cls):
        if not settings.TESTING:
            raise Exception("You are not allowed to create tables in Prod")
        conn = HbaseClient.get_connection()
        # Get all existing tables
        tables = [table.decode('utf-8') for table in conn.tables()]
        if cls.get_table_name() in tables:
            return
        # Create table when table not exist
        column_families = {
            field.column_family: dict()
            for key, field in cls.get_field_hash().items()
            if field.column_family is not None
        }
        conn.create_table(cls.get_table_name(), column_families)

    @property
    def row_key(self):
        return self.serialize_row_key(self.__dict__)

    @classmethod
    def init_from_row(cls, row_key, row_data):
        if not row_data:
            return None
        data = cls.deserialize_row_key(row_key)
        for column_key, column_value in row_data.items():
            # Change bytes to string
            column_key = column_key.decode('utf-8')
            # Remove column family
            key = column_key[column_key.find(':') + 1:]
            field = cls.get_field_hash().get(key)
            data[key] = cls.deserialize_field(field, column_value)
        return cls(**data)

    @classmethod
    def serialize_field(cls, field, value):
        value = str(value)
        if isinstance(field, IntegerField):
            # Make integer contain 16 digit by filling empty digit with 0s
            value = str(value)
            while len(value) < 16:
                value = '0' + value
        if field.reverse:
            value = value[::-1]
        return value

    @classmethod
    def deserialize_field(cls, field, value):
        if field.reverse:
            value = value[::-1]
        if isinstance(field, IntegerField) or isinstance(field, TimestampField):
            return int(value)
        return value

    @classmethod
    def serialize_row_key(cls, data, is_prefix=False):
        """
        serialize dict to bytes (not str)
        {key1: val1} => b"val1"
        {key1: val1, key2: val2} => b"val1:val2"
        {key1: val1, key2: val2, key3: val3} => b"val1:val2:val3"
        """
        field_hash = cls.get_field_hash()
        values = []
        for key, field in field_hash.items():
            if field.column_family:
                continue
            val = data.get(key)
            if val is None:
                if not is_prefix:
                    raise BadRowKeyError(f"{key} is missing in row key")
                break
            val = cls.serialize_field(field, val)
            if ':' in val:
                raise BadRowKeyError(f"{key} should not contain ':' in value: {val}")
            values.append(val)
        return bytes(":".join(values), encoding='utf-8')

    @classmethod
    def serialize_row_key_from_tuple(cls, row_key_tuple):
        if row_key_tuple is None:
            return None
        data = {}
        for key, value in zip(cls.Meta.row_key, row_key_tuple):
            data[key] = value
        return cls.serialize_row_key(data, is_prefix=True)

    @classmethod
    def filter(cls, start=None, stop=None, prefix=None, limit=None, reverse=False):
        # Serialize tuple to str(bytes)
        row_start = cls.serialize_row_key_from_tuple(start)
        row_stop = cls.serialize_row_key_from_tuple(stop)
        row_prefix = cls.serialize_row_key_from_tuple(prefix)

        # Scan table
        table = cls.get_table()
        rows = table.scan(row_start, row_stop, row_prefix, limit=limit, reverse=reverse)

        # Deserialize to instance list
        instances = []
        for row_key, row_data in rows:
            instance = cls.init_from_row(row_key, row_data)
            instances.append(instance)
        return instances

    @classmethod
    def deserialize_row_key(cls, row_key):
        """
         "val1" => {'key1': val1, 'key2': None, 'key3': None}
         "val1:val2" => {'key1': val1, 'key2': val2, 'key3': None}
         "val1:val2:val3" => {'key1': val1, 'key2': val2, 'key3': val3}
         """
        data = {}
        if isinstance(row_key, bytes):
            row_key = row_key.decode('utf-8')
        row_key = row_key.split(":")

        for i, key in enumerate(cls.Meta.row_key):
            if len(row_key) == 0:
                break
            field = cls.get_field_hash().get(key)
            data[key] = cls.deserialize_field(field, row_key[i])
        return data

    @classmethod
    def serialize_row_data(cls, data):
        row_data = {}
        field_hash = cls.get_field_hash()

        for key, field in field_hash.items():
            if not field.column_family:
                continue
            column_key = "{}:{}".format(field.column_family, key)
            column_val = data.get(key)
            if column_val is None:
                continue
            row_data[column_key] = cls.serialize_field(field, column_val)
        return row_data

    def save(self):
        row_data = self.serialize_row_data(self.__dict__)
        if len(row_data) == 0:
            raise EmptyColumnError()
        table = self.get_table()
        table.put(self.row_key, row_data)

    @classmethod
    def get(cls, **kwargs):
        row_key = cls.serialize_row_key(kwargs)
        table = cls.get_table()
        row_data = table.row(row_key)
        return cls.init_from_row(row_key, row_data)

    @classmethod
    def create(cls, **kwargs):
        instance = cls(**kwargs)
        instance.save()
        return instance
