from mongoengine import BooleanField, Document, DateTimeField, IntField, ListField, StringField
from datetime import datetime
from uuid import uuid4
import pytz

class CrawledDocument(Document):
    meta = {
        'db_alias': 'global',
        'collection': 'crawledDocument',
        'index_background': True,
        'indexes': [
            {
                'fields': ['fqdn', 'text'],
                'unique': True,
                'partialFilterExpression': {
                    'text': {'$type': 'string'}
                }
            },
            {'fields': ['url'], 'unique': True},
            {'fields': ['timestamp']},
            {'fields': ['-timestamp']}
        ]
    }

    uuid = StringField(required=True, unique=True)
    crawl_id = StringField(required=True)
    timestamp = DateTimeField()
    fqdn = StringField(required=True)
    html = StringField(required=True)
    url = StringField(required=True)
    processed = BooleanField(required=True)
    authors = ListField(StringField())
    title = StringField()
    text = StringField()
    publish_date = DateTimeField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.pk:
            self.uuid = uuid4().hex
            self.timestamp = pytz.utc.localize(datetime.utcnow())
            self.processed = False