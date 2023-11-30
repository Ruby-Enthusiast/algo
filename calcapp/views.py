from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse

# Create your views here.

def index(request):
    return render(request, 'calcapp/index.html')

def send_query(request):
    q1 = request.GET.get('query1', '')
    
    checkboxes = request.GET.getlist('checkboxes')

    url = reverse('news:grab') + f'?query1={q1}&'
    url += '&'.join([f'query{i + 2}={checkbox}' for i, checkbox in enumerate(checkboxes)])

    return HttpResponseRedirect(url)