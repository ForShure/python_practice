from django.contrib import admin
from .models import Product, News, Order, TelegramUser   # Импортируем наш класс

# Говорим админке: "Управляй этой таблицей"
admin.site.register(Product)
admin.site.register(News)
admin.site.register(TelegramUser)
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_filter = ('time',)
    search_fields = ('user_id',)