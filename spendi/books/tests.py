"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""
from django.contrib.auth.models import User

from django.test import TestCase
from spendi.books.utils import spend
from spendi.users.models import GroupMembership, UserGroup


class SimpleTest(TestCase):

    def create_users(self):
        group = UserGroup(name="Event Horizon")
        ternus = User(username='ternus')
        GroupMembership.objects.create(user=ternus, group=group)
        gonzo = User(username='gonzo')
        GroupMembership.objects.create(user=gonzo, group=group)
        keach = User(username='keach')
        GroupMembership.objects.create(user=keach, group=group)
        kyoki = User(username='kyoki')

        return group, ternus, gonzo, keach, kyoki

    def test_spend(self):
        group, ternus, gonzo, keach, kyoki = self.create_users()
        spend(group, ternus, 100.0, ((ternus, 2), (keach, 1), (gonzo, 3)))