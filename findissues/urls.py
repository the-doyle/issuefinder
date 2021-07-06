from django.urls import path
from .views import about, index, results, document

urlpatterns = [
    path("", index, name='index'),
    path("results/", results, name='results'),
    path("about/", about, name='about'),
    path("document/<name>#page=<page>", document, name='document'),
]