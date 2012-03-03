# Create your views here.
from django.contrib.auth.decorators import login_required
from spendi.books.models import Expenditure, Transfer


@login_required
def dashboard(request, group, template=None):





