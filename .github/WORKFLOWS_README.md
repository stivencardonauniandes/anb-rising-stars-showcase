a# 🚀 GitHub Actions Workflows - ANB Rising Stars Showcase

## 📋 Overview

Este proyecto incluye un conjunto completo de workflows de GitHub Actions para CI/CD, análisis de calidad de código, y despliegue automático.

## 🔧 Workflows Implementados

### 1. **CI - Tests and Coverage** (`.github/workflows/ci.yml`)

**Triggers**: Push y PR a `main`, `develop`

**Jobs**:
- ✅ **test**: Ejecuta tests con coverage en PostgreSQL + Redis
- ✅ **lint**: Análisis de calidad (Black, isort, Flake8, Bandit)
- ✅ **docker-test**: Tests de integración con Docker
- ✅ **security-scan**: Escaneo de vulnerabilidades con Safety
- ✅ **notify**: Resumen de resultados

**Artifacts generados**:
- Coverage reports (XML + HTML)
- Lint reports
- Security reports

### 2. **SonarQube Analysis** (`.github/workflows/sonarqube.yml`)

**Triggers**: Push y PR a `main`, `develop`

**Jobs**:
- ✅ **sonarqube**: Análisis completo de calidad de código
- ✅ **sonarqube-pr-decoration**: Decoración de PRs con resultados

**Métricas analizadas**:
- 📊 Code coverage
- 🐛 Code smells
- 🔒 Security hotspots
- 🏗️ Technical debt
- 🔍 Duplicated code

### 3. **Test Validation** (`.github/workflows/test-validation.yml`)

**Triggers**: Push, PR, schedule (daily), manual

**Jobs**:
- ✅ **test-matrix**: Tests en Python 3.9, 3.10, 3.11, 3.12
- ✅ **integration-test**: Tests de integración end-to-end
- ✅ **performance-test**: Tests básicos de rendimiento
- ✅ **test-summary**: Resumen consolidado

### 4. **Release and Deploy** (`.github/workflows/release.yml`)

**Triggers**: Tags `v*.*.*`, releases, manual

**Jobs**:
- ✅ **validate-release**: Validación completa pre-release
- ✅ **build-docker**: Build de imágenes Docker multi-arch
- ✅ **security-audit**: Auditoría de seguridad (Safety, Bandit, Semgrep)
- ✅ **sonarqube-release**: Análisis SonarQube para release
- ✅ **create-release**: Creación automática de GitHub Release
- ✅ **deploy-staging**: Despliegue a staging
- ✅ **notify-release**: Notificaciones de release

## 🔐 Secrets Requeridos

### Para SonarQube:
```bash
SONAR_TOKEN=your_sonarqube_token
SONAR_HOST_URL=https://your-sonarqube-instance.com
```

### Para Docker Registry (opcional):
```bash
DOCKER_USERNAME=your_docker_username
DOCKER_PASSWORD=your_docker_password
```

### Para despliegues (opcional):
```bash
STAGING_HOST=your_staging_server
STAGING_USER=deploy_user
STAGING_KEY=your_ssh_private_key
```

## 📊 SonarQube Configuration

### Archivo: `sonar-project.properties`

**Configuración incluida**:
- 📁 Source y test directories
- 🚫 Exclusiones (migrations, cache, etc.)
- 📈 Coverage reports paths
- 🎯 Quality gate settings
- 🔍 Analysis parameters

**Métricas configuradas**:
- Coverage threshold: 80%
- Maintainability rating: A-D scale
- Reliability rating: Bug-based scale
- Security rating: Vulnerability-based scale

## 🎯 Quality Gates

### SonarQube Quality Gate:
- ✅ Coverage > 80%
- ✅ 0 Bugs
- ✅ 0 Vulnerabilities
- ✅ Security Rating = A
- ✅ Maintainability Rating ≤ B
- ✅ Duplicated Lines < 3%

### CI Quality Checks:
- ✅ All tests must pass
- ✅ Security scan must pass
- ✅ Docker build must succeed
- ✅ Code formatting (Black)
- ✅ Import sorting (isort)
- ✅ Linting (Flake8)

## 🚀 Como Usar

### 1. Configurar SonarQube

```bash
# 1. Crear proyecto en SonarQube
# 2. Obtener token de proyecto
# 3. Agregar secrets a GitHub:
#    - SONAR_TOKEN
#    - SONAR_HOST_URL
```

### 2. Configurar Variables de Entorno

```bash
# En GitHub Settings > Secrets and variables > Actions
SONAR_TOKEN=sqp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
SONAR_HOST_URL=https://sonarcloud.io
```

### 3. Trigger Workflows

```bash
# CI automático en push/PR
git push origin main

# Release manual
git tag v1.0.0
git push origin v1.0.0

# Workflow manual
gh workflow run test-validation.yml
```

### 4. Ver Resultados

- **GitHub Actions**: https://github.com/your-repo/actions
- **SonarQube**: Your SonarQube instance
- **Artifacts**: Descargables desde workflow runs
- **Coverage**: HTML reports en artifacts

## 📈 Badges para README

```markdown
![CI](https://github.com/your-org/anb-rising-stars-showcase/workflows/CI%20-%20Tests%20and%20Coverage/badge.svg)
![SonarQube](https://github.com/your-org/anb-rising-stars-showcase/workflows/SonarQube%20Analysis/badge.svg)
![Tests](https://github.com/your-org/anb-rising-stars-showcase/workflows/Test%20Validation/badge.svg)

[![Quality Gate Status](https://your-sonarqube.com/api/project_badges/measure?project=anb-rising-stars-showcase&metric=alert_status)](https://your-sonarqube.com/dashboard?id=anb-rising-stars-showcase)
[![Coverage](https://your-sonarqube.com/api/project_badges/measure?project=anb-rising-stars-showcase&metric=coverage)](https://your-sonarqube.com/dashboard?id=anb-rising-stars-showcase)
[![Security Rating](https://your-sonarqube.com/api/project_badges/measure?project=anb-rising-stars-showcase&metric=security_rating)](https://your-sonarqube.com/dashboard?id=anb-rising-stars-showcase)
```

## 🛠️ Personalización

### Modificar thresholds de coverage:
```yaml
# En ci.yml, cambiar:
coverage report --fail-under=80  # Cambiar 80 por tu threshold
```

### Agregar más versiones de Python:
```yaml
# En test-validation.yml:
strategy:
  matrix:
    python-version: ['3.9', '3.10', '3.11', '3.12', '3.13']  # Agregar versiones
```

### Customizar SonarQube rules:
```properties
# En sonar-project.properties:
sonar.coverage.exclusions=**/tests/**,**/migrations/**,**/your-exclusions/**
```

## 🐛 Troubleshooting

### Common Issues:

1. **SonarQube connection failed**:
   - Verificar SONAR_TOKEN y SONAR_HOST_URL
   - Verificar que el proyecto existe en SonarQube

2. **Tests failing in CI**:
   - Verificar que las variables de entorno están configuradas
   - Verificar que los servicios (PostgreSQL, Redis) están corriendo

3. **Coverage too low**:
   - Revisar archivos excluidos en `.coveragerc`
   - Agregar más tests o ajustar threshold

4. **Docker build failing**:
   - Verificar que el Dockerfile es válido
   - Verificar que las dependencias están correctas

## 📞 Support

Para issues específicos con workflows:
1. Revisar logs de GitHub Actions
2. Verificar configuración de SonarQube
3. Validar secrets y variables de entorno
4. Consultar documentación de herramientas específicas

¡Los workflows están listos para usar! 🎉
