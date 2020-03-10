from mongoengine import Document, DateTimeField, IntField, StringField
from datetime import datetime

class QueuedLink(Document):
    meta = {
        'db_alias': 'global',
        'collection': 'queuedLink',
        'index_background': True,
        'indexes': [
            {'fields': ['crawl_id', 'fqdn']},
            {'fields': ['crawl_id', 'url'], 'unique': True},
            {'fields': ['depth', 'timestamp']},
            {'fields': ['fqdn']}
        ],
        'ordering': ['+depth', '+timestamp']
    }

    crawl_id = StringField(required=True)
    timestamp = DateTimeField(default=datetime.utcnow)
    fqdn = StringField(required=True)
    url = StringField(required=True)
    depth = IntField(required=True)
    depth_limit = IntField(required=True)