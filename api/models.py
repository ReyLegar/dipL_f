from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    phone_number = models.CharField(max_length=20)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    patronymic = models.CharField(max_length=50)
    balance = models.DecimalField(max_digits=10, decimal_places=2)
    document_image = models.ImageField(upload_to='document_images/')
    password = models.CharField(max_length=128)
    is_admin = models.BooleanField(default=False)

    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name='customuser_set',
        related_query_name='customuser',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='customuser_set',
        related_query_name='customuser',
    )
    personal_code = models.CharField(max_length=50)

class Credit(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_dates = models.TextField()
    image = models.ImageField(upload_to='credit_images/')
    #monthly_payment = models.DecimalField(max_digits=10, decimal_places=2)

class CreditApplication(models.Model):
    PENDING = 'Ожидает'
    APPROVED = 'Одобрена'
    REJECTED = 'Отклонена'
    STATUS_CHOICES = [
        (PENDING, 'Ожидает рассмотрения'),
        (APPROVED, 'Одобрена'),
        (REJECTED, 'Отклонена'),
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    application_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=9, choices=STATUS_CHOICES, default=PENDING)
    call_made = models.BooleanField(default=False)





