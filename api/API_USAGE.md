# ANB Rising Stars Showcase API

## 📋 Modelos de Datos

### Usuario
```json
{
  "id": "uuid",
  "email": "string",
  "first_name": "string",
  "last_name": "string", 
  "type": "player|voter",
  "city": "string (opcional)",
  "country": "string (opcional)"
}
```

### Video
```json
{
  "id": "uuid",
  "user_id": "uuid",
  "raw_video_id": "uuid",
  "processed_video_id": "uuid (opcional)",
  "title": "string",
  "status": "uploaded|processed|deleted",
  "uploaded_at": "datetime",
  "processed_at": "datetime (opcional)",
  "original_url": "string",
  "processed_url": "string (opcional)",
  "votes": "integer"
}
```

### Voto
```json
{
  "user_id": "uuid",
  "video_id": "uuid"
}
```

## 🚀 Endpoints

### Usuarios
- `POST /users/register` - Registrar usuario
- `GET /users` - Listar usuarios
- `GET /users/{user_id}` - Obtener usuario
- `PUT /users/{user_id}` - Actualizar usuario

### Videos
- `POST /videos` - Crear video
- `GET /videos` - Listar videos
- `GET /videos/{video_id}` - Obtener video
- `PUT /videos/{video_id}` - Actualizar video
- `DELETE /videos/{video_id}` - Eliminar video

### Votos
- `POST /votes` - Crear voto
- `DELETE /votes/{user_id}/{video_id}` - Eliminar voto
- `GET /videos/{video_id}/votes` - Obtener votos de un video

## 📝 Ejemplos de Uso

### 1. Registrar un Jugador
```bash
curl -X POST "http://localhost:8000/users/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john.doe@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "password1": "StrongPass123",
    "password2": "StrongPass123",
    "type": "player",
    "city": "Bogotá",
    "country": "Colombia"
  }'
```

### 2. Registrar un Votante
```bash
curl -X POST "http://localhost:8000/users/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "voter@example.com",
    "first_name": "Jane",
    "last_name": "Smith",
    "password1": "SecurePass456",
    "password2": "SecurePass456",
    "type": "voter",
    "city": "Medellín",
    "country": "Colombia"
  }'
```

### 3. Crear Video
```bash
curl -X POST "http://localhost:8000/videos" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "USER_UUID_AQUI",
    "title": "Tiros de tres en movimiento",
    "status": "uploaded",
    "original_url": "https://anb.com/uploads/raw-video.mp4"
  }'
```

### 4. Votar por un Video
```bash
curl -X POST "http://localhost:8000/votes" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "VOTER_UUID_AQUI",
    "video_id": "VIDEO_UUID_AQUI"
  }'
```

## 🛠️ Desarrollo

### Ejecutar con Docker
```bash
# Construir y levantar servicios
docker-compose up --build -d

# Ver logs
docker-compose logs -f api

# Parar servicios
docker-compose down
```

### Migraciones Manuales
```bash
cd api

# Generar nueva migración
alembic revision --autogenerate -m "Description"

# Aplicar migraciones
alembic upgrade head

# Ver historial
alembic history
```

## 🔧 URLs de Servicios
- **API**: http://localhost:8000
- **Documentación**: http://localhost:8000/docs
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

¡Las migraciones se ejecutan automáticamente al iniciar el contenedor! 🎉
