"""VISTAS API para Library"""
from uuid import UUID
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny

from src.domain.shared.base import DomainError, NotFoundError
from config.container import (
    get_create_author_handler, get_create_book_handler, get_checkout_book_handler,
    get_return_book_handler, get_list_authors_handler, get_list_available_books_handler,
    get_list_user_loans_handler,
)
from src.application.library.commands.author_commands import CreateAuthorCommand
from src.application.library.commands.book_commands import CreateBookCommand
from src.application.library.commands.loan_commands import CheckoutBookCommand, ReturnBookCommand
from src.application.library.queries.library_queries import ListAuthorsQuery, ListAvailableBooksQuery, ListUserLoansQuery
from .swagger_schemas import create_author_schema, list_authors_schema, create_book_schema, list_books_schema, checkout_book_schema, return_book_schema, my_loans_schema


def handle_error(exc):
    if isinstance(exc, NotFoundError):
        return Response({"error": str(exc)}, status=status.HTTP_404_NOT_FOUND)
    if isinstance(exc, DomainError):
        return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
    raise exc


class AuthorListCreateView(APIView):
    permission_classes = [AllowAny]
    
    @list_authors_schema
    def get(self, request):
        query = ListAuthorsQuery(page=int(request.query_params.get("page", 1)), page_size=int(request.query_params.get("page_size", 20)))
        authors = get_list_authors_handler().handle(query)
        return Response([{"id": str(a.id), "name": a.name, "biography": a.biography, "birth_year": a.birth_year, "books_count": a.books_count} for a in authors])
    
    @create_author_schema
    def post(self, request):
        try:
            command = CreateAuthorCommand(name=request.data.get("name", ""), biography=request.data.get("biography", ""), birth_year=request.data.get("birth_year"))
            result = get_create_author_handler().handle(command)
            return Response({"id": str(result.id), "name": result.name}, status=status.HTTP_201_CREATED)
        except DomainError as e:
            return handle_error(e)


class BookListCreateView(APIView):
    from src.infrastructure.auth.drf_jwt_authentication import JWTAuthentication as JWTAuth
    authentication_classes = [JWTAuth]
    
    def get_permissions(self):
        return [IsAuthenticated()] if self.request.method == "POST" else [AllowAny()]
    
    @list_books_schema
    def get(self, request):
        query = ListAvailableBooksQuery(page=int(request.query_params.get("page", 1)), page_size=int(request.query_params.get("page_size", 20)))
        books = get_list_available_books_handler().handle(query)
        return Response([{"id": str(b.id), "isbn": b.isbn, "title": b.title, "author_id": str(b.author_id), "author_name": b.author_name, "total_copies": b.total_copies, "available_copies": b.available_copies, "published_year": b.published_year} for b in books])
    
    @create_book_schema
    def post(self, request):
        try:
            command = CreateBookCommand(isbn=request.data.get("isbn", ""), title=request.data.get("title", ""), author_id=UUID(str(request.data.get("author_id"))), description=request.data.get("description", ""), total_copies=int(request.data.get("total_copies", 1)), published_year=request.data.get("published_year"))
            result = get_create_book_handler().handle(command)
            return Response({"id": str(result.id), "isbn": result.isbn, "title": result.title, "author_name": result.author_name}, status=status.HTTP_201_CREATED)
        except (DomainError, NotFoundError) as e:
            return handle_error(e)


class LoanCreateView(APIView):
    from src.infrastructure.auth.drf_jwt_authentication import JWTAuthentication as JWTAuth
    authentication_classes = [JWTAuth]
    permission_classes = [IsAuthenticated]
    
    @checkout_book_schema
    def post(self, request):
        try:
            command = CheckoutBookCommand(book_id=UUID(str(request.data.get("book_id"))), user_id=request.user.id, due_days=int(request.data.get("due_days", 14)))
            result = get_checkout_book_handler().handle(command)
            return Response({"id": str(result.id), "book_id": str(result.book_id), "user_id": str(result.user_id), "checkout_date": result.checkout_date.isoformat(), "due_date": result.due_date.isoformat(), "status": result.status}, status=status.HTTP_201_CREATED)
        except (DomainError, NotFoundError) as e:
            return handle_error(e)


class LoanReturnView(APIView):
    from src.infrastructure.auth.drf_jwt_authentication import JWTAuthentication as JWTAuth
    authentication_classes = [JWTAuth]
    permission_classes = [IsAuthenticated]
    
    @return_book_schema
    def post(self, request, loan_id):
        try:
            get_return_book_handler().handle(ReturnBookCommand(loan_id=loan_id))
            return Response({"message": "Libro devuelto exitosamente"})
        except (DomainError, NotFoundError) as e:
            return handle_error(e)


class MyLoansView(APIView):
    from src.infrastructure.auth.drf_jwt_authentication import JWTAuthentication as JWTAuth
    authentication_classes = [JWTAuth]
    permission_classes = [IsAuthenticated]
    
    @my_loans_schema
    def get(self, request):
        loans = get_list_user_loans_handler().handle(ListUserLoansQuery(user_id=request.user.id))
        return Response([{"id": str(l.id), "book_id": str(l.book_id), "book_title": l.book_title, "user_id": str(l.user_id), "checkout_date": l.checkout_date.isoformat(), "due_date": l.due_date.isoformat(), "return_date": l.return_date.isoformat() if l.return_date else None, "status": l.status, "is_overdue": l.is_overdue} for l in loans])
