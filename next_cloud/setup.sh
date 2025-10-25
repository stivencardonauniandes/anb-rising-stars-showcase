#!/bin/bash

# Script de configuración inicial para Nextcloud independiente
# Este script configura y despliega Nextcloud en un servidor independiente

set -e

echo "🚀 Configurando Nextcloud para servidor independiente..."

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

# Verificar si Docker está instalado
check_docker() {
    print_status "Verificando instalación de Docker..."
    if ! command -v docker &> /dev/null; then
        print_error "Docker no está instalado. Por favor instala Docker primero."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose no está instalado. Por favor instala Docker Compose primero."
        exit 1
    fi
    
    print_success "Docker y Docker Compose están instalados"
}

# Crear archivo .env si no existe
create_env_file() {
    if [ ! -f .env ]; then
        print_status "Creando archivo .env desde env.example..."
        cp env.example .env
        print_warning "Archivo .env creado. Por favor edita las variables según tu configuración."
        print_warning "Especialmente importante: NEXTCLOUD_TRUSTED_DOMAINS, OVERWRITEHOST, OVERWRITEPROTOCOL"
    else
        print_status "Archivo .env ya existe"
    fi
}

# Crear directorios necesarios
create_directories() {
    print_status "Creando directorios necesarios..."
    mkdir -p data config apps
    chmod 755 data config apps
    print_success "Directorios creados"
}

# Configurar permisos
setup_permissions() {
    print_status "Configurando permisos..."
    chmod +x entrypoint.sh
    chmod +x setup_nextcloud_folders.sh
    chmod +x setup.sh
    print_success "Permisos configurados"
}

# Verificar configuración de red
check_network_config() {
    print_status "Verificando configuración de red..."
    
    # Verificar si el puerto 8080 está disponible
    if lsof -Pi :8080 -sTCP:LISTEN -t >/dev/null 2>&1; then
        print_warning "Puerto 8080 está en uso. Nextcloud usará este puerto."
        print_warning "Si hay conflictos, puedes cambiar el puerto en docker-compose.yml"
    fi
    
    # Verificar si el puerto 6379 está disponible (Redis)
    if lsof -Pi :6379 -sTCP:LISTEN -t >/dev/null 2>&1; then
        print_warning "Puerto 6379 está en uso. Redis usará este puerto."
        print_warning "Si hay conflictos, puedes cambiar el puerto en docker-compose.yml"
    fi
    
    print_status "Verificando conectividad con servidor PostgreSQL externo..."
    print_warning "Asegúrate de que el servidor PostgreSQL esté ejecutándose y accesible"
}

# Desplegar servicios
deploy_services() {
    print_status "Desplegando servicios de Nextcloud..."
    docker-compose up -d
    
    print_status "Esperando a que los servicios estén listos..."
    sleep 30
    
    # Verificar estado de los servicios
    if docker-compose ps | grep -q "Up"; then
        print_success "Servicios desplegados correctamente"
    else
        print_error "Error al desplegar servicios"
        docker-compose logs
        exit 1
    fi
}

# Mostrar información de acceso
show_access_info() {
    print_success "🎉 Nextcloud configurado exitosamente!"
    echo ""
    echo "📋 Información de acceso:"
    echo "  • Nextcloud: http://localhost:8080"
    echo "  • Adminer (DB): http://localhost:8081"
    echo ""
    echo "👤 Credenciales por defecto:"
    echo "  • Usuario admin: admin"
    echo "  • Contraseña: admin123"
    echo ""
    echo "🔧 Comandos útiles:"
    echo "  • Ver logs: docker-compose logs -f"
    echo "  • Parar servicios: docker-compose down"
    echo "  • Reiniciar: docker-compose restart"
    echo "  • Backup: docker-compose exec nextcloud php occ maintenance:mode --on"
    echo ""
    print_warning "⚠️  IMPORTANTE: Cambia las contraseñas por defecto en producción!"
}

# Función principal
main() {
    echo "🔧 Configuración de Nextcloud Independiente"
    echo "=========================================="
    echo ""
    
    check_docker
    create_env_file
    create_directories
    setup_permissions
    check_network_config
    
    echo ""
    print_status "¿Deseas continuar con el despliegue? (y/N)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        deploy_services
        show_access_info
    else
        print_status "Configuración completada. Ejecuta 'docker-compose up -d' cuando estés listo."
    fi
}

# Ejecutar función principal
main "$@"
