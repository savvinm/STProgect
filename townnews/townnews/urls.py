"""townnews URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.contrib.staticfiles.storage import staticfiles_storage
from webapp import views


urlpatterns = [
    path('acc/<int:id>', views.accept),
    path('rej/<int:id>', views.reject),
    path('addnews', views.addnews),
    path('newadverts', views.newadverts),
    path('addpromo', views.addpromo),
    path('login', views.login),
    path('cleaner', views.clearPriority),
    path('tagslist', views.tagsList),
    path('favoriteslist/<str:uuiId>', views.favoritesList),
    path('usermissinglist/<str:uuiId>', views.userMissingList),
    path('getimage/<str:imagePath>', views.getImage),
    path('articleslist/<int:tagId>/<str:uuiId>', views.filterArticlesList),
    path('promoslist', views.promosList),
    path('deletemissing/<int:id>/<str:uuiId>', views.deleteMissing),
    path('articleslist/<str:uuiId>', views.articlesList),
    path('addfavorite/<int:articleId>/<str:uuiId>', views.addFavorite),
    path('getarticle/<int:articleId>/<str:uuiId>', views.articleById),
    path('article/<int:articleId>', views.openArticle),
    path('missinglist', views.missingList),
    path('addmissing', views.addMissing),
    path('deferred/a/<int:articleId>', views.deferredArticle),
    path('openapp', views.openApp),
    path('appinit/<str:iOSVersion>/<str:uuiId>', views.appInit),
    path('', views.index),
]
