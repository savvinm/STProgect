from django.shortcuts import render, redirect
from django.core.files.storage import FileSystemStorage
from django.core.files.base import ContentFile
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, HttpResponseNotFound, Http404, HttpResponseRedirect, HttpResponsePermanentRedirect
from .forms import LoginForm, NewsForm, PromoForm, TagForm
from .models import Admin, Resources, NewsArticles, City, Promo, Tag, MissingPeople, User, Favorites, DeferredLinks, AppInit
from hashlib import sha256, sha1
from django.http import JsonResponse
from PIL import Image, ExifTags
import datetime
import json
import base64
import textwrap
from datetime import timezone, timedelta

timezone_offset = +3.0  
tzinfo = timezone(timedelta(hours=timezone_offset))
months = {'1': "января",'2': "февраля",'3': "марта",'4': "апреля",'5': "мая",'6': "июня",'7': "июля",'8': "августа",'9': "сентября",'10': "октября",'11': "ноября",'12': "декабря"}

def isEqualIOS(iOSVersion, platform):
    keys = platform.split(' ')
    version = ""
    for i in range(len(keys)):
        if (keys[i] == "OS" and i < len(keys) - 1):
            if keys[i-1] == "iPhone":
                version = keys[i+1]
                break
    if version != "":
        version = version.replace('_','.')
        if version == iOSVersion:
            return True
    return False


def findTask(address, iOSVersion):
    tasks = list(DeferredLinks.objects.filter(address=address).filter(status="created"))
    if not tasks:
        return "none"
    else:
        tasks.reverse()
        for task in tasks:
            if isEqualIOS(iOSVersion, task.platform):
                dif = datetime.datetime.now().timestamp() - task.creationTime.timestamp() 
                if (dif < 1200.0):
                    return task
    return "none"
    
def addOrUpdateInit(address, iOSVersion, uuiId):
    try: 
        init = AppInit.objects.get(address=address, platform=iOSVersion, uuiId=uuiId)
        init.lastInit = datetime.datetime.now()
        init.save()
    except AppInit.DoesNotExist:
        init = AppInit()
        init.address = address
        init.platform = iOSVersion
        init.uuiId = uuiId
        init.lastInit = datetime.datetime.now()
        init.save()
  
@csrf_exempt    
def appInit(request, iOSVersion, uuiId):
    address = request.META['REMOTE_ADDR']
    addOrUpdateInit(address, iOSVersion, uuiId)
    task = findTask(address, iOSVersion)
    if task != "none":
        task.status = "opened"
        task.save()
        res = {
                'task': task.task,
            }
        return JsonResponse(res, safe=False)
        
  
@csrf_exempt
def checkInit(address, platform):
    inits = list(AppInit.objects.filter(address=address))
    if not inits:
        return False
    else:
        for init in inits:
            if isEqualIOS(init.platform, platform):
                dif = datetime.datetime.now().timestamp() - init.lastInit.timestamp() 
                if (dif < 2592000.0):
                    return True
    return False

@csrf_exempt   
def deferredArticle(request, articleId):
    meta = request.META
    if not checkInit(meta['REMOTE_ADDR'], meta['HTTP_USER_AGENT']):
        task = DeferredLinks()
        task.platform = meta['HTTP_USER_AGENT']
        task.address = meta['REMOTE_ADDR']
        task.task = "article/" + str(articleId)
        task.status = "created"
        task.creationTime = datetime.datetime.now()
        task.save()
        response = HttpResponse("", status=302)
        response['Location'] = "https://google.com"
        return response
    
@csrf_exempt
def openApp(request):
    info = request.META['HTTP_USER_AGENT']
    if "iPhone" in info:
        response = HttpResponse("", status=302)
        response['Location'] = "townnews.app://"
        return response
    raise Http404()

@csrf_exempt
def openArticle(request, articleId):
    try:
        article = NewsArticles.objects.get(id=articleId)
        imagePath = imageToJson(str(article.image.path))
        title = article.title
        body = textwrap.shorten(article.mainText, width=190, placeholder="...")
        publishedTime = article.creationTime
        return render(request, "openArticle.html", {"articleId": articleId, "imagePath": imagePath, "title": title, "description": body, "publishedTime": publishedTime})
    except NewsArticles.DoesNotExist:
        raise Http404()

