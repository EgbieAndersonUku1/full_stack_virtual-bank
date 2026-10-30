from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect


# Create your views here.

@login_required
@csrf_protect
def notifications_centre(request):
    return render(request, "home/notifications/base.html")
