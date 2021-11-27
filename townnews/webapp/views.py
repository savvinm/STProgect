from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseNotFound, Http404, HttpResponseRedirect
from .forms import LoginForm, NewsForm, PromoForm
from .models import Admin
from hashlib import sha256

def index(request):
    try:
        login = request.session['login']
        if(login):
            return render(request, "index.html")
    except KeyError:
        raise Http404()

def login(request):
    try:
        login = request.session['login']
        if(login):
            del request.session['login']
    finally:
        if request.method == "POST":
            login = request.POST.get("login")
            password = request.POST.get("password")
            message = ""
            try:
                admin = Admin.objects.get(login=login)
                hash = sha256(password.encode('utf-8')).hexdigest()
                if(admin.password == hash):
                    request.session['login'] = login
                    return HttpResponseRedirect('/')
                else:
                    message = "Неверный логин или пароль"
                    loginform = LoginForm()
                    return render(request, "login.html", {"form": loginform, "message": message})
            except Admin.DoesNotExist:
                message = "Неверный логин или пароль"
                loginform = LoginForm()
                return render(request, "login.html", {"form": loginform, "message": message})
        else:
            loginform = LoginForm()
            return render(request, "login.html", {"form": loginform})

def addnews(request):
    try:
        login = request.session['login']
        if(login):
                if request.method == "POST":
                    title = request.POST.get("title")
                    tags = request.POST.get("tags")
                    image = request.POST.get("image")
                    text = request.POST.get("text")
                    return HttpResponse("<h2>Новая запись {0} создана</h2>".format(title))
                else:
                    newsform = NewsForm()
                    return render(request, "addnews.html", {"form": newsform})
    except KeyError:
        raise Http404()

def addpromo(request):
        try:
            login = request.session['login']
            if(login):
                    if request.method == "POST":
                        title = request.POST.get("title")
                        code = request.POST.get("code")
                        image = request.POST.get("image")
                        return HttpResponse("<h2>Новое промо {0} создано</h2>".format(title))
                    else:
                        promoform = PromoForm()
                        return render(request, "addpromo.html", {"form": promoform})
        except KeyError:
            raise Http404()
