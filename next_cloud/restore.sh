#!/bin/bash

# Script de restauración para Nextcloud independiente
# Este script restaura backups creados con backup.sh

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

# Verificar argumentos
check_arguments() {
    if [ $# -eq 0 ]; then
        print_error "Uso: $0 <nombre-del-backup>"
        echo ""
        echo "Backups disponibles:"
        ls -la "$BACKUP_DIR" 2>/dev/null | grep "nextcloud-backup-" || echo "  No hay backups disponibles"
        exit 1
    fi
    
    BACKUP_NAME="$1"
    BACKUP_PATH="${BACKUP_DIR}/${BACKUP_NAME}"
    
    if [ ! -d "$BACKUP_PATH" ]; then
        print_error "Backup no encontrado: $BACKUP_PATH"
        echo ""
        echo "Backups disponibles:"
        ls -la "$BACKUP_DIR" 2>/dev/null | grep "nextcloud-backup-" || echo "  No hay backups disponibles"
        exit 1
    fi
}

# Verificar archivos de backup
verify_backup_files() {
    print_status "Verificando archivos de backup..."
    
    if [ ! -f "${BACKUP_PATH}/nextcloud-data.tar.gz" ]; then
        print_error "Archivo de datos no encontrado: nextcloud-data.tar.gz"
        exit 1
    fi
    
    if [ ! -f "${BACKUP_PATH}/config.tar.gz" ]; then
        print_error "Archivo de configuración no encontrado: config.tar.gz"
        exit 1
    fi
    
    if [ ! -f "${BACKUP_PATH}/database.sql" ]; then
        print_error "Archivo de base de datos no encontrado: database.sql"
        exit 1
    fi
    
    print_success "Archivos de backup verificados"
}

# Parar servicios
stop_services() {
    print_status "Parando servicios de Nextcloud..."
    docker-compose down
    print_success "Servicios parados"
}

# Restaurar datos de Nextcloud
restore_nextcloud_data() {
    print_status "Restaurando datos de Nextcloud..."
    
    # Crear volumen temporal para la restauración
    docker volume create next_cloud_nextcloud_data_temp
    
    # Restaurar datos
    docker run --rm \
        -v next_cloud_nextcloud_data_temp:/data \
        -v "$(pwd)/${BACKUP_PATH}:/backup" \
        alpine tar xzf /backup/nextcloud-data.tar.gz -C /data
    
    print_success "Datos de Nextcloud restaurados"
}

# Restaurar configuración
restore_config() {
    print_status "Restaurando configuración..."
    
    # Extraer archivos de configuración
    tar xzf "${BACKUP_PATH}/config.tar.gz"
    
    print_success "Configuración restaurada"
}

# Restaurar base de datos
restore_database() {
    print_status "Restaurando base de datos..."
    
    # Iniciar solo PostgreSQL
    docker-compose up -d postgres
    
    # Esperar a que PostgreSQL esté listo
    print_status "Esperando a que PostgreSQL esté listo..."
    sleep 10
    
    # Restaurar base de datos
    docker-compose exec -T postgres psql -U nextcloud -d nextcloud < "${BACKUP_PATH}/database.sql"
    
    print_success "Base de datos restaurada"
}

# Reemplazar volumen de datos
replace_data_volume() {
    print_status "Reemplazando volumen de datos..."
    
    # Parar PostgreSQL
    docker-compose stop postgres
    
    # Eliminar volumen original
    docker volume rm next_cloud_nextcloud_data 2>/dev/null || true
    
    # Renombrar volumen temporal
    docker volume rm next_cloud_nextcloud_data 2>/dev/null || true
    docker run --rm -v next_cloud_nextcloud_data_temp:/source -v next_cloud_nextcloud_data:/dest alpine sh -c "cp -a /source/. /dest/"
    docker volume rm next_cloud_nextcloud_data_temp
    
    print_success "Volumen de datos reemplazado"
}

# Iniciar servicios
start_services() {
    print_status "Iniciando servicios..."
    docker-compose up -d
    
    # Esperar a que los servicios estén listos
    print_status "Esperando a que los servicios estén listos..."
    sleep 30
    
    print_success "Servicios iniciados"
}

# Verificar restauración
verify_restoration() {
    print_status "Verificando restauración..."
    
    # Verificar que Nextcloud esté funcionando
    if curl -f http://localhost:8080/status.php > /dev/null 2>&1; then
        print_success "Nextcloud está funcionando correctamente"
    else
        print_warning "Nextcloud puede no estar completamente listo aún"
    fi
}

# Mostrar información de restauración
show_restoration_info() {
    print_success "🎉 Restauración completada exitosamente!"
    echo ""
    echo "📋 Información de acceso:"
    echo "  • Nextcloud: http://34.229.110.180:8080"
    echo "  • Adminer: http://34.229.110.180:8081"
    echo ""
    echo "🔧 Comandos útiles:"
    echo "  • Ver logs: docker-compose logs -f"
    echo "  • Verificar estado: docker-compose ps"
    echo "  • Reparar si es necesario: docker-compose exec nextcloud php occ maintenance:repair"
    echo ""
    print_warning "⚠️  Verifica que todos los servicios estén funcionando correctamente"
}

# Función principal
main() {
    echo "🔄 Restauración de Nextcloud Independiente"
    echo "=========================================="
    echo ""
    
    check_arguments "$@"
    verify_backup_files
    
    print_warning "⚠️  ADVERTENCIA: Esta operación reemplazará todos los datos actuales"
    print_warning "⚠️  Asegúrate de hacer un backup antes de continuar"
    echo ""
    print_status "¿Deseas continuar con la restauración? (y/N)"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        print_status "Restauración cancelada"
        exit 0
    fi
    
    stop_services
    restore_nextcloud_data
    restore_config
    restore_database
    replace_data_volume
    start_services
    verify_restoration
    show_restoration_info
}

# Ejecutar función principal
main "$@"
