from django import template

register = template.Library()

@register.filter
def currency(amount):
    # TODO Support different currencies.
    return "$%.2f" % amount