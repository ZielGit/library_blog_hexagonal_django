"""URL Routing del módulo Library API"""
from django.urls import path
from .views import AuthorListCreateView, BookListCreateView, LoanCreateView, LoanReturnView, MyLoansView

urlpatterns = [
    path("authors/", AuthorListCreateView.as_view(), name="author-list-create"),
    path("books/", BookListCreateView.as_view(), name="book-list-create"),
    path("loans/", LoanCreateView.as_view(), name="loan-create"),
    path("loans/<uuid:loan_id>/return/", LoanReturnView.as_view(), name="loan-return"),
    path("my-loans/", MyLoansView.as_view(), name="my-loans"),
]
