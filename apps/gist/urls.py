from django.urls import path

from . import views

app_name = "gist"

app_name = "gist"
urlpatterns = [
    path("", views.scrape_page, name="scrape_page"),
]
