from django.db import models

class Category(models.Model):
    name = models.CharField(max_length=64)
    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=100)                                 # Название (короткий текст)
    price = models.IntegerField()                                           # Цена (целое число)
    description = models.TextField()                                        # Описание (длинный текст)
    image = models.ImageField(upload_to='product/', blank=True, null=True)  # Картинка продука (aaaaaaaaaaa)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True) # Привязка товара к категории
    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товары"

    def __str__(self):
        return self.name  # Чтобы в админке писалось название, а не "Product object (1)"

class News(models.Model):
    title = models.CharField(max_length=200)    # Название (короткий текст)
    text = models.TextField()                   # Длинный текст, без ограничений

    class Meta:
        verbose_name = "Новость"
        verbose_name_plural = "Новости"
    def __str__(self):
        return self.title

class Order(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    user_id = models.BigIntegerField()
    time = models.DateTimeField(auto_now_add=True)
    address = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"
    def __str__(self):
        return self.product.name

class TelegramUser(models.Model):
    chat_id = models.BigIntegerField(unique=True) # Добавил unique=True (чтоб ID не дублировались)
    username = models.CharField(max_length=255, null=True, blank=True) # Увеличил длину до 255 и разрешил быть пустым (null=True)
    joined_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.chat_id} - {self.username}"
    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
class CartItem(models.Model):
    user = models.ForeignKey(TelegramUser, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.user.username} - {self.product.name}"
