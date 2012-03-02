# Create your views here.
from spendi.books.models import Expenditure, Transfer

class BadRecordException(Exception):
    pass

class Debt(object):
    def __init__(self, user, amount, to_user=None):
        self.user = user
        self.to_user = to_user
        self.amount = amount

    def __unicode__(self):
        if self.to_user:
            return "%s owes %s $%s" % (self.user.username, self.to_user.username, self.amount)
        elif self.amount > 0:
            return "%s owes the house $%s" % (self.user.username, self.amount)
        else:
            return "The house owes %s $%s" % (self.user.username, self.amount)

    def __repr__(self):
        return self.__unicode__()

def cook_books(group):

    users_owe = dict((user, 0.0) for user in group.users.all())
    expenditures = Expenditure.objects.filter(group=group)
    transfers = Transfer.objects.filter(group=group)

    for e in expenditures:
        users_owe[e.spender] -= e.amount
        for u in e.users.all():
            users_owe[u] += e.owed_amount(u)

    for t in transfers:
        users_owe[t.from_user] -= t.amount
        users_owe[t.to_user] += t.amount

    # Now we have a list of who owes the house what.

    debtors = list(Debt(user=x[0], amount=x[1]) for x in filter(lambda x: x[1] > 0, users_owe.items()))
    print debtors
    debtors.sort(key=lambda x: x.amount)
    creditors = list(Debt(user=x[0], amount=x[1]) for x in filter(lambda x: x[1] < 0, users_owe.items()))
    print creditors
    creditors.sort(key=lambda x: -x.amount)
    owe_each_other = dict((u1, []) for u1 in group.users.all())

    if not (sum(map(lambda x: x.amount, debtors)) + sum(map(lambda x: x.amount, creditors)) == 0):
        raise BadRecordException("Books don't add up to 0")

    while len(creditors) and len(debtors):
        print owe_each_other
        print creditors
        print debtors
        to = creditors[0]
        o = debtors[0]
        if abs(o.amount) < abs(to.amount):
            print 'Creditor is owed more than top debtor'
            owe_each_other[to.user].append(Debt(user=o.user, to_user=to.user, amount=o.amount))
            creditors[0].amount += o.amount
            if creditors[0].amount == 0.0:
                creditors.pop(0)
            debtors.pop(0)
        else:
            print 'Debtor owes more (or equal to) top creditor'
            owe_each_other[to.user].append(Debt(user=o.user, to_user=to.user, amount=abs(to.amount)))
            debtors[0].amount -= o.amount
            if debtors[0].amount == 0.0:
                debtors.pop(0)
            creditors.pop(0)

    if len(debtors):
        raise BadRecordException("%s people still owe money (%s)" % (len(debtors), debtors))

    return owe_each_other






