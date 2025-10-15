# ANB Rising Stars Showcase API

A FastAPI-based health check service for the ANB Rising Stars Showcase application.

## Features

- **FastAPI Framework**: Modern, fast web framework for building APIs with Python
- **Docker Support**: Containerized application for easy deployment
- **CORS Enabled**: Cross-Origin Resource Sharing configured for frontend integration
- **Comprehensive Health Checks**: Multiple health check endpoints for monitoring
- **Pydantic Models**: Data validation and serialization
- **Lightweight Service**: Focused on health monitoring and service status

## API Endpoints

### Health Check Endpoints
- `GET /health` - General health check endpoint
- `POST /api/auth/signup` - User signup
- `POST /api/auth/login` - Users authentication and JWT generation
- `POST /api/videos/upload` - Upload skills video by a player
- `GET /api/videos` - List all videos from the authenticated user
- `GET /api/videos/{video_id}` - Get details of a specific user video
- `DELETE /api/videos/{video_id}` - Delete own video if still allowed
- `GET /api/public/videos` - List public videos available for voting
- `POST /api/public/videos/{video_id}/vote` - Cast a vote for a public video
- `GET /api/public/rankings` - Show current ranking by accumulated votes

## Quick Start

### Prerequisites
- Python 3.11+
- Docker and Docker Compose (optional)

### Option 1: Run with Docker (Recommended)

1. **From the root directory, build and run the container:**
   ```bash
   docker-compose up --build
   ```

2. **Access the API:**
   - API: http://localhost:8000
   - Interactive API docs: http://localhost:8000/docs
   - Alternative docs: http://localhost:8000/redoc

### Option 2: Run Locally

1. **Navigate to the api directory:**
   ```bash
   cd api
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application:**
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

## Development

### Project Structure
```
/
├── docker-compose.yml   # Docker Compose configuration (root level)
└── api/
    ├── main.py          # FastAPI application
    ├── requirements.txt # Python dependencies
    ├── Dockerfile       # Docker configuration
    ├── .dockerignore    # Docker ignore file
    └── README.md        # This file
```

### Migraciones Manuales
NOTA: Las migraciones se ejecutan automáticamente al iniciar el contenedor 🎉, asi que solo ejecutelas manualmente de manera consciente 

```bash
cd api

# Generar nueva migración
alembic revision --autogenerate -m "Description"

# Aplicar migraciones
alembic upgrade head

# Ver historial
alembic history
```

### Environment Variables
Copy `.env.example` to `.env` and configure as needed:
```bash
cp .env.example .env
```

### API Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔧 URLs de Servicios

- **API**: http://localhost:8000
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

### Example API Usage

**Check API status:**
```bash
curl -X GET "http://localhost:8000/"
```

**Health check:**
```bash
curl -X GET "http://localhost:8000/health"
```

**Readiness check:**
```bash
curl -X GET "http://localhost:8000/health/ready"
```

**Liveness check:**
```bash
curl -X GET "http://localhost:8000/health/live"
```

**Player registration:**
```bash
curl -X POST "http://localhost:8000/api/auth/signup" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john.doe@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "password": "StrongPass123",
    "city": "Bogotá",
    "country": "Colombia"
  }'
```

**Voter registration:**
```bash
curl -X POST "http://localhost:8000/api/auth/signup" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "voter@example.com",
    "first_name": "Jane",
    "last_name": "Smith",
    "password": "SecurePass456",
    "city": "Medellín",
    "country": "Colombia"
  }'
```

## Docker Commands

**Build the image:**
```bash
docker build -t anb-api .
```

**Run the container:**
```bash
docker run -p 8000:8000 anb-api
```

**Run with Docker Compose (from root directory):**
```bash
docker-compose up -d
```

**View logs:**
```bash
docker-compose logs -f api
```

**Stop services:**
```bash
docker-compose down
```

## Production Considerations

- Configure CORS origins properly in `main.py`
- Add logging and monitoring integration
- Set up environment-specific configurations
- Implement rate limiting for health endpoints
- Add more detailed health checks (database connectivity, external services)
- Set up CI/CD pipeline
- Configure proper health check intervals in orchestration platforms

## Contributing

1. Create a feature branch
2. Make your changes
3. Test thoroughly
4. Submit a pull request

## License

This project is part of the ANB Rising Stars Showcase application.
