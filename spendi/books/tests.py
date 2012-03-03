"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""
from django.contrib.auth.models import User

from django.test import TestCase
from spendi.users.models import GroupMembership, UserGroup


class BooksTest(TestCase):

    def create_users(self):
        group = UserGroup.objects.create(name="Our House")
        group.save()
        alice = User.objects.create(username='alice')
        alice.save()
        GroupMembership(user=alice, group=group).save()
        self.assertTrue(alice in group.users.all())
        bob = User(username='bob')
        bob.save()
        GroupMembership(user=bob, group=group).save()
        charlie = User(username='charlie')
        charlie.save()
        GroupMembership(user=charlie, group=group).save()
        deb = User(username='deb')
        deb.save()
        GroupMembership(user=deb, group=group).save()
        deb.save()

        return group, alice, bob, charlie, deb

    def test_simple_expenditure(self):
        group, alice, bob, charlie, deb = self.create_users()
        group.spend(alice, 30.0, ((alice, 1), (charlie, 1), (bob, 1)))
        self.assertEquals(group.user_owes(charlie, alice), 10.0)
        self.assertEquals(group.user_owes(bob, alice), 10.0)
        self.assertEquals(group.user_owes(alice, alice), 0.0)

    def test_double_expenditure(self):
        group, alice, bob, charlie, deb = self.create_users()
        group.spend(alice, 100.0, ((alice, 1), (charlie, 1), (bob, 3)))
        self.assertEquals(group.user_owes(charlie, alice), 20.0)
        self.assertEquals(group.user_owes(bob, alice), 60.0)
        self.assertEquals(group.user_owes(alice, alice), 0.0)

        group.spend(alice, 100.0, ((alice, 1), (charlie, 1), (bob, 3)))
        self.assertEquals(group.user_owes(charlie, alice), 40.0)
        self.assertEquals(group.user_owes(bob, alice), 120.0)
        self.assertEquals(group.user_owes(alice, alice), 0.0)

    def test_more_complex_expenditure(self):
        group, alice, bob, charlie, deb = self.create_users()
        group.spend(alice, 100.0, ((alice, 1), (charlie, 1), (bob, 3)))
        # C->A 20, B->A 60
        self.assertEquals(group.user_owes(charlie, alice), 20.0)
        self.assertEquals(group.user_owes(bob, alice), 60.0)
        self.assertEquals(group.user_owes(alice, alice), 0.0)


        group.spend(bob, 100.0, ((alice, 3), (charlie, 1), (bob, 1)))
        # A->B 60, C->B 20
        self.assertEquals(group.user_owes(charlie, alice), 20.0)
        self.assertEquals(group.user_owes(charlie, bob), 20.0)
        self.assertEquals(group.user_owes(bob, alice), 0.0)
        self.assertEquals(group.user_owes(bob, charlie), 0.0)

    def test_expenditure_not_including_spender(self):
        group, alice, bob, charlie, deb = self.create_users()
        group.spend(bob, 20.0, ((alice,1),(charlie,1)))
        self.assertEquals(group.user_owes(alice, bob), 10.0)
        self.assertEquals(group.user_owes(charlie, bob), 10.0)

    def test_negative_expenditure(self):
        group, alice, bob, charlie, deb = self.create_users()
        group.spend(bob, -100.0, ((alice,1),))
        self.assertEquals(group.user_owes(bob, alice), 100.0)

    def test_single_penny(self):
        group, alice, bob, charlie, deb = self.create_users()
        group.spend(bob, .05, ((alice,1),(charlie,1),(bob,1)))
        self.assertEquals(group.user_owes(alice, bob), 0.02)
        self.assertEquals(group.user_owes(charlie, bob), 0.01)

    def test_multiple_pennies(self):
        group, alice, bob, charlie, deb = self.create_users()
        group.spend(bob, .06, ((alice,1),(charlie,1),(bob,1),(deb, 1)))
        self.assertEquals(group.user_owes(alice, bob), 0.01)
        self.assertEquals(group.user_owes(charlie, bob), 0.02)
        self.assertEquals(group.user_owes(deb, bob), 0.01)

    def test_fair_penny_allocation(self):
        group, alice, bob, charlie, deb = self.create_users()
        group.spend(alice, .01, ((alice,1),(bob,1),(charlie,1),(deb, 1)))
        self.assertEquals(group.user_owes(bob, alice), 0.01)
        self.assertEquals(group.user_owes(charlie, alice), 0.00)
        self.assertEquals(group.user_owes(deb, alice), 0.00)

        group.spend(alice, .01, ((alice,1),(bob,1),(charlie,1),(deb, 1)))
        self.assertEquals(group.user_owes(bob, alice), 0.01)
        self.assertEquals(group.user_owes(charlie, alice), 0.01)
        self.assertEquals(group.user_owes(deb, alice), 0.00)

        group.spend(alice, .01, ((alice,1),(bob,1),(charlie,1),(deb, 1)))
        self.assertEquals(group.user_owes(bob, alice), 0.01)
        self.assertEquals(group.user_owes(charlie, alice), 0.01)
        self.assertEquals(group.user_owes(deb, alice), 0.01)

        group.spend(alice, .01, ((alice,1),(bob,1),(charlie,1),(deb, 1)))
        self.assertEquals(group.user_owes(bob, alice), 0.01)
        self.assertEquals(group.user_owes(charlie, alice), 0.01)
        self.assertEquals(group.user_owes(deb, alice), 0.01)

        group.spend(alice, .01, ((alice,1),(bob,1),(charlie,1),(deb, 1)))
        self.assertEquals(group.user_owes(bob, alice), 0.02)
        self.assertEquals(group.user_owes(charlie, alice), 0.01)
        self.assertEquals(group.user_owes(deb, alice), 0.01)

    def test_round_robin_expenditure(self):
        group, alice, bob, charlie, deb = self.create_users()
        group.spend(alice, 100.0, ((alice, 1), (bob, 1), (charlie,1), (deb,1)))
        # C->A 20, B->A 60
        self.assertEquals(group.user_owes(charlie, alice), 25.0)
        self.assertEquals(group.user_owes(bob, alice), 25.0)
        self.assertEquals(group.user_owes(deb, alice), 25.0)
        self.assertEquals(group.user_owes(alice, alice), 0.0)

        group.spend(bob, 100.0, ((alice, 1), (bob, 1), (charlie,1), (deb,1)))
        # C->A 20, B->A 60
        self.assertEquals(group.user_owes(charlie, alice), 50.0)
        self.assertEquals(group.user_owes(deb, bob), 50.0)
        self.assertEquals(group.user_owes(alice, alice), 0.0)
        self.assertEquals(group.user_owes(charlie, deb), 0.0)
        self.assertEquals(group.user_owes(bob, deb), 0.0)
        self.assertEquals(group.user_owes(bob, bob), 0.0)

        group.spend(charlie, 100.0, ((alice, 1), (bob, 1), (charlie,1), (deb,1)))
        # C->A 20, B->A 60
        self.assertEquals(group.user_owes(deb, alice), 25.0)
        self.assertEquals(group.user_owes(deb, bob), 25.0)
        self.assertEquals(group.user_owes(deb, charlie), 25.0)

        group.spend(deb, 100.0, ((alice, 1), (bob, 1), (charlie,1), (deb,1)))
        # C->A 20, B->A 60
        self.assertEquals(group.user_owes(deb, alice), 0.0)
        self.assertEquals(group.user_owes(deb, bob), 0.0)
        self.assertEquals(group.user_owes(deb, charlie), 0.0)
