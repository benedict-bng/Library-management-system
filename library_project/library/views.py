from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import render
from .models import User
from .models import Book, Transaction
from .serializers import BookSerializer, UserSerializer, TransactionSerializer
from django.shortcuts import get_object_or_404

# Home view (for browser display)
def home(request):
    return render(request, 'home.html', {"message": "Welcome to the Library Management System API"})

# ViewSet for Books
class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer

# ViewSet for Users
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

# Checkout a book
class CheckoutAPIView(APIView):
    def post(self, request, book_id):
        book = get_object_or_404(Book, id=book_id)
        user = request.user

        if not book.available:
            return Response({"message": "Book is not available."}, status=status.HTTP_400_BAD_REQUEST)

        # Mark book as checked out
        book.available = False
        book.save()

        # Create transaction
        Transaction.objects.create(user=user, book=book, status='checked_out')

        return Response({"message": f"Book '{book.title}' checked out successfully."}, status=status.HTTP_200_OK)

# Return a book
class ReturnAPIView(APIView):
    def post(self, request, book_id):
        book = get_object_or_404(Book, id=book_id)
        user = request.user

        # Find transaction
        transaction = Transaction.objects.filter(user=user, book=book, status='checked_out').first()
        if not transaction:
            return Response({"message": "No active checkout found for this book."}, status=status.HTTP_400_BAD_REQUEST)

        # Mark book as available
        book.available = True
        book.save()

        # Update transaction
        transaction.status = 'returned'
        transaction.save()

        return Response({"message": f"Book '{book.title}' returned successfully."}, status=status.HTTP_200_OK)

# View user transactions
class UserTransactionsListView(APIView):
    def get(self, request):
        user = request.user
        transactions = Transaction.objects.filter(user=user)
        serializer = TransactionSerializer(transactions, many=True)
        return Response(serializer.data)