@csrf_exempt
def addMissingForUser(body, user):
    missing = MissingPeople()
    missing.name = body['name']
    missing.clothes = body['clothes']
    missing.characteristics = body['characteristics']
    missing.specCharacteristics = body['specCharacteristics']
    missing.lastLocation = body['lastLocation']
    missing.sex = body['sex']
    missing.creator = user
    missing.dateOfBirth = body['dateOfBirth']
    missing.telephone = body['phoneNumber']
    missing.city = City.objects.get(cityName=body['city'])
    missing.status="moderating"

    
    dt_now = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    imgname = sha1((dt_now + user.login).encode('utf-8')).hexdigest()
    filename = "static/images/missing/" + imgname + ".jpg"
    with open(filename, "wb") as fh:
        fh.write(base64.b64decode(body["image"]))
        
    resource = Resources()
    resource.path = filename
    resource.save()
    missing.image = Resources.objects.get(path=filename)
    try:
        missing.save()
        return True
    except:
        return False

@csrf_exempt
def addUser(uuiId):
    if(uuiId != ""):
        user = User()
        user.login = uuiId
        try:
            user.save()
            return True
        except:
            return False


@csrf_exempt
def deleteMissing(request, id, uuiId):
    status = 200
    try:
        user = User.objects.get(login=uuiId)
        try:
            missing = MissingPeople.objects.get(creator=user.id, id=id)
            missing.status = "deleted"
            missing.save()
        except MissingPeople.DoesNotExist:
            status = 400
    except User.DoesNotExist:
        status = 400
    response = HttpResponse()
    response.status_code = status
    return response

@csrf_exempt
def addMissing(request):
    status = 200
    if(request.method == 'POST'):
        body = json.loads(request.body)
        uuiId = body['id']
        res = False
        try:
            user = User.objects.get(login=uuiId)
            res = addMissingForUser(body, user)
        except User.DoesNotExist:
            res = addUser(uuiId)
            if(res):
                user = User.objects.get(login=uuiId)
                res = addMissingForUser(body, user)
        if(res != True):
            status = 400
    response = HttpResponse()
    response.status_code = status
    return response

        
def imageToJson(imagePath):
    name = imagePath.split("/")
    res = "https://townnews.site/getimage/" + name[2] + "." + name[3]
    return res

def getImage(request, imagePath):
    response = HttpResponse(content_type="image/png")
    name = imagePath.split(".")
    imagePath = "static/images/" + name[0] + "/" + name[1] + "." + name[2]
    img = Image.open(imagePath)
    response = HttpResponse(content_type="image/png")
    img.save(response, 'png')
    return response

def ageToString(dateOfBirth):
    age = datetime.datetime.now().year - dateOfBirth.year
    if(dateOfBirth.month > datetime.datetime.now().month):
        age = age - 1
    return str(age) + " лет"
    
def missingList(request):
    missing=list(MissingPeople.objects.filter(status="accepted"))
    res = []
    for mis in missing:
        res.append({
            'id': mis.id,
            'name': mis.name,
            'clothes': mis.clothes,
            'specCharacteristics': mis.specCharacteristics,
            'characteristics': mis.characteristics,
            'lastLocation': mis.lastLocation,
            'age': ageToString(mis.dateOfBirth),
            'sex': mis.sex,
            'telephone': mis.telephone,
            'imageUrl': imageToJson(str(mis.image.path)),
            'city': str(mis.city.cityName),
            'status': mis.status,
        })
    res.reverse()
    return JsonResponse(res, safe=False)

def promosList(request):
    promos=Promo.objects.all()
    res = []
    for promo in promos:
        if(promo.expirationTime >= datetime.datetime.now(tzinfo).date()):
            res.append({
                'id': promo.id,
                'title': promo.title,
                'promocode': promo.promocode,
                'expirationTime': promo.expirationTime,
                'imageUrl': imageToJson(str(promo.image.path)),
                'city': str(promo.city.cityName),
            })
    res.reverse()
    return JsonResponse(res, safe=False)

