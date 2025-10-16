from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.core.exceptions import ValidationError

class User(AbstractUser):
    email = models.EmailField('email address', unique=True)
    date_of_membership = models.DateField(default=timezone.now)
    # is_active already exists on AbstractUser
    # You can add roles later (is_staff/is_superuser as admin)

    def __str__(self):
        return f"{self.username} ({self.email})"


class Book(models.Model):
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    isbn = models.CharField(max_length=13, unique=True)
    published_date = models.DateField(null=True, blank=True)
    copies_available = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.title} by {self.author} ({self.isbn})"

    def clean(self):
        if self.copies_available < 0:
            raise ValidationError("copies_available cannot be negative")


class Transaction(models.Model):
    CHECKED_OUT = 'OUT'
    RETURNED = 'IN'

    STATUS_CHOICES = [
        (CHECKED_OUT, 'Checked Out'),
        (RETURNED, 'Returned'),
    ]

    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='transactions')
    book = models.ForeignKey('Book', on_delete=models.CASCADE, related_name='transactions')
    status = models.CharField(max_length=3, choices=STATUS_CHOICES, default=CHECKED_OUT)
    checked_out_at = models.DateTimeField(default=timezone.now)
    returned_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('user', 'book', 'status')  # prevent duplicate active checkout of same book by same user

    def __str__(self):
        return f"{self.user.username} - {self.book.title} -> {self.status}"
