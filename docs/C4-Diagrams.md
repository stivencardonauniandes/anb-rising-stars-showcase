# Diagramas C4 - ANB Rising Stars Showcase

Este documento presenta los diagramas C4 (Context, Containers, Components, Code) para el sistema ANB Rising Stars Showcase, una plataforma de showcase de habilidades de baloncesto donde los jugadores pueden subir videos y recibir votos de la comunidad.

## 1. Diagrama de Contexto (C1)

```mermaid
C4Context
    title Sistema ANB Rising Stars Showcase - Diagrama de Contexto

    Person(players, "Jugadores de Baloncesto", "Atletas que suben videos de sus habilidades para participar en el showcase")
    Person(voters, "Votantes/Espectadores", "Usuarios que ven y votan por los videos de los jugadores")
    Person(admins, "Administradores", "Personal que monitorea y administra la plataforma")

    System(anb_system, "ANB Rising Stars Showcase", "Plataforma web para showcase de habilidades de baloncesto con sistema de votación")

    System_Ext(cdn, "CDN/Storage", "Servicio de almacenamiento y distribución de videos")
    System_Ext(analytics, "Sistema de Analytics", "Herramientas de monitoreo y análisis")

    Rel(players, anb_system, "Sube videos, gestiona perfil", "HTTPS")
    Rel(voters, anb_system, "Ve videos, vota, consulta rankings", "HTTPS")
    Rel(admins, anb_system, "Administra usuarios y contenido", "HTTPS")
    
    Rel(anb_system, cdn, "Almacena y sirve videos", "WebDAV/HTTP")
    Rel(anb_system, analytics, "Envía métricas", "HTTP")

    UpdateLayoutConfig($c4ShapeInRow="3", $c4BoundaryInRow="2")
```

## 2. Diagrama de Contenedores (C2)

```mermaid
C4Container
    title Sistema ANB Rising Stars Showcase - Diagrama de Contenedores

    Person(users, "Usuarios", "Jugadores, votantes y administradores")

    Container_Boundary(anb_boundary, "ANB Rising Stars Showcase") {
        Container(api_gateway, "API Gateway", "FastAPI", "API REST que maneja autenticación, videos y votaciones")
        Container(video_worker, "Video Worker", "Go", "Servicio de procesamiento asíncrono de videos")
        Container(cache, "Cache", "Redis", "Cache de sesiones y datos frecuentes")
        Container(message_queue, "Cola de Mensajes", "Redis Streams", "Cola para procesamiento asíncrono de videos")
        Container(database, "Base de Datos", "PostgreSQL", "Almacena usuarios, videos, votos y metadatos")
    }

    Container_Boundary(storage_boundary, "Almacenamiento") {
        Container(file_storage, "Almacenamiento de Archivos", "NextCloud", "Almacena videos originales y procesados")
    }

    Container_Boundary(monitoring_boundary, "Monitoreo") {
        Container(metrics, "Métricas", "Prometheus", "Recolección de métricas del sistema")
        Container(dashboard, "Dashboard", "Grafana", "Visualización de métricas y alertas")
        Container(redis_ui, "Redis UI", "RedisInsight", "Interfaz para administrar Redis")
    }

    Rel(users,api_gateway , "Usa", "HTTPS")
    Rel(api_gateway, database, "Lee/Escribe datos", "SQL")
    Rel(api_gateway, cache, "Cache de sesiones", "Redis Protocol")
    Rel(api_gateway, message_queue, "Envía tareas", "Redis Streams")
    Rel(api_gateway, file_storage, "Sube videos", "WebDAV")
    
    Rel(video_worker, message_queue, "Consume tareas", "Redis Streams")
    Rel(video_worker, database, "Actualiza estado", "SQL")
    Rel(video_worker, file_storage, "Procesa videos", "WebDAV")
    Rel(video_worker, metrics, "Envía métricas", "HTTP")
    
    Rel(metrics, dashboard, "Datos de métricas", "HTTP")
    Rel(metrics, api_gateway, "Scraping", "HTTP")
    Rel(metrics, video_worker, "Scraping", "HTTP")

    UpdateLayoutConfig($c4ShapeInRow="2", $c4BoundaryInRow="1")
```

