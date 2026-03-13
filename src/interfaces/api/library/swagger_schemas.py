"""Schemas de drf-spectacular para Library API"""
from drf_spectacular.utils import extend_schema, OpenApiExample
from rest_framework import serializers


class CreateAuthorRequestSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=200)
    biography = serializers.CharField(required=False, allow_blank=True)
    birth_year = serializers.IntegerField(required=False, allow_null=True)


class AuthorResponseSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField()
    biography = serializers.CharField()
    birth_year = serializers.IntegerField(allow_null=True)
    books_count = serializers.IntegerField()


class CreateBookRequestSerializer(serializers.Serializer):
    isbn = serializers.CharField(max_length=13)
    title = serializers.CharField(max_length=300)
    author_id = serializers.UUIDField()
    description = serializers.CharField(required=False, allow_blank=True)
    total_copies = serializers.IntegerField(default=1, min_value=1)
    published_year = serializers.IntegerField(required=False, allow_null=True)


class BookSummarySerializer(serializers.Serializer):
    id = serializers.UUIDField()
    isbn = serializers.CharField()
    title = serializers.CharField()
    author_id = serializers.UUIDField()
    author_name = serializers.CharField()
    total_copies = serializers.IntegerField()
    available_copies = serializers.IntegerField()
    published_year = serializers.IntegerField(allow_null=True)


class CheckoutBookRequestSerializer(serializers.Serializer):
    book_id = serializers.UUIDField()
    due_days = serializers.IntegerField(default=14, min_value=1, max_value=90)


class LoanResponseSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    book_id = serializers.UUIDField()
    book_title = serializers.CharField()
    user_id = serializers.UUIDField()
    checkout_date = serializers.DateTimeField()
    due_date = serializers.DateTimeField()
    return_date = serializers.DateTimeField(allow_null=True)
    status = serializers.CharField()
    is_overdue = serializers.BooleanField()


create_author_schema = extend_schema(
    summary="Crear autor",
    request=CreateAuthorRequestSerializer,
    responses={201: AuthorResponseSerializer},
    tags=["Library - Authors"],
)

list_authors_schema = extend_schema(
    summary="Listar autores",
    responses={200: AuthorResponseSerializer(many=True)},
    tags=["Library - Authors"],
)

create_book_schema = extend_schema(
    summary="Crear libro",
    request=CreateBookRequestSerializer,
    responses={201: BookSummarySerializer},
    tags=["Library - Books"],
)

list_books_schema = extend_schema(
    summary="Listar libros disponibles",
    responses={200: BookSummarySerializer(many=True)},
    tags=["Library - Books"],
)

checkout_book_schema = extend_schema(
    summary="Solicitar préstamo",
    request=CheckoutBookRequestSerializer,
    responses={201: LoanResponseSerializer},
    tags=["Library - Loans"],
)

return_book_schema = extend_schema(
    summary="Devolver libro",
    responses={200: {"description": "OK"}},
    tags=["Library - Loans"],
)

my_loans_schema = extend_schema(
    summary="Mis préstamos",
    responses={200: LoanResponseSerializer(many=True)},
    tags=["Library - Loans"],
)
