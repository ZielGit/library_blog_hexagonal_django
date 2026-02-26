"""
URL Routing del módulo Blog API.
"""
from django.urls import path
from .views import (
    PostListCreateView,
    PostDetailView,
    PostPublishView,
    PostArchiveView,
    CommentCreateView,
    AuthorPostsView,
)

urlpatterns = [
    # Posts
    path("posts/", PostListCreateView.as_view(), name="post-list-create"),
    path("posts/<slug:slug>/", PostDetailView.as_view(), name="post-detail"),
    path("posts/<uuid:post_id>/publish/", PostPublishView.as_view(), name="post-publish"),
    path("posts/<uuid:post_id>/archive/", PostArchiveView.as_view(), name="post-archive"),
    path("posts/<uuid:post_id>/comments/", CommentCreateView.as_view(), name="comment-create"),

    # Authors
    path("authors/<uuid:author_id>/posts/", AuthorPostsView.as_view(), name="author-posts"),
]