## 3. Diagrama de Componentes (C3) - API Gateway

```mermaid
C4Component
    title API Gateway - Diagrama de Componentes

    Container(database, "Base de Datos", "PostgreSQL", "Almacenamiento de datos")
    Container(cache, "Cache", "Redis", "Cache y sesiones")
    Container(message_queue, "Cola de Mensajes", "Redis Streams", "Procesamiento asíncrono")
    Container(file_storage, "NextCloud", "WebDAV", "Almacenamiento de archivos")

    Container_Boundary(api_boundary, "API Gateway - FastAPI") {
        Component(main_app, "Main Application", "FastAPI", "Aplicación principal, configuración CORS y health check")
        Component(config_module, "Config Module", "Python Class", "Configuración centralizada y variables de entorno")
        
        Component(auth_router, "Auth Router", "FastAPI Router", "Endpoints de autenticación (/api/auth)")
        Component(public_router, "Public Router", "FastAPI Router", "Endpoints públicos (/api/public)")
        Component(videos_router, "Videos Router", "FastAPI Router", "Endpoints de gestión de videos (/api/videos)")
        
        Component(auth_service, "Auth Service", "Python Class", "Autenticación, registro y JWT")
        Component(vote_service, "Vote Service", "Python Class", "Lógica de votación y validaciones")
        Component(ranking_service, "Ranking Service", "Python Class", "Rankings públicos con paginación")
        Component(cache_service, "Cache Service", "Python Class", "Gestión de cache Redis")
        Component(video_service, "Video Service", "Python Class", "Upload, validación y gestión de videos")
        
        Component(db_models, "Database Models", "SQLAlchemy", "User, Video, Vote, VideoStatus")
        Component(pydantic_schemas, "Pydantic Schemas", "Pydantic", "12 schemas de validación y respuesta")
        Component(dependencies, "Dependencies", "FastAPI Dependencies", "get_current_user, get_db")
        Component(auth_utils, "Auth Utils", "Python Module", "JWT, password hashing, token verification")
        
        Component(middleware, "CORS Middleware", "FastAPI Middleware", "Cross-origin resource sharing")
    }

    Rel(main_app, config_module, "Loads config")
    Rel(main_app, middleware, "CORS handling")
    Rel(main_app, auth_router, "Include router")
    Rel(main_app, public_router, "Include router")
    Rel(main_app, videos_router, "Include router")
    
    Rel(auth_router, auth_service, "Delegates business logic")
    Rel(public_router, vote_service, "Handles voting")
    Rel(public_router, ranking_service, "Handles rankings")
    Rel(public_router, video_service, "Gets published videos")
    Rel(videos_router, video_service, "Handles video operations")
    
    Rel(auth_service, auth_utils, "Uses JWT functions")
    Rel(auth_service, db_models, "User CRUD")
    Rel(vote_service, db_models, "Vote, Video CRUD")
    Rel(ranking_service, db_models, "Video queries")
    Rel(ranking_service, cache_service, "Caching rankings")
    Rel(video_service, db_models, "Video CRUD")
    
    Rel(auth_service, pydantic_schemas, "UserSignup, UserLogin, UserAuthResponse")
    Rel(vote_service, pydantic_schemas, "VoteResponse")
    Rel(video_service, pydantic_schemas, "VideoUploadResponse, VideoResponse")
    Rel(ranking_service, pydantic_schemas, "Video schemas")
    
    Rel(auth_router, dependencies, "get_db")
    Rel(public_router, dependencies, "get_current_user, get_db")
    Rel(videos_router, dependencies, "get_current_user, get_db")
    
    Rel(db_models, database, "ORM Queries", "SQL")
    Rel(cache_service, cache, "Cache operations", "Redis Protocol")
    Rel(video_service, message_queue, "Video processing tasks", "Redis Streams")
    Rel(video_service, file_storage, "Upload/download videos", "WebDAV")
    Rel(video_service, config_module, "Nextcloud config")

    UpdateLayoutConfig($c4ShapeInRow="3", $c4BoundaryInRow="1")
```

