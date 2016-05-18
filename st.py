import json

import webapp2
from google.appengine.ext import ndb


class Profile(ndb.Model):
    like_a = ndb.StringProperty()
    like_b = ndb.StringProperty()
    like_c = ndb.StringProperty()
    like_d = ndb.StringProperty()


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


class ProfilesHandler(BaseHandler):

    def get(self):
        data = dict(self.request.GET)
        keys = data.keys()
        diff = set(keys) - {'like_a', 'like_b', 'like_c', 'like_d'}
        if diff:
            return self.result("%s is not allowed choice" % diff.pop())
        filters = [getattr(Profile, k) == v for k, v in data.iteritems()]

        keys = Profile.query(*filters).fetch(1000, keys_only=True)
        data = {
            'result': [k.id() for k in keys],
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
        if not isinstance(data, list):
            return self.result("a list of keys is required", 400)
        keys = [ndb.Key(Profile, d) for d in data]
        profiles = ndb.get_multi(keys)
        data = {
            'result': [p and self.to_dict(p) for p in profiles],
        }
        self.result(data)


app = webapp2.WSGIApplication([
    ('/profiles', ProfilesHandler),
    webapp2.Route(r'/profiles/bulk_get', handler=ProfilesHandler, handler_method='bulk_get', methods=['POST']),
], debug=False)
