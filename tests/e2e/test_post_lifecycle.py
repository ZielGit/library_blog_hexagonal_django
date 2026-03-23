"""E2E tests para el ciclo de vida completo de un Post"""
import pytest
from rest_framework.test import APIClient
from django.test import TestCase


@pytest.mark.e2e
class TestPostLifecycleE2E(TestCase):
    """Test del flujo completo: register → login → create → publish → list"""
    
    def setUp(self):
        self.client = APIClient()
        self.base_url = ""  # URLs relativas
    
    def test_complete_post_workflow(self):
        # 1. REGISTER
        register_data = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "TestPass123",
        }
        response = self.client.post('/api/auth/register/', register_data, format='json')
        assert response.status_code == 201
        user_id = response.json()['user_id']
        
        # 2. LOGIN
        login_data = {
            "email": "test@example.com",
            "password": "TestPass123",
        }
        response = self.client.post('/api/auth/login/', login_data, format='json')
        assert response.status_code == 200
        token = response.json()['access_token']
        
        # 3. CREATE POST
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        post_data = {
            "title": "Mi primer post",
            "content": "Este es el contenido del post que debe tener más de 100 caracteres para poder ser publicado según las reglas de negocio del dominio que requieren contenido sustancial.",
            "tags": ["test", "e2e"],
        }
        response = self.client.post('/api/posts/', post_data, format='json')
        assert response.status_code == 201
        post_id = response.json()['id']
        slug = response.json()['slug']
        
        # 4. VERIFY NOT IN PUBLIC LIST (draft)
        response = self.client.get('/api/posts/')
        assert response.status_code == 200
        assert response.json()['total'] == 0
        
        # 5. PUBLISH POST
        response = self.client.post(f'/api/posts/{post_id}/publish/')
        assert response.status_code == 200
        
        # 6. VERIFY IN PUBLIC LIST
        response = self.client.get('/api/posts/')
        assert response.status_code == 200
        data = response.json()
        assert data['total'] == 1
        assert data['items'][0]['slug'] == slug
        
        # 7. GET POST DETAIL
        response = self.client.get(f'/api/posts/{slug}/')
        assert response.status_code == 200
        assert response.json()['title'] == "Mi primer post"
        
        # 8. ADD COMMENT
        comment_data = {"body": "Excelente artículo!"}
        response = self.client.post(f'/api/posts/{post_id}/comments/', comment_data, format='json')
        assert response.status_code == 201
        
        # 9. ARCHIVE POST
        response = self.client.post(f'/api/posts/{post_id}/archive/')
        assert response.status_code == 200
        
        # 10. VERIFY NO LONGER IN PUBLIC LIST
        response = self.client.get('/api/posts/')
        assert response.json()['total'] == 0


@pytest.mark.e2e
class TestAuthenticationFlowE2E(TestCase):
    """Test del flujo de autenticación completo"""
    
    def setUp(self):
        self.client = APIClient()
    
    def test_register_login_access_protected_endpoint(self):
        # 1. Register
        response = self.client.post('/api/auth/register/', {
            "email": "user@test.com",
            "username": "user",
            "password": "Pass1234",
        }, format='json')
        assert response.status_code == 201
        
        # 2. Login
        response = self.client.post('/api/auth/login/', {
            "email": "user@test.com",
            "password": "Pass1234",
        }, format='json')
        assert response.status_code == 200
        token = response.json()['access_token']
        
        # 3. Access /me without token (should fail)
        response = self.client.get('/api/auth/me/')
        assert response.status_code == 401
        
        # 4. Access /me with token (should succeed)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get('/api/auth/me/')
        assert response.status_code == 200
        assert response.json()['email'] == "user@test.com"


@pytest.mark.e2e
class TestCommentWorkflowE2E(TestCase):
    """Test del flujo completo de comentarios"""
    
    def setUp(self):
        self.client = APIClient()
    
    def test_cannot_comment_on_draft_post(self):
        # Setup: crear usuario y post en draft
        self.client.post('/api/auth/register/', {
            "email": "author@test.com",
            "username": "author",
            "password": "Pass1234",
        })
        response = self.client.post('/api/auth/login/', {
            "email": "author@test.com",
            "password": "Pass1234",
        })
        token = response.json()['access_token']
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.post('/api/posts/', {
            "title": "Draft Post",
            "content": "x" * 150,
            "tags": [],
        })
        post_id = response.json()['id']
        
        # Try to comment (should fail - post not published)
        response = self.client.post(f'/api/posts/{post_id}/comments/', {
            "body": "Comment on draft",
        })
        assert response.status_code in [422, 400]  # Domain error
