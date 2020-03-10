from mongoengine import Document, DateTimeField, IntField, ListField, StringField
from datetime import datetime

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
    timestamp = DateTimeField(default=datetime.utcnow)
    fqdn = StringField(required=True)
    html = StringField(required=True)
    url = StringField(required=True)
    authors = ListField(StringField())
    title = StringField()
    text = StringField()
    publish_date = DateTimeField()