## 4. Diagrama de Código (C4) - Modelos de Datos

```mermaid
C4Component
    title Modelos de Datos - Diagrama de Código

    Container_Boundary(models_boundary, "Database Models - SQLAlchemy") {
        Component(user_model, "User Model", "SQLAlchemy Model", "id: UUID , email: str, first_name: str, last_name: str, password: str, city: str?, country: str?")
        Component(video_model, "Video Model", "SQLAlchemy Model", "id: UUID , user_id: UUID , raw_video_id: UUID, processed_video_id: UUID?, title: str, status: VideoStatus, uploaded_at: DateTime, processed_at: DateTime?, original_url: str, processed_url: str?, votes: int")
        Component(vote_model, "Vote Model", "SQLAlchemy Model", "user_id: UUID, video_id: UUID - Composite Primary Key")
        Component(video_status, "VideoStatus Enum", "Python Enum", "uploaded, processed, deleted")
    }

    Container_Boundary(schemas_boundary, "Pydantic Schemas") {
        Component(user_schemas, "User Schemas", "Pydantic Models", "UserSignup, UserLogin, UserResponse, UserAuthResponse")
        Component(video_schemas, "Video Schemas", "Pydantic Models", "VideoCreate, VideoResponse, VideoUpdate, VideoUploadResponse")
        Component(vote_schemas, "Vote Schemas", "Pydantic Models", "VoteCreate, VoteResponse")
        Component(auth_schemas, "Auth Schemas", "Pydantic Models", "Token, TokenData")
    }

    Container_Boundary(services_boundary, "Service Classes") {
        Component(auth_service_class, "AuthService", "Python Class", "authenticate_user, register_user, get_user_by_email, get_user_by_id, validate_user_credentials")
        Component(vote_service_class, "VoteService", "Python Class", "vote_for_video, has_user_voted")
        Component(ranking_service_class, "RankingService", "Python Class", "get_public_videos_ranking, get_top_videos, get_ranking_stats")
        Component(cache_service_class, "CacheService", "Python Class", "get, set, delete, exists, get_or_set")
        Component(video_service_class, "VideoService", "Python Class", "process_video_upload, get_videos_for_user, get_video_by_id, delete_video, upload_to_nextcloud")
    }

    Container_Boundary(config_boundary, "Configuration & Utils") {
        Component(config_class, "Config", "Python Class", "Centralized configuration with environment detection")
        Component(auth_utils_module, "Auth Utils", "Python Module", "verify_password, get_password_hash, create_access_token, verify_token, get_user_from_token")
    }

    Rel(user_model, video_model, "One-to-Many", "videos relationship")
    Rel(user_model, vote_model, "One-to-Many", "votes relationship")
    Rel(video_model, vote_model, "One-to-Many", "vote_records relationship")
    Rel(video_model, video_status, "Uses", "status field")

    Rel(auth_service_class, user_model, "CRUD operations")
    Rel(vote_service_class, vote_model, "Create votes")
    Rel(vote_service_class, video_model, "Update vote counts")
    Rel(ranking_service_class, video_model, "Query rankings")
    Rel(ranking_service_class, cache_service_class, "Cache rankings")
    Rel(video_service_class, video_model, "CRUD operations")

    Rel(auth_service_class, auth_utils_module, "Password & JWT operations")
    Rel(video_service_class, config_class, "Nextcloud configuration")
    Rel(auth_utils_module, config_class, "JWT configuration")

    Rel(user_schemas, auth_service_class, "Input/Output validation")
    Rel(video_schemas, video_service_class, "Input/Output validation")
    Rel(vote_schemas, vote_service_class, "Input/Output validation")
    Rel(auth_schemas, auth_utils_module, "Token validation")

    UpdateLayoutConfig($c4ShapeInRow="2", $c4BoundaryInRow="1")
```

