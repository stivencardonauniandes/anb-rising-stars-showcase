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

    System_Ext(email_system, "Sistema de Email", "Servicio externo para notificaciones por correo")
    System_Ext(cdn, "CDN/Storage", "Servicio de almacenamiento y distribución de videos")
    System_Ext(analytics, "Sistema de Analytics", "Herramientas de monitoreo y análisis")

    Rel(players, anb_system, "Sube videos, gestiona perfil", "HTTPS")
    Rel(voters, anb_system, "Ve videos, vota, consulta rankings", "HTTPS")
    Rel(admins, anb_system, "Administra usuarios y contenido", "HTTPS")
    
    Rel(anb_system, email_system, "Envía notificaciones", "SMTP")
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
        Container(web_app, "Aplicación Web", "React/Vue.js", "Interfaz de usuario para interactuar con la plataforma")
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

    Rel(users, web_app, "Usa", "HTTPS")
    Rel(web_app, api_gateway, "Hace llamadas API", "HTTPS/JSON")
    
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

    Container(web_app, "Aplicación Web", "React/Vue.js", "Frontend de la aplicación")
    Container(database, "Base de Datos", "PostgreSQL", "Almacenamiento de datos")
    Container(cache, "Cache", "Redis", "Cache y sesiones")
    Container(message_queue, "Cola de Mensajes", "Redis Streams", "Procesamiento asíncrono")
    Container(file_storage, "NextCloud", "WebDAV", "Almacenamiento de archivos")

    Container_Boundary(api_boundary, "API Gateway - FastAPI") {
        Component(main_app, "Main Application", "FastAPI", "Aplicación principal y configuración CORS")
        
        Component(auth_router, "Auth Router", "FastAPI Router", "Endpoints de autenticación (login/signup)")
        Component(public_router, "Public Router", "FastAPI Router", "Endpoints públicos (votación/rankings)")
        Component(video_upload, "Video Upload", "FastAPI Endpoint", "Endpoint para subida de videos")
        
        Component(auth_service, "Auth Service", "Python Class", "Lógica de autenticación y JWT")
        Component(vote_service, "Vote Service", "Python Class", "Lógica de votación")
        Component(ranking_service, "Ranking Service", "Python Class", "Lógica de rankings y estadísticas")
        Component(cache_service, "Cache Service", "Python Class", "Gestión de cache Redis")
        
        Component(db_models, "Database Models", "SQLAlchemy", "Modelos ORM (User, Video, Vote)")
        Component(schemas, "Pydantic Schemas", "Pydantic", "Validación y serialización de datos")
        Component(dependencies, "Dependencies", "FastAPI Dependencies", "Inyección de dependencias (DB, Auth)")
        
        Component(middleware, "Middleware", "FastAPI Middleware", "CORS, logging, error handling")
    }

    Rel(web_app, main_app, "HTTP Requests", "HTTPS/JSON")
    Rel(main_app, middleware, "Procesa requests")
    Rel(main_app, auth_router, "Include router")
    Rel(main_app, public_router, "Include router")
    Rel(main_app, video_upload, "Include endpoint")
    
    Rel(auth_router, auth_service, "Usa")
    Rel(public_router, vote_service, "Usa")
    Rel(public_router, ranking_service, "Usa")
    
    Rel(auth_service, db_models, "Usa")
    Rel(vote_service, db_models, "Usa")
    Rel(ranking_service, db_models, "Usa")
    Rel(ranking_service, cache_service, "Usa")
    
    Rel(auth_service, schemas, "Valida datos")
    Rel(vote_service, schemas, "Valida datos")
    Rel(ranking_service, schemas, "Valida datos")
    
    Rel(auth_router, dependencies, "Inyecta DB")
    Rel(public_router, dependencies, "Inyecta DB/Auth")
    Rel(video_upload, dependencies, "Inyecta DB")
    
    Rel(db_models, database, "ORM Queries", "SQL")
    Rel(cache_service, cache, "Cache operations", "Redis")
    Rel(video_upload, message_queue, "Envía tareas", "Redis Streams")
    Rel(video_upload, file_storage, "Sube archivos", "WebDAV")

    UpdateLayoutConfig($c4ShapeInRow="3", $c4BoundaryInRow="1")
