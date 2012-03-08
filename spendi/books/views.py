# Create your views here.
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.template.context import RequestContext
from spendi.books.models import Expenditure, Transfer
from spendi.contrib.json_view import json_view
from spendi.users.models import SpendiGroup


#@login_required
def dashboard(request, gslug, template="books/dashboard.html"):
    try:
        group = SpendiGroup.objects.get(slug=gslug)
    except SpendiGroup.DoesNotExist:
        raise Http404("That group doesn't exist!")
    context = {
        "group": group,
        "expenditures": Expenditure.objects.filter(group=group)
    }
    return render_to_response(template, context, context_instance=RequestContext(request))

@json_view
def ajax_spend(request):
    group = request.POST.get('group', None)
    user = request.POST.get('user', None)
    amount = request.POST.get('amount', None)
    description = request.POST.get('description', None)

    group = get_object_or_404(SpendiGroup, group)
    user = get_object_or_404(User, user)

    group.spend(user, amount, description)

    return {"result": "ok"}


@json_view
def ajax_add_user(request):
    group = request.POST.get('group', None)
    user = request.POST.get('user', None)
    amount = request.POST.get('amount', None)
    description = request.POST.get('description', None)

    group = get_object_or_404(SpendiGroup, group)
    user = get_object_or_404(User, user)

    group.spend(user, amount, description)

    return {"result": "ok"}

