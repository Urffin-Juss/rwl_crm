from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect, render
from django.urls import reverse

from apps.orders.models import Order
from apps.tasks.models import Task


def _has_full_access(user):
    return any([
        user.is_superuser,
        user.groups.filter(name='Owner').exists(),
        user.groups.filter(name='Admin').exists(),
    ])


def _mobile_orders_queryset(user):
    qs = Order.objects.select_related("client").exclude(status="completed")
    if _has_full_access(user):
        return qs
    return qs.filter(assigned_packer=user)


def _mobile_tasks_queryset(user):
    qs = Task.objects.select_related("assigned", "order")
    if _has_full_access(user):
        return qs
    return qs.filter(assigned=user)


def landing(request):
    return render(request, "webui/landing.html")


@login_required
def workspace(request):
    return render(request, "webui/workspace.html")


@login_required
def mobile_workspace(request):
    active_tab = request.GET.get("tab", "orders")
    if active_tab not in {"orders", "tasks"}:
        active_tab = "orders"

    if request.method == "POST":
        entity = request.POST.get("entity")
        object_id = request.POST.get("object_id")
        new_status = request.POST.get("status")
        active_tab = request.POST.get("tab", active_tab)
        if active_tab not in {"orders", "tasks"}:
            active_tab = "orders"

        if entity == "order":
            order = get_object_or_404(_mobile_orders_queryset(request.user), pk=object_id)
            allowed_statuses = {choice[0] for choice in Order.STATUS_CHOICES}
            if new_status in allowed_statuses:
                order.status = new_status
                order.save(update_fields=["status", "updated_at"])
                messages.success(request, f"Order #{order.pk}: статус обновлен.")
            else:
                messages.error(request, "Недопустимый статус заказа.")

        elif entity == "task":
            task = get_object_or_404(_mobile_tasks_queryset(request.user), pk=object_id)
            allowed_statuses = {choice[0] for choice in Task.STATUS_CHOICES}
            if new_status in allowed_statuses:
                task.status = new_status
                task.save(update_fields=["status", "updated_at"])
                messages.success(request, f"Task #{task.pk}: статус обновлен.")
            else:
                messages.error(request, "Недопустимый статус задачи.")

        else:
            messages.error(request, "Неизвестный тип объекта.")

        return redirect(f"{reverse('mobile_workspace')}?tab={active_tab}")

    orders = _mobile_orders_queryset(request.user).order_by("-created_at", "-id")[:20]
    tasks = _mobile_tasks_queryset(request.user).order_by("-updated_at", "-id")[:20]

    context = {
        "orders": orders,
        "tasks": tasks,
        "active_tab": active_tab,
        "order_status_choices": Order.STATUS_CHOICES,
        "task_status_choices": Task.STATUS_CHOICES,
    }
    return render(request, "webui/mobile_workspace.html", context)
