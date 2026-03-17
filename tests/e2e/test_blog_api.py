"""
E2E TESTS - Blog API Endpoints

Tests end-to-end que verifican flujos completos desde la API HTTP.
Simulan requests reales de clientes (web, mobile).
"""
import pytest
from rest_framework import status


@pytest.mark.django_db
class TestPostCreationFlow:
    """E2E: Flujo completo de creación de post."""
    
    def test_register_login_create_post_success(self, api_client):
        """
        Flujo completo: Registro → Login → Crear post
        
        Como un nuevo usuario
        Quiero registrarme y crear un post
        Para compartir contenido en la plataforma
        """
        # Step 1: Registrarse
        register_response = api_client.post('/api/auth/register/', {
            'email': 'newuser@example.com',
            'username': 'newuser',
            'password': 'NewPassword123',
        })
        assert register_response.status_code == status.HTTP_201_CREATED
        assert 'user_id' in register_response.json()
        
        # Step 2: Login
        login_response = api_client.post('/api/auth/login/', {
            'email': 'newuser@example.com',
            'password': 'NewPassword123',
        })
        assert login_response.status_code == status.HTTP_200_OK
        
        token = login_response.json()['access_token']
        assert token is not None
        
        # Step 3: Crear post
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        create_response = api_client.post('/api/posts/', {
            'title': 'Mi primer post',
            'content': 'Este es el contenido de mi primer post. ' * 10,
            'tags': ['introducción', 'bienvenida'],
        })
        assert create_response.status_code == status.HTTP_201_CREATED
        
        post_data = create_response.json()
        assert post_data['title'] == 'Mi primer post'
        assert post_data['slug'] == 'mi-primer-post'
        assert 'id' in post_data
    
    def test_create_post_without_auth_fails(self, api_client):
        """Crear post sin autenticación falla con 401."""
        response = api_client.post('/api/posts/', {
            'title': 'Post sin auth',
            'content': 'Contenido largo ' * 20,
        })
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestPostPublishingFlow:
    """E2E: Flujo completo de publicación."""
    
    def test_create_publish_verify_in_list(self, authenticated_client):
        """
        Flujo: Crear → Publicar → Verificar en lista pública
        
        Como autor
        Quiero publicar mi post
        Para que sea visible en la lista pública
        """
        # Step 1: Crear post
        create_response = authenticated_client.post('/api/posts/', {
            'title': 'Post para publicar',
            'content': 'Contenido sustancial que cumple con el mínimo de 100 caracteres requeridos para poder publicar el post sin problemas.',
            'tags': ['tutorial'],
        })
        assert create_response.status_code == status.HTTP_201_CREATED
        
        post_id = create_response.json()['id']
        
        # Step 2: Verificar no está en lista pública (aún draft)
        list_response = authenticated_client.get('/api/posts/')
        assert list_response.status_code == status.HTTP_200_OK
        
        posts = list_response.json()['items']
        post_ids = [p['id'] for p in posts]
        assert post_id not in post_ids  # no visible porque es draft
        
        # Step 3: Publicar
        publish_response = authenticated_client.post(f'/api/posts/{post_id}/publish/')
        assert publish_response.status_code == status.HTTP_200_OK
        
        # Step 4: Verificar ahora SÍ está en lista pública
        list_response = authenticated_client.get('/api/posts/')
        posts = list_response.json()['items']
        post_ids = [p['id'] for p in posts]
        assert post_id in post_ids  # ahora sí visible
    
    def test_publish_short_content_post_fails(self, authenticated_client):
        """Publicar post con contenido corto falla con 422."""
        # Crear post con contenido corto
        create_response = authenticated_client.post('/api/posts/', {
            'title': 'Post corto',
            'content': 'Muy corto',  # < 100 chars
        })
        post_id = create_response.json()['id']
        
        # Intentar publicar
        publish_response = authenticated_client.post(f'/api/posts/{post_id}/publish/')
        assert publish_response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert 'al menos 100 caracteres' in publish_response.json()['error']


@pytest.mark.django_db
class TestCommentingFlow:
    """E2E: Flujo completo de comentarios."""
    
    def test_publish_post_add_comment_verify(self, authenticated_client, db_cleanup):
        """
        Flujo: Publicar post → Agregar comentario → Verificar en detalle
        
        Como lector
        Quiero comentar en un post publicado
        Para participar en la discusión
        """
        # Step 1: Crear y publicar post
        create_response = authenticated_client.post('/api/posts/', {
            'title': 'Post con comentarios',
            'content': 'Contenido interesante que invita a comentar. ' * 10,
            'tags': ['discusión'],
        })
        post_id = create_response.json()['id']
        
        authenticated_client.post(f'/api/posts/{post_id}/publish/')
        
        # Step 2: Agregar comentario
        comment_response = authenticated_client.post(f'/api/posts/{post_id}/comments/', {
            'body': '¡Excelente artículo! Me ayudó mucho.',
        })
        assert comment_response.status_code == status.HTTP_201_CREATED
        
        comment_data = comment_response.json()
        assert comment_data['body'] == '¡Excelente artículo! Me ayudó mucho.'
        assert 'id' in comment_data
        
        # Step 3: Verificar comentario en detalle del post
        detail_response = authenticated_client.get(f'/api/posts/post-con-comentarios/')
        assert detail_response.status_code == status.HTTP_200_OK
        
        post_detail = detail_response.json()
        assert len(post_detail['comments']) == 1
        assert post_detail['comments'][0]['body'] == '¡Excelente artículo! Me ayudó mucho.'
    
    def test_comment_on_archived_post_fails(self, authenticated_client, db_cleanup):
        """Comentar en post archivado falla con 422."""
        # Crear, publicar, y archivar
        create_response = authenticated_client.post('/api/posts/', {
            'title': 'Post a archivar',
            'content': 'Contenido largo ' * 20,
        })
        post_id = create_response.json()['id']
        
        authenticated_client.post(f'/api/posts/{post_id}/publish/')
        authenticated_client.post(f'/api/posts/{post_id}/archive/')
        
        # Intentar comentar
        comment_response = authenticated_client.post(f'/api/posts/{post_id}/comments/', {
            'body': 'Intento comentar en archivado',
        })
        assert comment_response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.django_db
