# library/serializers.py
from rest_framework import serializers
from .models import Book, Transaction, User
from django.utils import timezone

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password', 'date_of_membership', 'is_active', 'is_staff')

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, val in validated_data.items():
            setattr(instance, attr, val)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ('id', 'title', 'author', 'isbn', 'published_date', 'copies_available')
        read_only_fields = ('id',)

    def validate_isbn(self, value):
        if len(value) not in (10, 13):
            # allow 10 or 13 char ISBNs; you can make strict validation here
            pass
        return value


class TransactionSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    book = serializers.PrimaryKeyRelatedField(queryset=Book.objects.all())

    class Meta:
        model = Transaction
        fields = ('id', 'user', 'book', 'status', 'checked_out_at', 'returned_at')
        read_only_fields = ('checked_out_at', 'returned_at', 'status')