def tagsList(request):
    tags=Tag.objects.all()
    res = []
    for tag in tags:
        res.append({
            'id': tag.id + 1,
            'title': tag.title,
            'important': tag.important,
        })
    return JsonResponse(res, safe=False)

def datetimeToString(dateTime):
    res = ""
    if(dateTime.date() == (datetime.datetime.now() + timedelta(hours=3)).date()):
        res = "Сегодня в "
        res += str(dateTime.time().hour) + ":" + str(dateTime.time().minute)
        return res
    if(dateTime.date() == (datetime.datetime.now() - timedelta(days=1) + timedelta(hours=3)).date()):
        res = "Вчера в "
        res += str(dateTime.time().hour) + ":" + str(dateTime.time().minute)
        return res
    else:
        res = ""
        res += str(dateTime.date().day) + " " + months[str(dateTime.date().month)] + " " + str(dateTime.date().year) + " в "
        res += str(dateTime.time().hour) + ":" + str(dateTime.time().minute)
        return res
    return res

@csrf_exempt
def articlesList(request, uuiId):
    favorites = []
    try:
        user = User.objects.get(login=uuiId)
        favorites = list(Favorites.objects.filter(user=user.id))
    except User.DoesNotExist:
        favorites = []
    articles=NewsArticles.objects.all()
    favIds = []
    for fav in favorites:
        favIds.append(fav.article.id)
    list1 = []
    try:
        tag = Tag.objects.get(important=1)
        new = []
        old = []
        for article in articles:
            if(article.creationTime.date() >= datetime.datetime.now().date() + timedelta(hours=3) - timedelta(days=2)):
                new.append(article)
            else:
                old.append(article)
        new1 = []
        new2 = []
        for article in new:
            if(article.tag.important):
                new1.append(article)
            else:
                new2.append(article)
        new1.reverse()
        new2.reverse()
        old.reverse()
        new = [*new1, *new2]
        list1 = [*new, *old]
    except Tag.DoesNotExist:
        list1 = [*list1, *articles]
        list1.reverse()

    res = []
    for article in list1:
        isFavorite = article.id in favIds
        res.append({
            'id': article.id,
            'title': article.title,
            'photoAuthor': article.photoAuthor,
            'content': articleBodyToJson(article),
            'creationTime': datetimeToString(article.creationTime),
            'tag': str(article.tag.title),
            'imageUrl': imageToJson(str(article.image.path)),
            'city': str(article.city.cityName),
            'isFavorite': isFavorite,
        })
    return JsonResponse(res, safe=False)
  
def articleBodyToJson(article):
    res = ""
    body = article.mainText
    parts = body.split("\& ")
    for part in parts:
        if len(res) > 0:
            res += "\n\n"
        #part = "    " + part
        res += part
    return res
  
@csrf_exempt
def articleById(request, articleId, uuiId):
    try:
        article = NewsArticles.objects.get(id=articleId)
        isFavorite = False
        try: 
            user = User.objects.get(login=uuiId)
            favorites = list(Favorites.objects.filter(user=user.id))
            for fav in favorites:
                if fav.article.id == article.id:
                    isFavorite = True
        except User.DoesNotExist:
            isFavorite = False
        res = {
                'id': article.id,
                'title': article.title,
                'photoAuthor': article.photoAuthor,
                'content': articleBodyToJson(article),
                'creationTime': datetimeToString(article.creationTime),
                'tag': str(article.tag.title),
                'imageUrl': imageToJson(str(article.image.path)),
                'city': str(article.city.cityName),
                'isFavorite': isFavorite,
            }
        return JsonResponse(res, safe=False)
    except NewsArticles.DoesNotExist:
        return
   
