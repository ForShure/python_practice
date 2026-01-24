from django.contrib import admin
from shop.models import Product, Order, News, TelegramUser, Category, OrderItem

admin.site.register(News)
admin.site.register(TelegramUser)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'price', 'category')

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_id', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    inlines = [OrderItemInline]