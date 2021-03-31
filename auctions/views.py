import datetime

from django import forms
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from .models import Listing, User, Category, Bid, Watchlist

# pylint: disable=no-member

class ListingForm(forms.Form):
    title = forms.CharField(label='', required=True, widget=forms.TextInput(attrs={'placeholder': 'Title'}))
    description = forms.CharField(label='', widget=forms.Textarea(attrs={'placeholder': 'Description (450 character maximum)'}))
    price = forms.DecimalField(label='PRICE', required=True, widget=forms.TextInput(attrs={'placeholder': 'Price in EUR'}))
    image = forms.ImageField()
    choice = forms.ChoiceField(choices = [])

    #To take Category by Model
    def __init__(self, *args, **kwargs):
        super(ListingForm, self).__init__(*args, **kwargs)
        self.fields['choice'].choices = [(x.pk, x.name) for x in Category.objects.all()]

class Bids(forms.Form):
    bid = forms.DecimalField(label='',required=False, widget=forms.TextInput(attrs={'placeholder': 'Place a bid'}))

class Button(forms.Form):
    btn = forms.CharField

def index(request):
    return render(request, "auctions/index.html", {
            "items": Listing.objects.exclude(on_sell=False)
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

    if not user.is_authenticated:
        return render(request, "auctions/item.html", {
            "item": Listing.objects.get(id=item_id),
            "logged": False
        })
    
    #IF USER IS AUTENTICATED
    else:
        item = Listing.objects.get(pk=item_id)
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
                    "present": present
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
                        "present": present
                    })
                            
            else:
                if user != item.owner:
                    return render(request, "auctions/item.html", {
                        "logged": True,
                        "item": Listing.objects.get(id=item_id),
                        "bid_form": Bids,
                        "bid.amount": 0,
                        "owner": False,
                        "present": present
                    })
                else:
                    return render(request, "auctions/item.html", {
                        "logged": True,
                        "item": Listing.objects.get(id=item_id),
                        "bid.amount": 0,
                        "owner": True,
                        "present": present
                    })

def add(request, item_id):
    if request.method == "GET":
        item = Listing.objects.get(pk=item_id)
        owner = User.objects.get(username=request.user.get_username())
        if Watchlist.objects.filter(item_id=item_id):
            return render(request, "auctions/watchlist.html", {
            "item": item,
            "all": False,
            "message": item.title + " was already added! "
        })
        
        else:
            new_item = Watchlist.objects.create(
                item = item,
                user = owner
            )
            new_item.save()
            return HttpResponseRedirect(reverse("details", args=(item.id,)))

def watchlist(request):
    if request.method == "GET":
        items = Watchlist.objects.filter(user = request.user)
        return render(request, "auctions/watchlist.html", {
            "items": items
        }) 

def remove(request, item_id):
    if request.method == "GET":
        item = Listing.objects.get(pk=item_id)
        removed = Watchlist.objects.get(item=item).delete()
        return HttpResponseRedirect(reverse("details", args=(item.id,)))

def sell(request, item_id):
    if request.method == "GET":
        item = Listing.objects.get(pk=item_id)
        item.on_sell=False
        item.save(update_fields=['on_sell'])
        return HttpResponseRedirect(reverse("details", args=(item.id,)))