class TestArchivingFlow:
    """E2E: Flujo completo de archivado."""
    
    def test_author_can_archive_own_post(self, authenticated_client, db_cleanup):
        """Autor puede archivar su propio post."""
        # Crear y publicar
        create_response = authenticated_client.post('/api/posts/', {
            'title': 'Post a archivar',
            'content': 'Contenido largo ' * 20,
        })
        post_id = create_response.json()['id']
        authenticated_client.post(f'/api/posts/{post_id}/publish/')
        
        # Archivar
        archive_response = authenticated_client.post(f'/api/posts/{post_id}/archive/')
        assert archive_response.status_code == status.HTTP_200_OK
        
        # Verificar no aparece en lista pública
        list_response = authenticated_client.get('/api/posts/')
        post_ids = [p['id'] for p in list_response.json()['items']]
        assert post_id not in post_ids


@pytest.mark.django_db
class TestPaginationFlow:
    """E2E: Flujo de paginación."""
    
    def test_list_posts_pagination_works(self, authenticated_client, create_post_helper, db_cleanup):
        """Paginación funciona correctamente en lista de posts."""
        # Crear 5 posts publicados
        for i in range(5):
            create_post_helper(title=f'Post {i}', published=True)
        
        # Página 1 (2 items)
        response = authenticated_client.get('/api/posts/?page=1&page_size=2')
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data['total'] == 5
        assert len(data['items']) == 2
        assert data['page'] == 1
        assert data['has_next'] is True
        assert data['has_previous'] is False
        
        # Página 2
        response = authenticated_client.get('/api/posts/?page=2&page_size=2')
        data = response.json()
        assert len(data['items']) == 2
        assert data['page'] == 2
        assert data['has_next'] is True
        assert data['has_previous'] is True


@pytest.mark.django_db
class TestCompleteUserJourney:
    """E2E: Journey completo de usuario."""
    
    def test_new_user_complete_journey(self, api_client, db_cleanup):
        """
        Journey completo: Registro → Login → Crear → Publicar → Comentar → Archivar
        
        Simula el recorrido completo de un nuevo usuario en la plataforma.
        """
        # 1. Registro
        register_resp = api_client.post('/api/auth/register/', {
            'email': 'journey@example.com',
            'username': 'journeyuser',
            'password': 'JourneyPass123',
        })
        assert register_resp.status_code == 201
        
        # 2. Login
        login_resp = api_client.post('/api/auth/login/', {
            'email': 'journey@example.com',
            'password': 'JourneyPass123',
        })
        assert login_resp.status_code == 200
        
        token = login_resp.json()['access_token']
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        # 3. Ver perfil
        profile_resp = api_client.get('/api/auth/me/')
        assert profile_resp.status_code == 200
        assert profile_resp.json()['email'] == 'journey@example.com'
        
        # 4. Crear post
        create_resp = api_client.post('/api/posts/', {
            'title': 'Mi viaje en la plataforma',
            'content': 'Este es mi primer post documentando mi experiencia. ' * 10,
            'tags': ['introducción', 'experiencia'],
        })
        assert create_resp.status_code == 201
        post_id = create_resp.json()['id']
        
        # 5. Publicar
        publish_resp = api_client.post(f'/api/posts/{post_id}/publish/')
        assert publish_resp.status_code == 200
        
        # 6. Agregar comentario a su propio post
        comment_resp = api_client.post(f'/api/posts/{post_id}/comments/', {
            'body': 'Actualizando mi propio post con más información.',
        })
        assert comment_resp.status_code == 201
        
        # 7. Verificar está en lista pública
        list_resp = api_client.get('/api/posts/')
        assert post_id in [p['id'] for p in list_resp.json()['items']]
        
        # 8. Archivar
        archive_resp = api_client.post(f'/api/posts/{post_id}/archive/')
        assert archive_resp.status_code == 200
        
        # 9. Verificar ya no está en lista pública
        list_resp = api_client.get('/api/posts/')
        assert post_id not in [p['id'] for p in list_resp.json()['items']]
