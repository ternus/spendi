from django.db import models
from django.contrib.auth.models import User
from django.db.models.fields import CharField, TextField, DateTimeField, BooleanField
from django.db.models.fields.related import ManyToManyField, ForeignKey

class UserGroup(models.Model):
    name = CharField(max_length=200)
    slug = CharField(max_length=65)
    description = TextField()
    users = ManyToManyField(User, through='GroupMembership')

class GroupMembership(models.Model):
    group = ForeignKey(UserGroup)
    user = ForeignKey(User)
    joined = DateTimeField(auto_now_add=True)
    resident = BooleanField(default=False)
    active = BooleanField(default=True)