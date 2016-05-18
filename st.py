import time
import json
import string
import random

import webapp2
from google.appengine.ext import ndb

from google.appengine.ext import deferred


def id_generator(size=12, chars=string.ascii_lowercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


def create_profiles():
    for z in range(10):
        profiles = [Profile(
            id=id_generator(),
            luxury_score=random.randint(1, 10),
            likes_fast_car=bool(random.randint(0, 1)),

        ) for x in range(1000)]
        ndb.put_multi(profiles)
    deferred.defer(create_profiles)


class Profile(ndb.Model):
    likes_fast_car = ndb.BooleanProperty()
    luxury_score = ndb.IntegerProperty()


class BaseHandler(webapp2.RequestHandler):
    def initialize(self, request, response):
        super(BaseHandler, self).initialize(request, response)
        response.headers['Content-Type'] = 'application/json'

    def result(self, data, status=200):
        if isinstance(data, basestring):
            data = {'message': data}
        self.response.out.write(json.dumps(data))
        self.response.set_status(status)

    def to_dict(self, obj):
        data = obj.to_dict()
        data['key'] = obj.key.id()
        return data


class HomeHandler(webapp2.RequestHandler):
    def get(self):
        self.response.write("Hello, go to /profile to list profiles keys")


class ProfilesHandler(BaseHandler):
    OP_MAPPING = {
        'gt': '>',
        'gte': '>=',
        'eq': '=',
        'lt': '<',
        'lte': '<='
    }

    def get(self):
        data = dict(self.request.GET)

        filters = []
        for key, value in data.iteritems():
            try:
                key, op = key.split('__')
            except:
                return self.result("%s not allowed" % key, 400)

            if key not in ('likes_fast_car', 'luxury_score'):
                return self.result("%s key not allowed" % key, 400)
            if not self.OP_MAPPING.get(op):
                return self.result("%s op not allowed" % op, 400)

            try:
                if key == 'luxury_score':
                    value = int(value)
                elif key == 'likes_fast_car':
                    value = bool(int(value))
            except:
                return self.result("%s is not allowed value" % value, 400)

            filter_ = ndb.GenericProperty(key)
            filters.append(filter_._comparison(self.OP_MAPPING[op], value))

        start = time.time()
        keys = Profile.query(*filters).fetch(1000, keys_only=True)
        end = time.time()

        data = {
            'result': [k.id() for k in keys],
            'time': '%s' % (end-start)
        }
        self.result(data)

    def post(self):
        data = json.loads(self.request.body)
        key = data.pop('key', None)
        if not key:
            return self.result("'key' is a required property", 400)
        profile = Profile(id=key, **data)
        profile.put()
        self.result({'status': 'ok'})

    def bulk_get(self):
        data = json.loads(self.request.body)
        keys = data.pop('keys', None)
        if not keys:
            return self.result("'keys' is a required property", 400)

        if not isinstance(keys, list):
            return self.result("a list of keys is required", 400)
        keys = [ndb.Key(Profile, d) for d in keys]
        start = time.time()
        profiles = ndb.get_multi(keys)
        end = time.time()
        data = {
            'result': [p and self.to_dict(p) for p in profiles],
            'time': '%s' % (end-start)
        }
        self.result(data)

    def generate(self):
        pass
        #self.request.POST.get('a')
        #deferred.defer(create_profiles)


app = webapp2.WSGIApplication([
    ('/', HomeHandler),
    ('/profiles', ProfilesHandler),
    webapp2.Route(r'/profiles/bulk_get', handler=ProfilesHandler, handler_method='bulk_get', methods=['POST']),
    webapp2.Route(r'/profiles/generate', handler=ProfilesHandler, handler_method='generate', methods=['POST']),
], debug=False)
