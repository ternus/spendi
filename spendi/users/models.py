import logging
from django.db import models
from django.contrib.auth.models import User
from django.db.models.fields import CharField, TextField, DateTimeField, BooleanField
from django.db.models.fields.related import ManyToManyField, ForeignKey

logger = logging.getLogger(__name__)


def _c(amt):
    return amt

class BadRecordException(Exception):
    pass

class Debt(object):
    """
    A helper class used in books calculation.
    """
    def __init__(self, user, amount, to_user=None):
        self.user = user
        self.to_user = to_user
        self.amount = amount

    def __unicode__(self):
        if self.to_user:
            return "%s owes %s $%s" % (self.user.username, self.to_user.username, _c(self.amount))
        elif self.amount > 0:
            return "%s owes the house $%s" % (self.user.username, _c(self.amount))
        else:
            return "The house owes %s $%s" % (self.user.username, _c(abs(self.amount)))

    def __repr__(self):
        return self.__unicode__()


class SpendiGroup(models.Model):
    """
    A group of users, such as a household or business.
    """
    name = CharField(max_length=200)
    slug = CharField(max_length=65, unique=True)
    description = TextField()
    users = ManyToManyField(User, through='GroupMembership')
    last_update = DateTimeField(auto_now=True)

    @property
    def books(self):
        """
        Implementation of the min
        """
        from spendi.books.models import Expenditure, Transfer

        users_owe = dict((user, 0) for user in self.users.all())
        expenditures = Expenditure.objects.filter(group=self)
        transfers = Transfer.objects.filter(group=self)

        for e in expenditures:
            if not e.users.all().count():
                logging.warning("Expenditure with no shares?  Ignoring -- please fix!")
                continue
            logging.debug("Expenditure: %s spent %s" % (e.spender, e.amount))
            users_owe[e.spender] -= round(e.amount, 2)
            for u in e.users.all():
                users_owe[u] += round(e.owed_amount(u), 2)
            pennies = e.amount - sum(e.owed_amount(u) for u in e.users.all())
            if pennies:
                pf = -1 if pennies < 0 else 1 # "Penny factor"
                for pn in range(0, abs(int(pennies * 100))):
                    # (fairly and consistently) pick users to assign the pennies to.
                    # It'll either be +0.01 or -0.01.
                    user = list(e.users.all())[(e.id + pn) % e.users.all().count()]
                    logging.debug("Pennies left over: %s (pn %s, id %s, picking %s)" % (pennies, pn, e.id, user))
                    users_owe[user] += (.01 * pf)


        for t in transfers:
            users_owe[t.from_user] -= t.amount
            users_owe[t.to_user] += t.amount

        # Now we have a list of who owes the house what.

        debtors = list(Debt(user=x[0], amount=x[1]) for x in filter(lambda x: x[1] > 0, users_owe.items()))
        debtors.sort(key=lambda x: x.amount)
        logger.debug("Debtors are: %s" % debtors)
        creditors = list(Debt(user=x[0], amount=x[1]) for x in filter(lambda x: x[1] < 0, users_owe.items()))
        creditors.sort(key=lambda x: -x.amount)
        logger.debug("Creditors are: %s" % creditors)
        owe_each_other = dict((u1, []) for u1 in self.users.all())

        debt_amount = sum(map(lambda x: x.amount, debtors))
        credit_amount = sum(map(lambda x: x.amount, creditors))
        logging.debug("Credit = $%f , debt = $%f, total = $%f" % (debt_amount, credit_amount, debt_amount+credit_amount))
        if not (round(sum(map(lambda x: x.amount, debtors)) + sum(map(lambda x: x.amount, creditors)), 2) == 0.0):
            raise BadRecordException("Books don't add up to 0")

        while len(creditors) and len(debtors):
            to = creditors[0]
            o = debtors[0]
            if abs(o.amount) < abs(to.amount):
                logging.debug("%s paying %s %s" % (o.user, to.user, o.amount))
                owe_each_other[to.user].append(Debt(user=o.user, to_user=to.user, amount=o.amount))
                logging.debug("%s owed %s" % (o.user, o.amount))
                creditors[0].amount += round(o.amount, 2)
                if creditors[0].amount == 0.0:
                    logging.debug("%s is owed nothing; removing them." % creditors[0].user)
                    creditors.pop(0)
                logging.debug("removing %s" % o.user)
                debtors.pop(0)
            else:
                owe_each_other[to.user].append(Debt(user=o.user, to_user=to.user, amount=abs(to.amount)))
                logging.debug("%s paying %s %s" % (o.user, to.user, abs(to.amount)))
                logging.debug("%s owed %s" % (o.user, o.amount))
                debtors[0].amount -= round(abs(to.amount), 2)
                logging.debug("%s now owes %s" % (o.user, o.amount))
                if debtors[0].amount == 0.0:
                    logging.debug("%s owes nothing; removing them." % debtors[0].user)
                    debtors.pop(0)
                creditors.pop(0)

        if len(debtors):
            raise BadRecordException("%s people still owe money (%s)" % (len(debtors), debtors))

        return owe_each_other

    def residents(self):
        return User.objects.filter(id__in=GroupMembership.objects.filter(group=self, resident=True).values_list('user', flat=True))

    def spend(self, spender, amount, description, shares=None):
        from spendi.books.models import Expenditure, ExpenditureSplit

        if not shares:
            shares = list((u, 1) for u in self.residents())
            logging.debug("shares are %s" % shares)

        e = Expenditure(group=self,
                        spender=spender,
                        amount=amount,
                        created_by=spender,
                        updated_by=spender,
                        description=description)
        e.save()
        for s in shares:
            ExpenditureSplit(expenditure=e, user=s[0], share=s[1]).save()
        return e

    def user_owes(self, user, to):
        books = self.books
        if not len(books[to]): return 0.0
        for t in books[to]:
            if t.user == user:
                return round(t.amount,2)
        return 0


class GroupMembership(models.Model):
    """
    Intermediate model representing group ownership.
    """
    group = ForeignKey(SpendiGroup)
    user = ForeignKey(User)
    joined = DateTimeField(auto_now_add=True)
    resident = BooleanField(default=False)
    active = BooleanField(default=True)

    class Meta:
        unique_together=('group', 'user')