# Test de Concurrencia - Upload de Videos

Este script simula 5 usuarios subiendo videos simultáneamente durante 1 minuto al endpoint de upload de videos.

## 📋 Requisitos

- Node.js (v14 o superior)
- npm o yarn

## 🚀 Instalación

```bash
cd test_concurrency
npm install
```

## 🔧 Configuración

### 1. Obtener Token de Autenticación

Primero necesitas obtener un token de autenticación. Puedes hacerlo con:

```bash
curl --location 'http://localhost:8000/api/auth/login' \
--header 'Content-Type: application/json' \
--data '{
    "email": "tu-email@example.com",
    "password": "tu-password"
}'
```

### 2. Configurar el Token

Exporta el token como variable de entorno:

```bash
export AUTH_TOKEN="tu-token-aqui"
```

O en Windows:

```bash
set AUTH_TOKEN=tu-token-aqui
```

## ▶️ Ejecutar los Tests

### Smoke Test (5 usuarios, 1 minuto)
```bash
npm test
# o
npm run smoke
```

### Ramp-Up Tests
```bash
npm run ramp:100    # 100 usuarios
npm run ramp:200    # 200 usuarios
npm run ramp:300    # 300 usuarios
npm run ramp:500    # 500 usuarios
npm run ramp:progressive  # Test progresivo
npm run ramp:custom  # Test personalizado (configurar MAX_USERS)
```

### Stability Test (Test de Estabilidad)
Ejecuta 5 minutos al 80% del mejor nivel previo sin degradación para confirmar estabilidad.

```bash
npm run stability
```

Por defecto usa 200 usuarios como nivel base (80% = 160 usuarios). Para usar un nivel diferente:

```bash
BASE_LEVEL=300 npm run stability  # Usará 240 usuarios (80% de 300)
```

**Configuración del Stability Test:**
- **Ramp-up**: 60 segundos (0 → 80% de X usuarios)
- **Hold duration**: 5 minutos (mantiene la carga estable)
- **Nivel base (X)**: Configurable via `BASE_LEVEL` (default: 200)

## 📊 Configuración del Test

Puedes modificar las siguientes variables en `index.js`:

- `API_URL`: URL del endpoint (por defecto: `http://localhost:8000/api/videos/upload`)
- `DURATION_SECONDS`: Duración del test en segundos (por defecto: 60)
- `CONCURRENT_USERS`: Número de usuarios concurrentes (por defecto: 5)
- `VIDEO_FILE_PATH`: Ruta al archivo de video (por defecto: `../sample-video.mp4`)

## 📈 Resultados

El test mostrará:

- **Total Test Duration**: Duración total del test
- **Total Requests**: Número total de requests realizadas
- **Successful Requests**: Requests exitosas
- **Failed Requests**: Requests fallidas
- **Success Rate**: Porcentaje de éxito
- **Requests per Second**: Requests por segundo
- **Response Time Statistics**: 
  - Average: Tiempo promedio de respuesta
  - Minimum: Tiempo mínimo de respuesta
  - Maximum: Tiempo máximo de respuesta
- **Errors Summary**: Resumen de errores (si hay)

## 🔍 Ejemplo de Salida

```
🚀 Starting concurrency test...
📊 Configuration:
   - API URL: http://localhost:8000/api/videos/upload
   - Duration: 60 seconds
   - Concurrent Users: 5
   - Video File: /path/to/sample-video.mp4

👤 User 1 started uploading videos...
👤 User 2 started uploading videos...
...
✅ User 1 - Request 1 - Success in 5234ms - Task ID: abc-123
✅ User 2 - Request 1 - Success in 5123ms - Task ID: def-456
...

═══════════════════════════════════════════════════════════
📊 CONCURRENCY TEST RESULTS
═══════════════════════════════════════════════════════════
⏱️  Total Test Duration: 60.12 seconds
📈 Total Requests: 45
✅ Successful Requests: 45
❌ Failed Requests: 0
📊 Success Rate: 100.00%
⚡ Requests per Second: 0.75

⏱️  Response Time Statistics:
   - Average: 5234.56ms
   - Minimum: 4123ms
   - Maximum: 6789ms
═══════════════════════════════════════════════════════════
```

## 🐛 Troubleshooting

### Error: "Video file not found"
- Verifica que el archivo `sample-video.mp4` existe en la raíz del proyecto
- O ajusta la ruta en `VIDEO_FILE_PATH`

### Error: "AUTH_TOKEN not set"
- Asegúrate de exportar el token como variable de entorno
- O modifica directamente en el código (no recomendado para producción)

### Error: "ECONNREFUSED"
- Verifica que la API esté ejecutándose en `http://localhost:8000`
- O ajusta la `API_URL` si la API está en otro puerto

## 📝 Notas

- El test hace un pequeño delay (100-200ms) entre requests para no sobrecargar el servidor
- El timeout por request es de 5 minutos (300000ms)
- Cada usuario sube videos continuamente hasta que se cumpla el tiempo
- El **Stability Test** está diseñado para confirmar que el sistema puede mantener una carga sostenible (80% del nivel máximo sin degradación) durante 5 minutos

## 🎯 Escenarios de Prueba

1. **Smoke Test**: Validación básica con 5 usuarios durante 1 minuto
2. **Ramp-Up Tests**: Identificar el nivel máximo sin degradación (ramp-up de 3 min, hold de 5 min)
3. **Stability Test**: Confirmar estabilidad ejecutando 5 minutos al 80% del mejor nivel previo

