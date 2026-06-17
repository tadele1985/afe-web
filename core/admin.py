from django.contrib import admin

from .models import Item, ItemInventory, Location, Sector, AfeUser, UserGroup

admin.site.register([Sector, AfeUser, UserGroup, Item, ItemInventory, Location])
