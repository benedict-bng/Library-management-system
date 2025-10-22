from rest_framework import serializers
from .models import Book, Transaction, User


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'email',
            'password',
            'date_of_membership',
            'is_active',
            'is_staff',
        )
        read_only_fields = ('id', 'date_of_membership')

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = (
            'id',
            'title',
            'author',
            'isbn',
            'published_date',
            'copies_available',
        )
        read_only_fields = ('id',)

    def validate_isbn(self, value):
        """Ensure ISBN is 10 or 13 characters."""
        if len(value) not in (10, 13):
            raise serializers.ValidationError("ISBN must be 10 or 13 characters long.")
        return value


class TransactionSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    book = serializers.PrimaryKeyRelatedField(queryset=Book.objects.all())
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Transaction
        fields = (
            'id',
            'user',
            'book',
            'status',
            'status_display',
            'checked_out_at',
            'returned_at',
        )
        read_only_fields = ('checked_out_at', 'returned_at', 'status_display')