@csrf_exempt
def favoritesList(request, uuiId):
    res = []
    try:
        user = User.objects.get(login=uuiId)
        favorites = list(Favorites.objects.filter(user=user.id))
        for fav in favorites:
            res.append({
                'id': fav.article.id,
                'title': fav.article.title,
                'photoAuthor': fav.article.photoAuthor,
                'content': articleBodyToJson(fav.article),
                'creationTime': datetimeToString(fav.article.creationTime),
                'tag': str(fav.article.tag.title),
                'imageUrl': imageToJson(str(fav.article.image.path)),
                'city': str(fav.article.city.cityName),
                'isFavorite': True,
            })
        res.reverse()
        return JsonResponse(res, safe=False)
    except User.DoesNotExist:
        return JsonResponse(res, safe=False)
 
@csrf_exempt
def userMissingList(request, uuiId):
    res = []
    try:
        user = User.objects.get(login=uuiId)
        missing=list(MissingPeople.objects.filter(creator=user.id))
        for mis in missing:
            if(mis.status == "accepted" or mis.status == "moderating"):
                res.append({
                    'id': mis.id,
                    'name': mis.name,
                    'clothes': mis.clothes,
                    'specCharacteristics': mis.specCharacteristics,
                    'characteristics': mis.characteristics,
                    'lastLocation': mis.lastLocation,
                    'age': ageToString(mis.dateOfBirth),
                    'sex': mis.sex,
                    'telephone': mis.telephone,
                    'imageUrl': imageToJson(str(mis.image.path)),
                    'city': str(mis.city.cityName),
                    'status': mis.status,
                })
        res.reverse()
        return JsonResponse(res, safe=False)
    except User.DoesNotExist:
        return JsonResponse(res, safe=False)
 
@csrf_exempt
def filterArticlesList(request, tagId, uuiId):
    favorites = []
    try:
        user = User.objects.get(login=uuiId)
        favorites = list(Favorites.objects.filter(user=user.id))
    except User.DoesNotExist:
        favorites = []
    articles=list(NewsArticles.objects.filter(tag=tagId))
    favIds = []
    for fav in favorites:
        favIds.append(fav.article.id)
    res = []
    for article in articles:
        isFavorite = article.id in favIds
        res.append({
            'id': article.id,
            'title': article.title,
            'photoAuthor': article.photoAuthor,
            'content': articleBodyToJson(article),
            'creationTime': datetimeToString(article.creationTime),
            'tag': str(article.tag.title),
            'imageUrl': imageToJson(str(article.image.path)),
            'city': str(article.city.cityName),
            'isFavorite': isFavorite,
        })
    res.reverse()
    return JsonResponse(res, safe=False)
    
@csrf_exempt
def addFavorite(request, articleId, uuiId):
    status = 200
    try: 
        article = NewsArticles.objects.get(id=articleId)
        try:
            user = User.objects.get(login=uuiId)
            try: 
                fav = Favorites.objects.get(user=user.id, article=articleId)
                fav.delete()
            except Favorites.DoesNotExist:
                fav = Favorites()
                fav.user = user
                fav.article = article
                fav.save()
        except User.DoesNotExist:
            addUser(uuiId)
            user = User.objects.get(login=uuiId)
            fav = Favorites()
            fav.user = user
            fav.article = article
            fav.save()
    except NewsArticles.DoesNotExist:
        status = 406
    response = HttpResponse()
    response.status_code = status
    return response

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
                photoAuthor = request.POST.get("photoAuthor")

                name = image.name.split(".")
                fs = FileSystemStorage()
                dt_now = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
                imgname = sha1((dt_now + image.name).encode('utf-8')).hexdigest()
                filename = "static/images/articles/" + imgname + "." + name[-1]
                path = fs.save(filename, image)
                size = 1020, 800
                im = Image.open(filename)
                im.thumbnail(size, Image.ANTIALIAS)
                im.save(filename, "JPEG")
                resource = Resources()
                resource.path = filename
                resource.save()

                article = NewsArticles()
                article.title = title
                article.tag = Tag.objects.get(id=tag)
                article.image = Resources.objects.get(path=filename)
                article.mainText = text
                article.photoAuthor = photoAuthor
                cr_time = (datetime.datetime.now() + timedelta(hours=3)).isoformat(' ', 'seconds')
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
                        cr_time = datetime.datetime.now(tzinfo).isoformat(' ', 'seconds')
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
