from django.shortcuts import render
from rest_framework import viewsets, status, permissions, filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from django.db import transaction as db_transaction
from django.shortcuts import get_object_or_404
from .models import Book, Transaction, User
from .serializers import BookSerializer, TransactionSerializer, UserSerializer
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from django.http import HttpResponse

def home(request):
    return HttpResponse("Welcome to the Library API")

class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_staff


class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all().order_by('title')
    serializer_class = BookSerializer
    permission_classes = (IsAdminOrReadOnly,)
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    filterset_fields = ['copies_available']
    search_fields = ['title', 'author', 'isbn']

    def get_queryset(self):
        qs = super().get_queryset()
        available = self.request.query_params.get('available')
        if available is not None:
            if available.lower() in ('1', 'true', 'yes'):
                qs = qs.filter(copies_available__gt=0)
        return qs


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('date_of_membership')
    serializer_class = UserSerializer
    permission_classes = (IsAdminOrReadOnly,)
    filter_backends = (filters.SearchFilter,)
    search_fields = ['username', 'email']

    def get_permissions(self):
        # Allow users to retrieve/update their own profiles
        if self.action in ['retrieve', 'update', 'partial_update']:
            if self.request.user.is_authenticated and (self.request.user.is_staff or self.request.user.pk == int(self.kwargs.get('pk', 0) or 0)):
                return [permissions.IsAuthenticated()]
        return super().get_permissions()


# Checkout endpoint
from rest_framework.views import APIView

class CheckoutAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    @db_transaction.atomic
    def post(self, request, book_id):
        user = request.user
        book = get_object_or_404(Book, pk=book_id)

        # Check availability
        if book.copies_available <= 0:
            return Response({'detail': 'No copies available.'}, status=status.HTTP_400_BAD_REQUEST)

        # Check if user already has this book checked out
        existing = Transaction.objects.filter(user=user, book=book, status=Transaction.CHECKED_OUT).exists()
        if existing:
            return Response({'detail': 'You already have this book checked out.'}, status=status.HTTP_400_BAD_REQUEST)

        # Create transaction and decrement copies
        book.copies_available -= 1
        if book.copies_available < 0:
            return Response({'detail': 'No copies left.'}, status=status.HTTP_400_BAD_REQUEST)
        book.save()

        tx = Transaction.objects.create(user=user, book=book, status=Transaction.CHECKED_OUT)
        serializer = TransactionSerializer(tx)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ReturnAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    @db_transaction.atomic
    def post(self, request, book_id):
        user = request.user
        book = get_object_or_404(Book, pk=book_id)

        # Find active transaction
        try:
            tx = Transaction.objects.get(user=user, book=book, status=Transaction.CHECKED_OUT)
        except Transaction.DoesNotExist:
            return Response({'detail': 'No active checkout of this book found for this user.'}, status=status.HTTP_400_BAD_REQUEST)

        # Mark returned
        tx.status = Transaction.RETURNED
        tx.returned_at = timezone.now()
        tx.save()

        # Increase copies
        book.copies_available += 1
        book.save()

        serializer = TransactionSerializer(tx)
        return Response(serializer.data, status=status.HTTP_200_OK)


# Optional: A view to list a user's borrowing history
from rest_framework.generics import ListAPIView
class UserTransactionsListView(ListAPIView):
    serializer_class = TransactionSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        # Use the requesting user's id, or allow admin to view others via query param
        user = self.request.user
        user_id = self.request.query_params.get('user_id')
        if user.is_staff and user_id:
            return Transaction.objects.filter(user_id=user_id).order_by('-checked_out_at')
        return Transaction.objects.filter(user=user).order_by('-checked_out_at')