## Descripción de los Diagramas

### 1. Contexto (C1)
Muestra el sistema ANB Rising Stars Showcase en su entorno, con los diferentes tipos de usuarios (jugadores, votantes, administradores) y los sistemas externos con los que interactúa.

### 2. Contenedores (C2)
Detalla la arquitectura de microservicios del sistema, incluyendo:
- **API Gateway (FastAPI)**: Maneja la lógica de negocio y endpoints REST
- **Video Worker (Go)**: Procesa videos de forma asíncrona
- **Base de Datos (PostgreSQL)**: Almacena datos estructurados
- **Cache (Redis)**: Mejora el rendimiento y maneja colas de mensajes
- **NextCloud**: Almacenamiento de archivos de video
- **Monitoreo**: Prometheus y Grafana para observabilidad

### 3. Componentes (C3)
Se enfoca en la estructura interna del API Gateway, mostrando la arquitectura real implementada:
- **3 Routers**: auth (autenticación), public (votación/rankings), videos (gestión de videos)
- **5 Services**: AuthService, VoteService, RankingService, CacheService, VideoService
- **Config Module**: Configuración centralizada con detección de entorno
- **Auth Utils**: Utilidades JWT y hashing de contraseñas
- **Dependencies**: get_current_user, get_db para inyección de dependencias
- **12 Pydantic Schemas**: Validación completa de entrada y salida

### 4. Código (C4)
Muestra las clases y relaciones reales del sistema implementado:
- **Database Models**: User, Video, Vote con relaciones One-to-Many y composite keys
- **Pydantic Schemas**: 12 schemas organizados por funcionalidad (User, Video, Vote, Auth)
- **Service Classes**: 5 servicios con métodos específicos implementados
- **Configuration**: Gestión centralizada de configuración con validación
- **Auth Utils**: Funciones de seguridad para JWT y contraseñas

## 5. Arquitectura de Testing

El proyecto implementa una arquitectura de testing completa con múltiples niveles:

### Testing Pyramid Implementado

```mermaid
graph TD
    A[Integration Tests - Newman/Postman] --> B[Endpoint Tests - FastAPI TestClient]
    B --> C[Unit Tests - Pytest]
    C --> D[Code Coverage - 93.91%]
    
    E[30+ Postman Tests] --> A
    F[31 Endpoint Tests] --> B
    G[128 Unit Tests] --> C
    
    H[Auth Tests] --> E
    I[Video Tests] --> E
    J[Vote Tests] --> E
    
    K[Router Tests] --> F
    L[Service Tests] --> F
    
    M[Service Unit Tests] --> G
    N[Model Unit Tests] --> G
    O[Auth Unit Tests] --> G
    P[Config Unit Tests] --> G
```

### Cobertura de Testing por Componente

- **Unit Tests (128 tests)**: 100% pass rate
  - VideoService: 30 tests (100% coverage)
  - AuthService: 17 tests (100% coverage) 
  - Auth Utils: 24 tests (100% coverage)
  - Database Models: 19 tests (100% coverage)
  - Configuration: 28 tests (100% coverage)

- **Integration Tests (31 endpoint tests)**: 100% pass rate
  - Video endpoints: 13 tests
  - Authentication: 18 tests

- **API Tests (30+ Postman tests)**: Newman compatible
  - Authentication scenarios: 8 tests
  - Video management: 21 tests
  - Voting system: 8 tests

## Tecnologías Utilizadas

- **Backend**: FastAPI (Python), Go
- **Base de Datos**: PostgreSQL
- **Cache/Cola**: Redis
- **Almacenamiento**: NextCloud (WebDAV)
- **Monitoreo**: Prometheus, Grafana
- **Contenedores**: Docker, Docker Compose
- **ORM**: SQLAlchemy
- **Validación**: Pydantic
- **Autenticación**: JWT
- **Testing**: Pytest, Newman, FastAPI TestClient
- **Coverage**: pytest-cov (93.91% coverage)
