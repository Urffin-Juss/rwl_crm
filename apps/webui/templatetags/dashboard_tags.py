from django import template

from apps.events.models import Event
from apps.orders.models import Order
from apps.tasks.models import Task
from apps.imports.models import ImportBatch

register = template.Library()


@register.simple_tag
def latest_tasks(limit=8):
    return (
        Task.objects
        .select_related("assigned")
        .order_by("-created_at")[:limit]
    )


@register.simple_tag
def latest_orders(limit=8):
    return (
        Order.objects
        .select_related("client", "event", "assigned_packer", "stock_location")
        .order_by("-created_at")[:limit]
    )


@register.simple_tag
def latest_imports(limit=8):
    return (
        ImportBatch.objects
        .select_related("uploaded_by", "event")
        .order_by("-created_at")[:limit]
    )


@register.simple_tag
def dashboard_breakdown():
    active_orders = Order.objects.exclude(status__in=["completed", "cancelled"]).count()
    open_tasks = Task.objects.exclude(status="DONE").count()
    open_events = Event.objects.filter(status="OPEN").count()

    total = active_orders + open_tasks + open_events
    if total == 0:
        return {
            "active_orders": 0,
            "open_tasks": 0,
            "open_events": 0,
            "order_deg": 120,
            "task_deg": 120,
            "event_deg": 120,
        }

    order_deg = round((active_orders / total) * 360, 2)
    task_deg = round((open_tasks / total) * 360, 2)
    event_deg = round(360 - order_deg - task_deg, 2)

    return {
        "active_orders": active_orders,
        "open_tasks": open_tasks,
        "open_events": open_events,
        "order_deg": order_deg,
        "task_deg": task_deg,
        "event_deg": event_deg,
    }
