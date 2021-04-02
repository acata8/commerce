import datetime

from django import forms
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from .models import Listing, User, Category, Bid, Watchlist, Comment

# pylint: disable=no-member

class ListingForm(forms.Form):
    title = forms.CharField(label='', required=True, widget=forms.TextInput(attrs={'placeholder': 'Title'}))
    description = forms.CharField(label='', max_length=450, widget=forms.Textarea(attrs={'placeholder': 'Description (450 character maximum)', 'maxlenght':'450', 'cols':'32'}))
    price = forms.DecimalField(label='PRICE', required=True, widget=forms.TextInput(attrs={'placeholder': 'Price in EUR'}))
    image = forms.ImageField()
    choice = forms.ChoiceField(choices = [])

    #To take Category by Model
    def __init__(self, *args, **kwargs):
        super(ListingForm, self).__init__(*args, **kwargs)
        self.fields['choice'].choices = [(x.pk, x.name) for x in Category.objects.all()]

class Bids(forms.Form):
    bid = forms.DecimalField(label='',required=False, widget=forms.TextInput(attrs={'placeholder': 'Place a bid'}))

class CommentForm(forms.Form):
    comment = forms.CharField(label='', required=False, max_length=250, widget=forms.Textarea(attrs={'placeholder': 'Leave a comment (250 character maximum)', 'rows':'15', 'cols':'32','maxlenght':250}))

def index(request):
    return render(request, "auctions/index.html", {
            "items": Listing.objects.exclude(on_sell=False),
            "all": False
        })

def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]

        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })
        
        if request.POST["password"] == "" :
             return render(request, "auctions/register.html", {
                "message": "You need a password."
        })
        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", { 
                "message": "Username already taken."
            })            
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")


@login_required
def create(request):
    if request.method == "POST":
        requestForm = ListingForm(request.POST, request.FILES)
        if requestForm.is_valid():
            title = requestForm.cleaned_data.get("title")
            description = requestForm.cleaned_data.get("description")
            price = requestForm.cleaned_data.get("price")
            image = requestForm.cleaned_data.get("image")
            id_category = requestForm.cleaned_data.get("choice")
            item = Listing.objects.create(
                                 title = title,
                                 description = description,
                                 price = price,
                                 image = image,
                                 category = Category.objects.get(id=id_category),
                                 owner = User.objects.get(username=request.user.get_username()),
                                 date=datetime.datetime.now()
                                 )
            item.save()
            return HttpResponseRedirect(reverse("index"))
    else: 
        return render(request, "auctions/create.html", {
            "form": ListingForm()
        })


def details(request, item_id):
    user = request.user
    item = Listing.objects.get(pk=item_id)
    if not user.is_authenticated:
        return render(request, "auctions/item.html", {
            "item": Listing.objects.get(id=item_id),
            "logged": False,
            "comments": Comment.objects.filter(item_id=item_id),
            "bid": Bid.objects.filter(item = item).last(),
        })
    
    #IF USER IS AUTENTICATED
    else:
        
        form = Bids(request.POST)

        if Watchlist.objects.filter(user=user).filter(item=item).exists():
            present = True
        else:
            present = False

        context = { "logged": True,
                    "item": Listing.objects.get(pk = item_id),
                    "bid_form": Bids,
                    "bid": Bid.objects.filter(item = item).last(),
                    "owner": False,
                    "present": present,
                    "comment_form": CommentForm(),
                    "comments": Comment.objects.filter(item_id=item_id)
                    }
        
        if request.method == "POST" and form.is_valid():
            offer = form.cleaned_data.get('bid')
            if item.actual_bid < offer and item.price < offer:
                    new_bid = Bid.objects.create(
                        amount= offer,
                        buyer = request.user,
                        item = item
                    )
                    new_bid.save()
                    item.actual_bid = offer
                    item.save()
                    return HttpResponseRedirect(reverse("details", args=(item.id,)))               
            else:
                    return render(request, "auctions/item.html",
                    { 
                    "message": str(offer) + " € ISN'T ENOUGH!",
                    "logged": True,
                    "item": Listing.objects.get(pk = item_id),
                    "bid_form": Bids,
                    "bid": Bid.objects.filter(item = item).last(),
                    "present": present
                    })
            #METHOD GET
        else:
            
            if item.actual_bid != 0.0:
                if user != item.owner:
                    return render(request, "auctions/item.html", context)
                else:
                    return render(request, "auctions/item.html", {
                       "logged": True,
                        "item": Listing.objects.get(pk = item_id),
                        "bid": Bid.objects.filter(item = item).last(),
                        "owner": True,
                        "present": present,
                        "comment_form": CommentForm(),
                        "comments": Comment.objects.filter(item_id=item_id)
                    })
                            
            else:
                if user != item.owner:
                    return render(request, "auctions/item.html", {
                        "logged": True,
                        "item": Listing.objects.get(id=item_id),
                        "bid_form": Bids,
                        "bid.amount": 0,
                        "owner": False,
                        "present": present,
                        "comment_form": CommentForm(),
                        "comments": Comment.objects.filter(item_id=item_id)
                    })
                else:
                    return render(request, "auctions/item.html", {
                        "logged": True,
                        "item": Listing.objects.get(id=item_id),
                        "bid.amount": 0,
                        "owner": True,
                        "present": present,
                        "comment_form": CommentForm(),
                        "comments": Comment.objects.filter(item_id=item_id)
                    })

@login_required
def add(request, item_id):
    if request.method == "GET":
        item = Listing.objects.get(pk=item_id)
        owner = User.objects.get(username=request.user.get_username())
        new_item = Watchlist.objects.create(
                item = item,
                user = owner
            )
        new_item.save()
        return HttpResponseRedirect(reverse("details", args=(item.id,)))

@login_required
def watchlist(request):
    if request.method == "GET":
        items = Watchlist.objects.filter(user = request.user)
        return render(request, "auctions/watchlist.html", {
            "items": items
        }) 

@login_required
def remove(request, item_id):
    if request.method == "GET":
        item = Listing.objects.get(pk=item_id)
        removed = Watchlist.objects.filter(item=item).delete()
        return HttpResponseRedirect(reverse("details", args=(item.id,)))

@login_required
def sell(request, item_id):
    if request.method == "GET":
        item = Listing.objects.get(pk=item_id)
        item.on_sell=False
        item.save(update_fields=['on_sell'])
        return HttpResponseRedirect(reverse("details", args=(item.id,)))


def all(request):
    if request.method == "GET":
        return render(request, "auctions/index.html", {
            "items": Listing.objects.all(),
            "all": True
        })


def add_comment(request, item_id):
    form = CommentForm(request.POST)
    if request.method == "POST" and form.is_valid():
        new_comment = Comment.objects.create(
            description= form.cleaned_data.get('comment'),
            date = datetime.datetime.now(),
            user = request.user,
            item = Listing.objects.get(pk=item_id)
        )
        new_comment.save()
        return HttpResponseRedirect(reverse("details", args=(item_id,)))
        
def category(request):
    if request.method == "GET":
        return render(request, "auctions/category.html",{
            "categories": Category.objects.all(),
            "all": True
        })


def search(request, category_id):
    if request.method == "GET":
        return render(request, "auctions/category.html",{
            "item": Category.objects.all().filter(pk=category_id).first(),
            "categories": Listing.objects.filter(category=category_id).exclude(on_sell=False),
            "all": False
        }) 
   
