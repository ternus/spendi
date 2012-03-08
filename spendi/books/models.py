from django.contrib.auth.models import User
from django.db import models
from spendi.users.models import SpendiGroup
from django.db.models.fields import DateTimeField, FloatField, CharField, TextField
from django.db.models.fields.related import ForeignKey, ManyToManyField
from currencies import currencies

class Expenditure(models.Model):
    group = ForeignKey(SpendiGroup)

    spender = ForeignKey(User, related_name="spender")

    created = DateTimeField(auto_now_add=True)
    created_by = ForeignKey(User, related_name="creator", blank=True,null=True)
    updated = DateTimeField(auto_now=True)
    updated_by = ForeignKey(User, related_name="updater", blank=True,null=True)

    users = ManyToManyField(User, through='ExpenditureSplit')

    description = TextField(blank=True,null=True)

    amount = FloatField()
    currency = CharField(max_length=3, choices=currencies)

    def total_shares(self):
        return sum(ExpenditureSplit.objects.filter(expenditure=self).values_list('share', flat=True))

    def owed_amount(self, user):
        if not user in self.users.all(): return 0.0
        return round(self.amount * (ExpenditureSplit.objects.get(expenditure=self, user=user).share / self.total_shares()), 2)

    def __unicode__(self):
        return "$%s spent by %s on %s" % (self.amount, self.spender, self.created)

class ExpenditureSplit(models.Model):
    user = ForeignKey(User)
    expenditure = ForeignKey(Expenditure)
    share = FloatField(default=1.0)

class Transfer(models.Model):
    group = ForeignKey(SpendiGroup)

    from_user = ForeignKey(User, related_name="from_user")
    to_user = ForeignKey(User, related_name="to_user")

    created = DateTimeField(auto_now_add=True)
    created_by = ForeignKey(User, related_name="transfer_creator")

    amount = FloatField()
    currency = CharField(max_length=3, choices=currencies)
