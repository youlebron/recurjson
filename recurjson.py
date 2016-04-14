# -*- coding: utf-8 -*-
import json
import warnings
import quopri
import typeutil
from typeutil import PY2


def encode(value):
    context = Pickler()
    return json.dumps(context.flatten(value))


class Pickler(object):
    def __init__(self):
        self._objs = {}
        self._seen = []

    def reset(self):
        self._objs = {}
        self._seen = []

    def flatten(self, obj):
        self.reset()
        return self._flatten_obj(obj)

    def _flatten_obj(self, obj):
        self._seen.append(obj)
        flatten_func = self._get_flattener(obj)
        if flatten_func is None:
            return None
        return flatten_func(obj)

    def _get_flattener(self, obj):
        if PY2 and isinstance(obj, file):
            return self._flatten_file

        if typeutil.is_primitive(obj):
            return lambda obj: obj

        if typeutil.is_bytes(obj):
            return self._flatten_bytestring

        if typeutil.is_sequence(obj):
            return self._flatten_list

        if typeutil.is_dictionary(obj):
            return self._flatten_dict_obj

        if typeutil.is_time(obj):
            return self._flatten_time

        if typeutil.is_object(obj):
            return self._flatten_obj_instance

        if typeutil.is_module_function(obj):
            return self._flatten_function

        self._pickle_warning(obj)
        return None

    def _flatten_file(self, obj):
        return None

    def _flatten_time(self, obj):
        return obj.__str__()

    def _flatten_function(self, obj):
        return None

    def _flatten_bytestring(self, obj):
        if PY2:
            try:
                return obj.decode('utf-8')
            except:
                pass
        return quopri.encodestring(obj).decode('utf-8')

    def _flatten_list(self, obj):
        return [self._flatten_obj(v) for v in obj]

    def _flatten_dict_obj(self, obj, data=None):
        if data is None:
            data = obj.__class__()

        for k, v in sorted(obj.items(), key=typeutil.itemgetter):
            self._flatten_key_value_pair(k, v, data)

        return data

    def _flatten_key_value_pair(self, k, v, data):
        if not typeutil.is_picklable(k, v):
            return data
        if k is None:
            k = 'null'
        if not isinstance(k, (str, unicode)):
            try:
                k = repr(k)
            except:
                k = unicode(k)
        data[k] = self._flatten_obj(v)
        return data

    def _flatten_obj_instance(self, obj):
        '''
            去除sqlalchemy.Model类`
        '''
        if hasattr(obj, "_sa_instance_state"):
            delattr(obj, "_sa_instance_state")

        data = {}
        has_dict = hasattr(obj, '__dict__')
        if typeutil.is_module(obj):
            return unicode(obj)
        if has_dict:
            return self._flatten_dict_obj(obj.__dict__, data)
        if data:
            return data

        self._pickle_warning(obj)
        return None

    def _pickle_warning(self, obj):
        msg = 'recurjson cannot pickle %r: replaced with None' % obj
        warnings.warn(msg)
