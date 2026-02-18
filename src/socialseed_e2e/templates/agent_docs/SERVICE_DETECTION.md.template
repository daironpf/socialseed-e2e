# 🔍 Detección Automática de Servicios y Puertos

> **IMPORTANTE**: Este documento es OBLIGATORIO leerlo antes de generar cualquier test E2E.

## 🎯 Propósito

Como agente de IA, **DEBES** detectar automáticamente dónde está corriendo el servicio antes de crear los tests. **NUNCA** asumas el puerto o la URL.

---

## 📋 Flujo de Detección Obligatorio

### Paso 1: Detectar Puerto desde Código Fuente

Busca en los archivos de configuración del proyecto:

```bash
# Para proyectos Java/Spring Boot
grep -r "port" services/<service-name>/src/main/resources/*.yml
grep -r "port" services/<service-name>/src/main/resources/*.properties

# Para proyectos Node.js
grep -r "PORT" services/<service-name>/.env
grep -r "port" services/<service-name>/config/*

# Para Docker Compose
grep -r "ports" docker-compose.yml
```

**Ubicaciones comunes:**
- `application.yml` / `application.properties`
- `application-dev.yml` / `application-prod.yml`
- `docker-compose.yml`
- `.env` files
- `Dockerfile` (EXPOSE statements)

### Paso 2: Verificar Servicio Activo

Usa el comando `observe` del framework:

```bash
e2e observe --host localhost --ports 8080-8090
```

O directamente con curl:

```bash
# Intenta health endpoints comunes
curl -s http://localhost:8080/actuator/health
curl -s http://localhost:8085/actuator/health
curl -s http://localhost:8080/health
curl -s http://localhost:8080/healthz
```

### Paso 3: Detectar Contenedores Docker

```bash
# Ver contenedores activos
docker ps --format "table {{.Names}}\t{{.Ports}}\t{{.Status}}"

# Ver puertos expuestos
docker ps --format "{{.Names}}: {{.Ports}}"
```

### Paso 4: Detectar Procesos Locales

```bash
# Linux/Mac
lsof -i :8080-8090

# O con netstat
netstat -tuln | grep LISTEN | grep -E "808[0-9]"
```

---

## 🔧 Puertos Comunes por Tecnología

| Tecnología | Puertos Típicos |
|------------|-----------------|
| Spring Boot | 8080, 8081, 8082, 8085, 8090 |
| Node.js/Express | 3000, 3001, 4000, 5000 |
| Flask/Python | 5000, 5001, 8000 |
| gRPC | 50051, 50052, 50053 |
| Docker (mapeado) | 8000-9000 |

---

## 📝 Ejemplo Completo de Detección

```bash
# 1. Buscar en configuración
$ grep "port" ../services/auth-service/src/main/resources/application*.yml
server:
  port: 8085

# 2. Verificar que está activo
$ curl -s http://localhost:8085/actuator/health
{"status":"UP"}

# 3. Usar el puerto detectado en e2e.conf
auth_service:
  base_url: http://localhost:8085
  health_endpoint: /actuator/health
```

---

## ⚠️ ERRORES COMUNES

### Error 1: Asumir puerto 8080

```python
# ❌ MAL - Asumir puerto sin verificar
base_url: http://localhost:8080

# ✅ BIEN - Verificar primero
# Ejecutar: grep "port" application.yml
# Resultado: port: 8085
base_url: http://localhost:8085
```

### Error 2: No verificar que el servicio está corriendo

```bash
# ❌ MAL - Crear tests sin verificar
# Los tests fallarán con ECONNREFUSED

# ✅ BIEN - Verificar primero
curl http://localhost:8085/actuator/health
# Si responde, proceder con los tests
```

### Error 3: Ignorar Docker

```bash
# ❌ MAL - Ignorar contenedores Docker

# ✅ BIEN - Verificar Docker
docker ps
# Si el servicio está en Docker, usar el puerto mapeado
```

---

## 🚀 Checklist Pre-Generación

Antes de generar tests, verifica:

- [ ] Busqué el puerto en `application.yml` o `.properties`
- [ ] Ejecuté `e2e observe` o `curl` para verificar el servicio
- [ ] Revisé contenedores Docker con `docker ps`
- [ ] Actualicé `e2e.conf` con el puerto correcto
- [ ] Verifiqué el health endpoint responde

---

## 📖 Comandos Útiles

```bash
# Detección completa con el framework
e2e observe --host localhost --ports 8000-9000 --docker

# Ver solo puertos abiertos
lsof -i -P | grep LISTEN

# Ver configuración de un servicio específico
cat services/auth-service/src/main/resources/application.yml | grep -A 2 "server:"

# Probar múltiples puertos rápidamente
for port in 8080 8081 8085 8090; do
  echo "Testing port $port..."
  curl -s -o /dev/null -w "%{http_code}" http://localhost:$port/actuator/health
  echo ""
done

# ⭐ CONFIGURAR URL REMOTA (AWS, Azure, GCP, etc.)
e2e set url auth_service https://my-api.azurewebsites.net
e2e set url payment_service https://my-api.execute-api.us-east-1.amazonaws.com
e2e set url auth_service https://api.example.com:443 --health-endpoint /health

# Ver configuración actual
e2e set show
e2e set show auth_service
```

---

## 🎯 Template de Detección para Agentes

Cuando generes tests para un nuevo servicio, sigue ESTE ORDEN:

```python
# 1. DETECTAR puerto desde código
# Ejecutar: grep "port" ../services/<service>/src/main/resources/application*.yml

# 2. VERIFICAR servicio activo
# Ejecutar: curl http://localhost:<detected_port>/actuator/health

# 3. CONFIGURAR e2e.conf
# services:
#   <service_name>:
#     base_url: http://localhost:<detected_port>
#     health_endpoint: /actuator/health

# 4. CREAR tests con la URL correcta
```

---

**Versión:** 1.0
**Última actualización:** 2026-02-17
**Framework:** socialseed-e2e v0.1.0+
