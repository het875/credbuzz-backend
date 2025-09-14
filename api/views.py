from django.http import JsonResponse


def health(request):
    return JsonResponse({'status': 'ok', 'service': 'credbuzzpay-backend'})
from django.shortcuts import render

# Create your views here.
