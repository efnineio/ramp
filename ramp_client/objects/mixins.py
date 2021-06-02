import simplejson as json
import six
import os

from datetime import datetime, date



class ToJsonMixin(object):
    def to_json(self):
        return json.dumps(self, default=self.json_filter, sort_keys=True, indent=4)

    def json_filter(self, obj):
        """
        filter out properties that have names starting with _
        or properties that have a value of None
        """

        if isinstance(obj, (date, datetime)):
            return obj.isoformat()
        if hasattr(obj, "__dict__"):
            return {
                k: v
                for k, v in obj.__dict__.items()
                if not k.startswith("_") and (getattr(obj, k) is not None or k in obj._required_fields)
            }

        return obj


def to_dict(obj, classkey=None):
    """
    Recursively converts Python object into a dictionary
    """
    if isinstance(obj, dict):
        data = {}
        for (k, v) in obj.items():
            data[k] = to_dict(v, classkey)
        return data
    elif hasattr(obj, "_ast"):
        return to_dict(obj._ast())
    elif hasattr(obj, "__iter__") and not isinstance(obj, str):
        return [to_dict(v, classkey) for v in obj]
    elif hasattr(obj, "__dict__"):
        if six.PY2:
            data = dict([(key, to_dict(value, classkey))
                        for key, value in obj.__dict__.iteritems()
                        if not callable(value) and not key.startswith('_')])
        else:
            data = dict([(key, to_dict(value, classkey))
                        for key, value in obj.__dict__.items()
                        if not callable(value) and not key.startswith('_')])

        if classkey is not None and hasattr(obj, "__class__"):
            data[classkey] = obj.__class__.__name__
        return data
    else:
        return obj


class ToDictMixin(object):
    def to_dict(self):
        return to_dict(self)

class FromJsonMixin(object):
    class_dict = {}
    list_dict = {}

    @classmethod
    def from_json(cls, json_data):
        obj = cls()
#        print(json_data)
        for key in json_data:
            if key in obj.class_dict:
                sub_obj = obj.class_dict[key]()
                sub_obj = sub_obj.from_json(json_data[key])
                setattr(obj, key, sub_obj)

            elif key in obj.list_dict:
                sub_list = []

                for data in json_data[key]:
                    #print(obj.list_dict[key])
                    sub_obj = obj.list_dict[key]()
                    sub_obj = sub_obj.from_json(data)
                    sub_list.append(sub_obj)

                setattr(obj, key, sub_list)
            else:
                setattr(obj, key, json_data[key])

        return obj


class FromFileMixin(FromJsonMixin):
    def from_file(self, filename=None, id=None, context ={}):
        if not any([filename, id]):
            raise ValueError("MUST SUPPLY FILENAME OR ID")

        if not filename and id:
            filename = os.path.join(os.environ['SLACKOBJECTTEMPLATES'], "{}s".format(self.__class__.__name__.lower()),
                                    "{}.json".format(id))

        with open(filename, 'r') as f:
            str_read = f.read()
            for key, value in context.items():
                if value is not None:
                    str_read = str_read.replace("!!{}!!".format(key), json.dumps(value)[1:-1])
                else:
                    str_read = str_read.replace(key, "")

        return self.from_json(json.loads(str_read))


