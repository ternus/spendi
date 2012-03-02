from spendi.books.models import Expenditure, ExpenditureSplit
from spendi.books.views import cook_books

def spend(group, spender, amount, shares):
    e = Expenditure(group=group, spender=spender, amount=amount, created_by=spender, updated_by=spender)
    e.save()
    for s in shares:
        ExpenditureSplit.objects.create(expenditure=e, user=s[0], shares=s[1])
    return e

def user_owes(group, user, to):
    books = cook_books(group)
    if not len(books[user]): return 0.0
    for t in books[user]:
        if t.user == to:
            return t.amount
    return 0.0
