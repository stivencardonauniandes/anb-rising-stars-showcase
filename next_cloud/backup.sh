#!/bin/bash

# Script de backup para Nextcloud independiente
# Este script crea backups automáticos de datos y configuración

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para imprimir mensajes con color
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Configuración
BACKUP_DIR="./backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="nextcloud-backup-${DATE}"

# Crear directorio de backup si no existe
create_backup_dir() {
    if [ ! -d "$BACKUP_DIR" ]; then
        print_status "Creando directorio de backup: $BACKUP_DIR"
        mkdir -p "$BACKUP_DIR"
    fi
}

# Activar modo mantenimiento
enable_maintenance_mode() {
    print_status "Activando modo mantenimiento..."
    docker-compose exec -T nextcloud php occ maintenance:mode --on
    print_success "Modo mantenimiento activado"
}

# Desactivar modo mantenimiento
disable_maintenance_mode() {
    print_status "Desactivando modo mantenimiento..."
    docker-compose exec -T nextcloud php occ maintenance:mode --off
    print_success "Modo mantenimiento desactivado"
}

# Backup de datos de Nextcloud
backup_nextcloud_data() {
    print_status "Creando backup de datos de Nextcloud..."
    
    # Crear directorio de backup específico
    mkdir -p "${BACKUP_DIR}/${BACKUP_NAME}"
    
    # Backup de datos
    docker run --rm \
        -v next_cloud_nextcloud_data:/data \
        -v "$(pwd)/${BACKUP_DIR}/${BACKUP_NAME}:/backup" \
        alpine tar czf /backup/nextcloud-data.tar.gz -C /data .
    
    print_success "Backup de datos completado"
}

# Backup de configuración
backup_config() {
    print_status "Creando backup de configuración..."
    
    # Backup de archivos de configuración
    tar czf "${BACKUP_DIR}/${BACKUP_NAME}/config.tar.gz" \
        docker-compose.yml \
        .env \
        entrypoint.sh \
        setup_nextcloud_folders.sh \
        setup.sh \
        backup.sh \
        README.md
    
    print_success "Backup de configuración completado"
}

# Backup de base de datos
backup_database() {
    print_status "Creando backup de base de datos..."
    
    # Crear backup de PostgreSQL
    docker-compose exec -T postgres pg_dump -U nextcloud nextcloud > "${BACKUP_DIR}/${BACKUP_NAME}/database.sql"
    
    print_success "Backup de base de datos completado"
}

# Limpiar backups antiguos
cleanup_old_backups() {
    print_status "Limpiando backups antiguos (más de 7 días)..."
    
    find "$BACKUP_DIR" -type d -name "nextcloud-backup-*" -mtime +7 -exec rm -rf {} \; 2>/dev/null || true
    
    print_success "Limpieza de backups antiguos completada"
}

# Verificar integridad del backup
verify_backup() {
    print_status "Verificando integridad del backup..."
    
    if [ -f "${BACKUP_DIR}/${BACKUP_NAME}/nextcloud-data.tar.gz" ] && \
       [ -f "${BACKUP_DIR}/${BACKUP_NAME}/config.tar.gz" ] && \
       [ -f "${BACKUP_DIR}/${BACKUP_NAME}/database.sql" ]; then
        print_success "Backup verificado correctamente"
        return 0
    else
        print_error "Error en la verificación del backup"
        return 1
    fi
}

# Mostrar información del backup
show_backup_info() {
    print_success "🎉 Backup completado exitosamente!"
    echo ""
    echo "📁 Ubicación del backup: ${BACKUP_DIR}/${BACKUP_NAME}/"
    echo "📊 Contenido del backup:"
    echo "  • nextcloud-data.tar.gz (datos de Nextcloud)"
    echo "  • config.tar.gz (archivos de configuración)"
    echo "  • database.sql (base de datos PostgreSQL)"
    echo ""
    echo "💾 Tamaño del backup:"
    du -sh "${BACKUP_DIR}/${BACKUP_NAME}"
    echo ""
    echo "🔄 Para restaurar:"
    echo "  ./restore.sh ${BACKUP_NAME}"
}

# Función principal
main() {
    echo "💾 Backup de Nextcloud Independiente"
    echo "===================================="
    echo ""
    
    # Verificar que Docker Compose esté ejecutándose
    if ! docker-compose ps | grep -q "Up"; then
        print_error "Los servicios de Nextcloud no están ejecutándose"
        print_error "Ejecuta 'docker-compose up -d' primero"
        exit 1
    fi
    
    create_backup_dir
    enable_maintenance_mode
    
    # Crear backups
    backup_nextcloud_data
    backup_config
    backup_database
    
    disable_maintenance_mode
    
    # Verificar y limpiar
    if verify_backup; then
        cleanup_old_backups
        show_backup_info
    else
        print_error "El backup falló la verificación"
        exit 1
    fi
}

# Ejecutar función principal
main "$@"
