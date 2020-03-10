from flask import escape
from flask_restx import fields

__all__ = [
    'HtmlEscapeField',
    'NewlineConvertField'
]

class HtmlEscapeField(fields.Raw):
    def format(self, value):
        return escape(value)

class NewlineConvertField(fields.Raw):
    def format(self, value):
        value = value.replace('\n\n', '<br>')
        return value.replace('\n', '<br>') # Make up for any missed newlines 