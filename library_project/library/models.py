from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.core.exceptions import ValidationError


class User(AbstractUser):
    email = models.EmailField('email address', unique=True)
    date_of_membership = models.DateField(default=timezone.now)

    # Use built-in is_active, is_staff, is_superuser for roles
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
            raise ValidationError("Copies available cannot be negative")

    def decrease_copies(self):
        """Reduce available copies by one when checked out."""
        if self.copies_available <= 0:
            raise ValidationError("No available copies to check out.")
        self.copies_available -= 1
        self.save()

    def increase_copies(self):
        """Increase available copies by one when returned."""
        self.copies_available += 1
        self.save()


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
        ordering = ['-checked_out_at']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'book', 'status'],
                name='unique_active_checkout'
            )
        ]

    def __str__(self):
        return f"{self.user.username} - {self.book.title} ({self.get_status_display()})"

    def mark_returned(self):
        """Mark transaction as returned and update book copies."""
        if self.status == self.RETURNED:
            raise ValidationError("Book is already returned.")
        self.status = self.RETURNED
        self.returned_at = timezone.now()
        self.book.increase_copies()
        self.save()