```

## 4. Diagrama de Código (C4) - Modelos de Datos

```mermaid
C4Component
    title Modelos de Datos - Diagrama de Código

    Container_Boundary(models_boundary, "Database Models (SQLAlchemy)") {
        Component(user_model, "User Model", "SQLAlchemy Model", "id: UUID, email: str, first_name: str, last_name: str, password: str, city: str, country: str")
        Component(video_model, "Video Model", "SQLAlchemy Model", "id: UUID, user_id: UUID, raw_video_id: UUID, processed_video_id: UUID, title: str, status: VideoStatus, uploaded_at: DateTime, processed_at: DateTime, original_url: str, processed_url: str, votes: int")
        Component(vote_model, "Vote Model", "SQLAlchemy Model", "user_id: UUID (PK), video_id: UUID (PK)")
        Component(video_status, "VideoStatus Enum", "Python Enum", "uploaded, processed, deleted")
    }

    Container_Boundary(schemas_boundary, "Pydantic Schemas") {
        Component(user_signup, "UserSignup", "Pydantic Model", "email: EmailStr, first_name: str, last_name: str, password: str, city: str, country: str")
        Component(user_login, "UserLogin", "Pydantic Model", "email: EmailStr, password: str")
        Component(user_auth_response, "UserAuthResponse", "Pydantic Model", "access_token: str, token_type: str, user: UserResponse")
        Component(video_upload_response, "VideoUploadResponse", "Pydantic Model", "message: str, task_id: str")
        Component(vote_response, "VoteResponse", "Pydantic Model", "message: str, video_id: UUID, total_votes: int")
        Component(ranking_response, "RankingResponse", "Pydantic Model", "videos: List[VideoRanking], pagination: PaginationInfo")
    }

    Container_Boundary(services_boundary, "Service Classes") {
        Component(auth_service_class, "AuthService", "Python Class", "authenticate_user(), register_user(), create_access_token(), verify_token()")
        Component(vote_service_class, "VoteService", "Python Class", "vote_for_video(), has_user_voted(), get_video_votes()")
        Component(ranking_service_class, "RankingService", "Python Class", "get_public_videos_ranking(), get_top_videos(), get_ranking_stats()")
        Component(cache_service_class, "CacheService", "Python Class", "get(), set(), delete(), exists(), get_or_set()")
    }

    ' Relaciones entre modelos
    Rel(user_model, video_model, "One-to-Many", "videos relationship")
    Rel(user_model, vote_model, "One-to-Many", "votes relationship")
    Rel(video_model, vote_model, "One-to-Many", "vote_records relationship")
    Rel(video_model, video_status, "Uses", "status field")

    ' Relaciones servicios con modelos
    Rel(auth_service_class, user_model, "CRUD operations")
    Rel(vote_service_class, vote_model, "CRUD operations")
    Rel(vote_service_class, video_model, "Read/Update votes")
    Rel(ranking_service_class, video_model, "Read operations")
    Rel(ranking_service_class, cache_service_class, "Caching")

    ' Relaciones schemas con modelos
    Rel(user_signup, user_model, "Creates")
    Rel(user_login, auth_service_class, "Validates")
    Rel(user_auth_response, auth_service_class, "Returns")
    Rel(vote_response, vote_service_class, "Returns")
    Rel(ranking_response, ranking_service_class, "Returns")

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
Se enfoca en la estructura interna del API Gateway, mostrando:
- **Routers**: Organizan endpoints por funcionalidad
- **Services**: Contienen la lógica de negocio
- **Models**: Definen la estructura de datos
- **Schemas**: Validan entrada y salida de datos
- **Dependencies**: Manejan inyección de dependencias

### 4. Código (C4)
Muestra las clases y relaciones principales del modelo de datos:
- **Modelos SQLAlchemy**: User, Video, Vote con sus relaciones
- **Schemas Pydantic**: Para validación y serialización
- **Clases de Servicio**: Encapsulan la lógica de negocio

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
