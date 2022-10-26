from django import template

register = template.Library()

@register.filter
def modulo(num, val):
    return num % val

@register.filter
def separate(value: str):
    return value.split()

@register.filter
def total_votes(upvotes: str, downvotes: str):
    uv = upvotes.split(",") if upvotes != "" else []
    dv = downvotes.split(",") if downvotes != "" else []
    # not count '' as vote
    for i in uv:
        if i == '':
            uv.remove(i)
    for i in dv:
        if i == '':
            dv.remove(i)
    return len(uv) - len(dv)