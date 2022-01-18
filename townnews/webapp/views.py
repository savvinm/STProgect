from django.shortcuts import render, redirect
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse, HttpResponseNotFound, Http404, HttpResponseRedirect
from .forms import LoginForm, NewsForm, PromoForm, TagForm
from .models import Admin, Resources, NewsArticles, City, Promo, Tag, MissingPeople
from hashlib import sha256, sha1
from django.http import JsonResponse
from PIL import Image
import datetime


def imageToJson(imagePath):
    name = imagePath.split("/")
    res = name[2] + "." + name[3]
    return res

def getImage(request, imagePath):
    response = HttpResponse(content_type="image/png")
    name = imagePath.split(".")
    imagePath = "static/images/" + name[0] + "/" + name[1] + "." + name[2]
    img = Image.open(imagePath)
    img.save(response, 'png')
    return response


def missingList(request):
    missing=MissingPeople.objects.all()
    res = []
    for mis in missing:
        res.append({
            'id': mis.id,
            'name': mis.name,
            'clothes': mis.clothes,
            'specCharacteristics': mis.specCharacteristics,
            'characteristics': mis.characteristics,
            'lastLocation': mis.lastLocation,
            'dateOfBirth': mis.dateOfBirth,
            'sex': mis.sex,
            'telephone': mis.telephone,
            'imageUrl': imageToJson(str(mis.image.path)),
            'city': str(mis.city.cityName),
        })
    return JsonResponse(res, safe=False)

def promosList(request):
    promos=Promo.objects.all()
    res = []
    for promo in promos:
        if(promo.expirationTime > datetime.datetime.now().date()):
            res.append({
                'id': promo.id,
                'title': promo.title,
                'promocode': promo.promocode,
                'expirationTime': promo.expirationTime,
                'imageUrl': imageToJson(str(promo.image.path)),
                'city': str(promo.city.cityName),
            })
    return JsonResponse(res, safe=False)

def articlesList(request):
    articles=NewsArticles.objects.all()
    res = []
    for article in articles:
        res.append({
            'id': article.id,
            'title': article.title,
            'content': article.mainText,
            'creationTime': article.creationTime,
            'tag': str(article.tag.title),
            'imageUrl': imageToJson(str(article.image.path)),
            'city': str(article.city.cityName),
        })
    return JsonResponse(res, safe=False)

def filterArticlesList(request, tag_id):
    articles=list(NewsArticles.objects.filter(tag=tag_id))
    res = []
    for article in articles:
        res.append({
            'id': article.id,
            'title': article.title,
            'content': article.mainText,
            'creationTime': article.creationTime,
            'tag': str(article.tag.title),
            'imageUrl': imageToJson(str(article.image.path)),
            'city': str(article.city.cityName),
        })
    return JsonResponse(res, safe=False)



def TagsToSelect():
    CHOICES = []
    tags = Tag.objects.all()
    for tag in tags:
        choice = (tag.id, tag.title)
        CHOICES.append(choice)
    return CHOICES
def TagsWithPriority():
    CHOICES = []
    tagsList = list(Tag.objects.all())
    priority = False
    priorityId = 0
    for tag in tagsList:
        if(tag.important == 1):
            priority = True
            priorityId = tag.id
    if(priority):
        CHOICES.append((tagsList[priorityId-1].id, tagsList[priorityId-1].title))
        for tag in tagsList:
            if(tag.id != priorityId):
                choice = (tag.id, tag.title)
                CHOICES.append(choice)
    else:
        CHOICES.append((0, "Приоритетный тег не выбран"))
        for tag in tagsList:
            choice = (tag.id, tag.title)
            CHOICES.append(choice)
    return CHOICES
def GetNewAdverts():
    adverts = list(MissingPeople.objects.filter(status="moderating"))
    return adverts

def clearTag():
    try:
        tag = Tag.objects.get(important=1)
        tag.important = 0
        tag.save()
        return
    except Tag.DoesNotExist:
        return
def CheckTag():
    try:
        tag = Tag.objects.get(important=1)
        return True
    except Tag.DoesNotExist:
        return False
def index(request):
    try:
        login = request.session['login']
        if(login):
            if request.method == "POST":
                tagId = request.POST.get("tag")
                if(int(tagId) != 0):
                    clearTag()
                    tag = Tag.objects.get(id=tagId)
                    tag.important = 1
                    tag.save()
                city = request.session['city']
                tagform = TagForm()
                tagform.fields["tag"].choices = TagsWithPriority()
                return render(request, "index.html",{"form": tagform, "isTag": CheckTag(), "advertsCount": len(GetNewAdverts()), "city":city, "login": login})
            else:
                city = request.session['city']
                tagform = TagForm()
                tagform.fields["tag"].choices = TagsWithPriority()
                return render(request, "index.html",{"form": tagform, "isTag": CheckTag(), "advertsCount": len(GetNewAdverts()), "city":city, "login": login})
    except KeyError:
        raise Http404()
def clearPriority(request):
    try:
        login = request.session['login']
        if(login):
            clearTag()
            return HttpResponseRedirect('/')
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
                tag = request.POST.get("tag")
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
                article.tag = Tag.objects.get(id=tag)
                article.image = Resources.objects.get(path=filename)
                article.mainText = text
                cr_time = datetime.datetime.now().isoformat(' ', 'seconds')
                article.creationTime = cr_time
                article.city = City.objects.get(id=request.session['city_id'])
                article.save()
                return HttpResponseRedirect('/')
            else:
                city = request.session['city']
                newsform = NewsForm(request.POST, request.FILES)
                newsform.fields["tag"].choices = TagsToSelect()
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

                        return HttpResponseRedirect('/')
                    else:
                        promoform = PromoForm(request.POST, request.FILES)
                        city = request.session['city']
                        return render(request, "addpromo.html", {"form": promoform, "city":city, "login": login})
        except KeyError:
            raise Http404()

def newadverts(request):
    try:
        login = request.session['login']
        if(login):
            adverts = GetNewAdverts()
            city = request.session['city']
            return render(request, "newadverts.html", {"adverts":adverts, "city":city, "login": login})
    except KeyError:
        raise Http404()
def reject(request, id):
        try:
            login = request.session['login']
            if(login):
                advent = MissingPeople.objects.get(id=id)
                advent.status = "rejected"
                advent.save()
                return HttpResponseRedirect('/newadverts')
        except KeyError:
            raise Http404()
def accept(request, id):
    try:
        login = request.session['login']
        if(login):
            advent = MissingPeople.objects.get(id=id)
            advent.status = "accepted"
            advent.save()
            return HttpResponseRedirect('/newadverts')
    except KeyError:
        raise Http404()
