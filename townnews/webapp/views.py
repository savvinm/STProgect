from django.shortcuts import render
from django.http import HttpResponse

def index(request):
    return render(request, "index.html")

def login(request):
    return render(request, "login.html")

def addnews(request):
    return render(request, "addnews.html")

def addpromo(request):
    return render(request, "addpromo.html")
