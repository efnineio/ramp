import simplejson as json
import six
import os

from datetime import datetime, date



# class ToJsonMixin(object):
#     def to_json(self):
#         return json.dumps(self, default=self.json_filter, sort_keys=True, indent=4)
#
#     def json_filter(self, obj):
#         """
#         filter out properties that have names starting with _
#         or properties that have a value of None
#         """
#
#         if isinstance(obj, (date, datetime)):
#             return obj.isoformat()
#         if hasattr(obj, "__dict__"):
#             return {
#                 k: v
#                 for k, v in obj.__dict__.items()
#                 if not k.startswith("_") and (getattr(obj, k) is not None or k in obj._required_fields)
#             }
#
#         return obj

class ToJsonMixin(object):
    def to_json(self, read_only_fields=True):
        if read_only_fields:
            return json.dumps(self, default=self.json_filter, sort_keys=True, indent=4)
        else:
            return json.dumps(self, default=self.json_filter_no_ro, sort_keys=True, indent=4)

    def json_filter(self, obj):
        """
        filter out properties that have names starting with _
        or properties that have a value of None
        """

        if isinstance(obj, (date, datetime)):
            return obj.isoformat()
        if hasattr(obj, "__dict__"):
            # return {
            #     k: v
            #     for k, v in obj.__dict__.items()
            #     if not k.startswith("_") and (getattr(obj, k) is not None or k in obj._required_fields)
            # }
            answer = {}
            for k, v in obj.__dict__.items():
                if getattr(obj,'_field_dict', {}).get(k,{}).get('type') == 'jsonfield':
                    answer[k] = json.dumps(v)
                    continue

                if not k.startswith("_") and (getattr(obj, k) is not None or k in obj._required_fields):
                    answer[k] = v

            return answer

        return obj

    def json_filter_no_ro(self, obj):
        """
        filter out properties that have names starting with _
        or properties that have a value of None
        """

        if isinstance(obj, (date, datetime)):
            return obj.isoformat()
        if hasattr(obj, "__dict__"):

            answer = {}
            for k, v in obj.__dict__.items():
                if k in obj._read_only_fields:
                    continue

                if getattr(obj,'_field_dict', {}).get(k,{}).get('type') == 'jsonfield':
                    answer[k] = json.dumps(v)
                    continue

                if not k.startswith("_") and (getattr(obj, k) is not None or k in obj._required_fields):
                    answer[k] = v

            return answer

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


import uuid
import time
import json


class IdempotencyMixin(object):
    def get_key(self):
        return str(uuid.uuid4())


# task_check_status =
# {"data":{"card_id":"1c63c83d-df72-45a8-9154-74945f1e60e0"},
# "id":"4618986a-b944-4f17-a071-c1b875921409",
# "status":"SUCCESS"}\n'



class DeferredTaskMixin(object):
    def check_deferred_task(self, task_id):

        ep = self.get_endpoint(self._client) + '/deferred/status/{}'.format(task_id)

        r = self._client.hit_api(verb='GET', endpoint=ep)
        return r

    def run_deferred_task(self, task_id, client=None):
        if client: self._client = client
        i = 0
        multiplier = 1.1
        total_count = 10
        delay = 1
        task_status = None

        while i < 10 and task_status != 'FAILED':
            i += 1
            r = self.check_deferred_task(task_id)
            # print(r.json())

            # 'STARTED'
            if r.status_code == 200:
                # print(r.json())
                task_status = r.json().get('status')
                if task_status == 'SUCCESS':
                    return r.json()
            else:
                task_status = 'FAILED'
                return {'id': task_id, 'status': 'FAILED', 'data': {}}

            time.sleep(delay)
            delay = delay * multiplier


class SaveMixin(object):
    def save(self, client=None):
        if client: self._client = client
        ep = self.get_object_api_endpoint()

        res = self._client.hit_api('PATCH', endpoint=ep, json=json.loads(self.to_json(read_only_fields=False)))
        res.raise_for_status()

        self.refresh()