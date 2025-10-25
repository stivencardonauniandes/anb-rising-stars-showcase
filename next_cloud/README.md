# Nextcloud Independiente

Esta configuración permite ejecutar Nextcloud en un servidor independiente usando Docker Compose.

## 🚀 Inicio Rápido

### 1. Configuración Inicial

```bash
# Ejecutar el script de configuración
./setup.sh
```

### 2. Configuración Manual

Si prefieres configurar manualmente:

```bash
# Copiar archivo de variables de entorno
cp env.example .env

# Editar variables según tu servidor
nano .env

# Crear directorios necesarios
mkdir -p data config apps

# Desplegar servicios
docker-compose up -d
```

## 📋 Servicios Incluidos

- **Nextcloud**: Servidor principal (puerto 8080)
- **PostgreSQL**: Usa servidor PostgreSQL externo existente
- **Redis**: Cache y sesiones (puerto 6379)
- **Adminer**: Administración de BD (puerto 8081)

## 🔧 Configuración

### Requisitos del Servidor PostgreSQL

**IMPORTANTE**: Esta configuración requiere que tengas un servidor PostgreSQL ejecutándose externamente. Asegúrate de que:

1. **Base de datos `nextcloud` existe** en tu servidor PostgreSQL
2. **Usuario tiene permisos** para acceder a la base de datos
3. **Servidor es accesible** desde el contenedor de Nextcloud
4. **Puerto 5432 está abierto** (o el puerto que uses)

### Variables de Entorno Importantes

Edita el archivo `.env` con tus valores:

```bash
# Configuración básica
NEXTCLOUD_ADMIN_USER=admin
NEXTCLOUD_ADMIN_PASSWORD=admin123

# Configuración de dominio (IMPORTANTE para producción)
NEXTCLOUD_TRUSTED_DOMAINS=localhost your-domain.com your-server-ip
OVERWRITEHOST=your-domain.com
OVERWRITEPROTOCOL=https

# Configuración de base de datos (servidor externo)
POSTGRES_HOST=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
```

### Configuración para Producción

1. **Cambiar contraseñas por defecto**
2. **Configurar dominio correcto** en `NEXTCLOUD_TRUSTED_DOMAINS`
3. **Configurar HTTPS** con `OVERWRITEPROTOCOL=https`
4. **Configurar host** con `OVERWRITEHOST=tu-dominio.com`

## 🌐 Acceso

- **Nextcloud**: http://localhost:8080
- **Adminer**: http://localhost:8081

### Credenciales por Defecto

- **Usuario**: admin
- **Contraseña**: admin123

⚠️ **IMPORTANTE**: Cambia estas credenciales en producción.

## 📁 Estructura de Archivos

```
next_cloud/
├── docker-compose.yml      # Configuración de servicios
├── env.example            # Variables de entorno de ejemplo
├── entrypoint.sh          # Script de inicialización
├── setup_nextcloud_folders.sh  # Script para crear carpetas
├── setup.sh              # Script de configuración automática
├── README.md             # Esta documentación
├── data/                 # Datos de Nextcloud (creado automáticamente)
├── config/               # Configuración de Nextcloud (creado automáticamente)
└── apps/                 # Aplicaciones personalizadas (creado automáticamente)
```

## 🛠️ Comandos Útiles

### Gestión de Servicios

```bash
# Iniciar servicios
docker-compose up -d

# Ver logs
docker-compose logs -f

# Parar servicios
docker-compose down

# Reiniciar servicios
docker-compose restart

# Ver estado de servicios
docker-compose ps
```

### Mantenimiento de Nextcloud

```bash
# Activar modo mantenimiento
docker-compose exec nextcloud php occ maintenance:mode --on

# Desactivar modo mantenimiento
docker-compose exec nextcloud php occ maintenance:mode --off

# Actualizar Nextcloud
docker-compose exec nextcloud php occ upgrade

# Limpiar cache
docker-compose exec nextcloud php occ maintenance:repair
```

### Backup y Restauración

```bash
# Backup de datos
docker-compose exec nextcloud php occ maintenance:mode --on
docker run --rm -v next_cloud_nextcloud_data:/data -v $(pwd)/backup:/backup alpine tar czf /backup/nextcloud-backup-$(date +%Y%m%d).tar.gz -C /data .

# Restaurar datos
docker run --rm -v next_cloud_nextcloud_data:/data -v $(pwd)/backup:/backup alpine tar xzf /backup/nextcloud-backup-YYYYMMDD.tar.gz -C /data
```

## 🔒 Seguridad

### Configuración Recomendada para Producción

1. **Cambiar contraseñas por defecto**
2. **Configurar HTTPS con certificados SSL**
3. **Configurar firewall** para limitar acceso
4. **Hacer backups regulares**
5. **Mantener actualizado** el sistema

### Configuración de Firewall (Ubuntu/Debian)

```bash
# Permitir solo puertos necesarios
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 22/tcp  # SSH
sudo ufw enable
```

## 🐛 Solución de Problemas

### Problemas Comunes

1. **Error de permisos**: Verificar que los directorios tengan permisos correctos
2. **Puerto en uso**: Cambiar puertos en docker-compose.yml
3. **Error de base de datos**: Verificar que PostgreSQL esté funcionando
4. **Error de dominio**: Configurar correctamente NEXTCLOUD_TRUSTED_DOMAINS

### Logs y Diagnóstico

```bash
# Ver logs de todos los servicios
docker-compose logs

# Ver logs de un servicio específico
docker-compose logs nextcloud
docker-compose logs postgres
docker-compose logs redis

# Verificar estado de servicios
docker-compose ps
```

## 📞 Soporte

Para problemas específicos:

1. Revisar logs: `docker-compose logs -f`
2. Verificar configuración en `.env`
3. Verificar que los puertos no estén en uso
4. Verificar conectividad de red entre servicios

## 🔄 Actualizaciones

Para actualizar Nextcloud:

```bash
# Parar servicios
docker-compose down

# Actualizar imágenes
docker-compose pull

# Iniciar servicios
docker-compose up -d

# Ejecutar actualización de Nextcloud
docker-compose exec nextcloud php occ upgrade
```
