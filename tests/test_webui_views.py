from datetime import date

from django.contrib.auth.models import Group
from django.contrib.messages import get_messages
from django.test import TestCase
from django.urls import reverse

from apps.clients.models import Client
from apps.events.models import Event
from apps.orders.models import Order
from apps.tasks.models import Task


class MobileWorkspaceViewTests(TestCase):
    def setUp(self):
        self.owner_group = Group.objects.create(name="Owner")
        self.admin_group = Group.objects.create(name="Admin")
        self.packer_group = Group.objects.create(name="Packer")

        self.owner = self._create_user("owner", [self.owner_group])
        self.packer = self._create_user("packer", [self.packer_group])
        self.other_packer = self._create_user("other", [self.packer_group])

        self.event = Event.objects.create(name="Race", city="Moscow", date=date(2026, 1, 1))
        self.client1 = Client.objects.create(name="A", phone="79990000001")
        self.client2 = Client.objects.create(name="B", phone="79990000002")

        self.order_own = Order.objects.create(client=self.client1, event=self.event, assigned_packer=self.packer, status="new")
        self.order_other = Order.objects.create(client=self.client2, event=self.event, assigned_packer=self.other_packer, status="new")

        self.task_own = Task.objects.create(title="Own", type="ORDER", order=self.order_own, assigned=self.packer, status="TODO")
        self.task_other = Task.objects.create(title="Other", type="ORDER", order=self.order_other, assigned=self.other_packer, status="TODO")

    def _create_user(self, username, groups):
        from django.contrib.auth import get_user_model

        user = get_user_model().objects.create_user(username=username, password="123")
        for group in groups:
            user.groups.add(group)
        return user

    def test_packer_sees_only_assigned_objects(self):
        self.client.force_login(self.packer)

        resp_orders = self.client.get(reverse("mobile_workspace"), {"tab": "orders"})
        order_ids = {o.id for o in resp_orders.context["orders"]}
        self.assertEqual(order_ids, {self.order_own.id})

        resp_tasks = self.client.get(reverse("mobile_workspace"), {"tab": "tasks"})
        task_ids = {t.id for t in resp_tasks.context["tasks"]}
        self.assertEqual(task_ids, {self.task_own.id})

    def test_owner_sees_all_objects(self):
        self.client.force_login(self.owner)
        resp = self.client.get(reverse("mobile_workspace"), {"tab": "orders"})
        order_ids = {o.id for o in resp.context["orders"]}
        self.assertEqual(order_ids, {self.order_own.id, self.order_other.id})

    def test_packer_can_update_own_order_status(self):
        self.client.force_login(self.packer)
        resp = self.client.post(
            reverse("mobile_workspace"),
            {
                "entity": "order",
                "object_id": self.order_own.id,
                "status": "processing",
                "tab": "orders",
            },
        )
        self.assertEqual(resp.status_code, 302)
        self.order_own.refresh_from_db()
        self.assertEqual(self.order_own.status, "processing")

    def test_packer_cannot_update_foreign_order(self):
        self.client.force_login(self.packer)
        resp = self.client.post(
            reverse("mobile_workspace"),
            {
                "entity": "order",
                "object_id": self.order_other.id,
                "status": "processing",
                "tab": "orders",
            },
        )
        self.assertEqual(resp.status_code, 404)
        self.order_other.refresh_from_db()
        self.assertEqual(self.order_other.status, "new")

    def test_invalid_status_does_not_change_task(self):
        self.client.force_login(self.packer)
        resp = self.client.post(
            reverse("mobile_workspace"),
            {
                "entity": "task",
                "object_id": self.task_own.id,
                "status": "INVALID",
                "tab": "tasks",
            },
            follow=True,
        )
        self.assertEqual(resp.status_code, 200)
        self.task_own.refresh_from_db()
        self.assertEqual(self.task_own.status, "TODO")
        msgs = [m.message for m in get_messages(resp.wsgi_request)]
        self.assertTrue(msgs)
