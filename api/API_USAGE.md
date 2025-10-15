# ANB Rising Stars Showcase API

## 📋 Modelos de Datos

### Usuario
```json
{
  "id": "uuid",
  "email": "string",
  "first_name": "string",
  "last_name": "string", 
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
- `POST /api/auth/signup` - Registrar usuario
- `POST /api/auth/login` - Autenticación de usuarios y generación de token JWT

### Videos
- `POST /api/videos/upload` - Subida de video de habilidades por un jugador
- `GET /api/videos` - Lista todos los videos del usuario autenticado
- `GET /api/videos/{video_id}` - Obtiene el detalle de un video específico del usuario
- `DELETE /api/videos/{video_id}` - Elimina un video propio si aún es permitido

### Votos
- `GET /api/public/videos` - Lista videos públicos disponibles para votacion
- `POST /api/public/videos/{video_id}/vote` - Emite un voto por un video público
- `GET /api/public/rankings` - Muestra el ranking actual por votos acumulados

## 📝 Ejemplos de Uso

### 1. Subir Video
```bash
curl -X POST "http://localhost:8000/api/videos/upload" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "USER_UUID_AQUI",
    "title": "Tiros de tres en movimiento",
    "status": "uploaded",
    "original_url": "https://anb.com/uploads/raw-video.mp4"
  }'
```

### 2. Votar por un Video
```bash
curl -X POST "http://localhost:8000/api/public/videos/{video_id}/vote" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "VOTER_UUID_AQUI",
    "video_id": "VIDEO_UUID_AQUI"
  }'
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
