from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    home,
    BookViewSet,
    UserViewSet,
    CheckoutAPIView,
    ReturnAPIView,
    UserTransactionsListView
)

router = DefaultRouter()
router.register(r'books', BookViewSet, basename='book')
router.register(r'users', UserViewSet, basename='user')

urlpatterns = [
    path('', home, name='home'),
    path('', include(router.urls)),
    path('books/<int:book_id>/checkout/', CheckoutAPIView.as_view(), name='book-checkout'),
    path('books/<int:book_id>/return/', ReturnAPIView.as_view(), name='book-return'),
    path('transactions/', UserTransactionsListView.as_view(), name='user-transactions'),
]
