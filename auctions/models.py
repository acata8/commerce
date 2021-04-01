from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    pass

class Category(models.Model):
    name = models.CharField(max_length=25, blank=True)

    def __str__(self):
        return f"{self.name}"

    class Meta:
        ordering = ['name']

class Listing(models.Model):
    title = models.CharField(max_length=64)
    description = models.TextField(max_length=450)
    price = models.DecimalField(max_digits=5, decimal_places=2)
    image = models.ImageField(upload_to='items')
    date = models.DateTimeField()
    actual_bid = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    on_sell = models.BooleanField(default=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, default=None, related_name="owner")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, default=None, related_name="category")
    
    
    def __str__(self):
        return f"{self.pk}| {self.title}, {self.owner}, {self.category}, {self.date}, on sell={self.on_sell}, {self.price} and bid {self.actual_bid}"

    class Meta:
        ordering = ['-date']
    
class Bid(models.Model):
    amount = models.DecimalField(max_digits=5, decimal_places=2)
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, default=None, related_name="buyer")
    item = models.ForeignKey(Listing, on_delete=models.CASCADE, default=None, related_name="item_tobuy")

    def __str__(self):
        return f"{self.buyer}, {self.amount}, ({self.item})"


class Comment(models.Model):
    description = models.TextField(max_length=250)
    date = models.DateTimeField()
    user = models.ForeignKey(User, on_delete=models.CASCADE, default=None, related_name="commentator")
    item = models.ForeignKey(Listing, on_delete=models.CASCADE, default=None, related_name="item")

    def __str__(self):
        return f"{self.user}, {self.item}, {self.description}"

    class Meta:
        ordering = ['-date']


class Watchlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, default=None, related_name="ownerList")
    item = models.ForeignKey(Listing, on_delete=models.CASCADE, default=None, related_name="itemList")