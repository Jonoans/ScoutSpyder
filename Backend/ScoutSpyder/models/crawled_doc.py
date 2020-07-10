from mongoengine import Document, DateTimeField, IntField, ListField, StringField
from datetime import datetime
import pytz

class CrawledDocument(Document):
    meta = {
        'db_alias': 'global',
        'collection': 'crawledDocument',
        'index_background': True,
        'indexes': [
            {'fields': ['fqdn', 'html'], 'unique': True},
            {'fields': ['url'], 'unique': True},
            {'fields': ['timestamp']},
            {'fields': ['-timestamp']}
        ]
    }

    crawl_id = StringField(required=True)
    timestamp = DateTimeField(required=True)
    fqdn = StringField(required=True)
    html = StringField(required=True)
    url = StringField(required=True)
    processed = StringField(required=True)
    authors = ListField(StringField())
    title = StringField()
    text = StringField()
    publish_date = DateTimeField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.pk:
            self.timestamp = pytz.utc.localize(datetime.utcnow())