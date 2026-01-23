from django.contrib import admin
from shop.models import Product, Order, News, TelegramUser, Category  # Импортируем наш класс

# Говорим админке: "Управляй этой таблицей"
admin.site.register(News)
admin.site.register(TelegramUser)
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'price', 'category')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    # Добавляем список полей, которые будут видны в таблице
    list_display = ('id', 'product', 'user_id', 'time', 'address')
    list_filter = ('time',)
    search_fields = ('user_id', 'address')
