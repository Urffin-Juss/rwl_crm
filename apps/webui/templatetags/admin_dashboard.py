from django import template

from apps.core.models import Order, Task
from apps.imports.models import ImportBatch

register = template.Library()


@register.simple_tag
def latest_tasks(limit=8):
    return Task.objects.select_related("assignee", "event", "order").order_by("-created_at")[:limit]


@register.simple_tag
def latest_orders(limit=8):
    return Order.objects.select_related("client", "event", "assigned_packer").order_by("-created_at")[:limit]


@register.simple_tag
def latest_imports(limit=8):
    return ImportBatch.objects.select_related("uploaded_by").order_by("-created_at")[:limit]
