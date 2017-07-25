import csv
import os

import jinja2
import webapp2

from addressbook.models import Address
from addressbook.validators import (
    validate,
    validate_address_email,
)


JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True
)


class BaseHandler(webapp2.RequestHandler):
    def respond(self, template, **params):
        # Flatten line errors
        errors = params.get('errors')
        if isinstance(errors, dict):
            params['errors'] = [
                'Line {}: {}'.format(k, v) for k, v in errors.items()
            ]

        t = JINJA_ENVIRONMENT.get_template(template)
        self.response.write(t.render(params))


class MainHandler(BaseHandler):
    def get(self):
        addresses = Address.query()
        self.respond('index.html', addresses=addresses)


class BaseImportHandler(BaseHandler):
    def save(self, data):
        saved = []
        unsaved = []
        for datum in data:
            address = Address(id=datum['email'],
                              name=datum['name'],
                              email=datum['email'])
            successful = address.put_in_transaction(
                overwrite=datum.get('overwrite', False)
            )
            saved_list = saved if successful else unsaved
            saved_list.append(address)
        return saved, unsaved

    def respond(self, template, **params):
        if 'addresses' not in params:
            params['addresses'] = Address.query()

        super(BaseImportHandler, self).respond(template, **params)


class BulkImportHandler(BaseImportHandler):
    def post(self):
        params = self.request.POST
        names = params.getall('name')
        emails = params.getall('email')
        data = []

        for name, email in zip(names, emails):
            overwrite_field = '{}_overwrite'.format(email)
            overwrite = overwrite_field in params
            data.append({
                'name': name,
                'email': email,
                'overwrite': overwrite
            })

        saved, __ = self.save(data)
        return self.respond('index.html', saved_count=len(saved))


class CSVImportHandler(BaseImportHandler):
    ERROR_ATTACH_FILE = 'Please attach a file'
    ERROR_CSV_FILE = 'Please upload a CSV file'
    ERROR_MISSING_REQUIRED_FIELDS = 'Missing required fields: {}'
    FIELD_FILE = 'file'
    REQUIRED_FIELDS = ('name', 'email')

    def post(self):
        params = self.request.POST

        # File parameter should be given
        if self.FIELD_FILE not in params:
            return self.respond('index.html', errors=[self.ERROR_ATTACH_FILE])

        file_ = params[self.FIELD_FILE]

        # File type should be CSV
        if not file_.filename.endswith('.csv'):
            return self.respond('index.html',
                                errors=[self.ERROR_CSV_FILE])

        header = file_.file.readline().strip('\n')
        fields = header.split(',')

        # Required fields should be given
        if not set(fields) >= set(self.REQUIRED_FIELDS):
            return self.respond(
                'index.html',
                errors=[self.ERROR_MISSING_REQUIRED_FIELDS.format(
                    ', '.join(self.REQUIRED_FIELDS)
                )]
            )

        data = [d for d in csv.DictReader(file_.file, fieldnames=fields) if d]

        # Validate content
        errors = validate(data, validators=[validate_address_email])
        if errors:
            return self.respond('index.html', errors=errors)

        saved, unsaved = self.save(data)
        return self.respond(
            'index.html', saved_count=len(saved), unsaved=unsaved
        )


app = webapp2.WSGIApplication([
    ('/import/bulk', BulkImportHandler),
    ('/import/csv', CSVImportHandler),
    ('/', MainHandler),
], debug=True)
