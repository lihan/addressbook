from google.appengine.ext import ndb


class Address(ndb.Model):
    name = ndb.StringProperty()
    email = ndb.StringProperty()

    @property
    def ndb_key(self):
        return ndb.Key(type(self), self.email)

    @ndb.transactional
    def put_in_transaction(self, overwrite=False):
        key = self.ndb_key.get()
        if key is None or overwrite:
            self.put()
            return True

        return False
