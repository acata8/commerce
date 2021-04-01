from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
    path("create", views.create, name="create"),
    path("all", views.all, name="all"),
    path("listing/<str:item_id>", views.details, name="details"),
    path("watchlist/add/<str:item_id>", views.add, name="add"),
    path("watchlist/remove/<str:item_id>", views.remove, name="remove"),
    path("watchlist/", views.watchlist, name="watchlist"),
    path("listing/sell/<str:item_id>", views.sell, name="sell"),
    path("listing/comment/<str:item_id>", views.add_comment, name="add_comment"),
    path("category", views.category, name="category"),
    path("category/<str:category_id>", views.search, name="searchCategory")
]
