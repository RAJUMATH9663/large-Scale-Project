from django.contrib import admin
from .models import Vendor, Product, Cart, Order

class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'vendor')
    list_filter = ('vendor',)

class OrderAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'quantity', 'ordered_at')
    list_filter = ('ordered_at', 'user')

admin.site.register(Vendor)
admin.site.register(Product, ProductAdmin)
admin.site.register(Cart)
admin.site.register(Order, OrderAdmin)
