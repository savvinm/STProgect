from django.shortcuts import render, redirect
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse, HttpResponseNotFound, Http404, HttpResponseRedirect
from .forms import LoginForm, NewsForm, PromoForm
from .models import Admin, Resources, NewsArticles, City, Promo
from hashlib import sha256, sha1
import datetime

def index(request):
    try:
        login = request.session['login']
        if(login):
            city = request.session['city']
            return render(request, "index.html",{"city":city, "login": login})
    except KeyError:
        raise Http404()

def login(request):
    try:
        login = request.session['login']
        if(login):
            del request.session['login']
            del request.session['city_id']
            del request.session['city']
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
                    request.session['city_id'] = admin.city_id
                    request.session['city'] = admin.city.formForText
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
            if request.method == "POST" and request.FILES:
                title = request.POST.get("title")
                tags = request.POST.get("tags")
                image = request.FILES["image"]
                text = request.POST.get("text")

                name = image.name.split(".")
                fs = FileSystemStorage()
                dt_now = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
                imgname = sha1((dt_now + image.name).encode('utf-8')).hexdigest()
                filename = "static/images/articles/" + imgname + "." + name[-1]
                path = fs.save(filename, image)
                resource = Resources()
                resource.path = filename
                resource.save()

                article = NewsArticles()
                article.title = title
                article.tags = tags
                article.image = Resources.objects.get(path=filename)
                article.mainText = text
                cr_time = datetime.datetime.now().isoformat(' ', 'seconds')
                article.creationTime = cr_time
                article.city = City.objects.get(id=request.session['city_id'])
                article.save()

                return HttpResponse("<h2>Новая запись {0} создана</h2>".format(title))
            else:
                city = request.session['city']
                newsform = NewsForm(request.POST, request.FILES)
                return render(request, "addnews.html", {"form": newsform, "city":city, "login": login})
    except KeyError:
        raise Http404()

def addpromo(request):
        try:
            login = request.session['login']
            if(login):
                    if request.method == "POST":
                        title = request.POST.get("title")
                        code = request.POST.get("code")
                        image = request.FILES["image"]
                        expirationMonth = request.POST.get("expirationDate_month")
                        expirationDay = request.POST.get("expirationDate_day")
                        expirationYear = request.POST.get("expirationDate_year")

                        name = image.name.split(".")
                        fs = FileSystemStorage()
                        dt_now = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
                        imgname = sha1((dt_now + image.name).encode('utf-8')).hexdigest()
                        filename = "static/images/promo/" + imgname + "." + name[-1]
                        path = fs.save(filename, image)
                        resource = Resources()
                        resource.path = filename
                        resource.save()

                        promo = Promo()
                        promo.title = title
                        promo.promocode = code
                        promo.image = Resources.objects.get(path=filename)
                        cr_time = datetime.datetime.now().isoformat(' ', 'seconds')
                        promo.creationTime = cr_time
                        ex_time = datetime.date(int(expirationYear), int(expirationMonth), int(expirationDay))
                        promo.expirationTime = ex_time
                        promo.city = City.objects.get(id=request.session['city_id'])
                        promo.save()

                        return HttpResponse("<h2>Новое промо {0} создано</h2>".format(ex_time))
                    else:
                        promoform = PromoForm(request.POST, request.FILES)
                        city = request.session['city']
                        return render(request, "addpromo.html", {"form": promoform, "city":city, "login": login})
        except KeyError:
            raise Http404()
