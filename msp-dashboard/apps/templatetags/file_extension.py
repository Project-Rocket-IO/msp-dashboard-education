from django import template
import os
from urllib.parse import quote

register = template.Library()

@register.filter
def file_extension(value):
    _, extension = os.path.splitext(value)
    return extension.lower()


@register.filter
def encoded_file_path(path):
    return path.replace('/', '%slash%')

@register.filter
def encoded_path(path):
    return path.replace('\\', '/')


@register.inclusion_tag('apps/filemanager/directory_item.html', takes_context=True)
def render_directory(context, **kwargs):
    return kwargs


@register.filter
def zip_lists(a, b):
    return zip(a, b)
