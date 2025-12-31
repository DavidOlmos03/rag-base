# Configuración de Ollama para Docker

Este documento describe la configuración necesaria para que Ollama funcione correctamente con la aplicación RAG Base cuando se ejecuta en contenedores Docker, especialmente en sistemas Linux.

## Problema común

Por defecto, Ollama escucha solo en `localhost` (127.0.0.1), lo que impide que los contenedores Docker puedan conectarse al servicio. Además, en Linux, `host.docker.internal` no está disponible de forma nativa como en Mac/Windows.

### Síntomas del error

Si ves este error al intentar hacer queries:

```json
{
  "detail": "Query failed: Ollama HTTP error: [Errno -2] Name or service not known"
}
```

Significa que el contenedor no puede conectarse a Ollama en el host.

## Solución

La solución requiere dos cambios:

### 1. Configurar Docker Compose para Linux

En `docker-compose.dev.yml`, agregar `extra_hosts` al servicio `api` para que `host.docker.internal` resuelva correctamente:

```yaml
services:
  api:
    # ... otras configuraciones ...
    extra_hosts:
      - "host.docker.internal:host-gateway"
    depends_on:
      # ... resto de dependencias ...
```

Esto permite que el contenedor resuelva `host.docker.internal` a la IP del host (generalmente 172.17.0.1).

### 2. Configurar Ollama para escuchar en todas las interfaces

Ollama debe estar configurado para escuchar en `0.0.0.0` en lugar de solo `127.0.0.1`.

#### Editar el servicio systemd

```bash
sudo nano /etc/systemd/system/ollama.service
```

Agregar la siguiente línea en la sección `[Service]`:

```ini
Environment="OLLAMA_HOST=0.0.0.0"
```

El archivo debería verse así:

```ini
[Unit]
Description=Ollama Service
After=network-online.target

[Service]
ExecStart=/usr/local/bin/ollama serve
User=ollama
Group=ollama
Restart=always
RestartSec=3
Environment="PATH=..."
Environment="OLLAMA_HOST=0.0.0.0"

[Install]
WantedBy=default.target
```

#### Aplicar los cambios

```bash
# Recargar la configuración de systemd
sudo systemctl daemon-reload

# Reiniciar Ollama
sudo systemctl restart ollama

# Verificar que escucha en todas las interfaces
ss -tulpn | grep 11434
```

Deberías ver:
```
tcp   LISTEN 0      4096         *:11434            *:*
```

### 3. Reiniciar los contenedores Docker

```bash
docker-compose -f docker-compose.dev.yml down
docker-compose -f docker-compose.dev.yml up -d
```

## Verificación

Para verificar que la conexión funciona correctamente:

```bash
# 1. Verificar que Ollama está disponible en el host
curl http://localhost:11434/api/tags

# 2. Verificar que el contenedor puede conectarse
docker exec ragbase-api-dev curl http://host.docker.internal:11434/api/tags
```

Ambos comandos deberían devolver la lista de modelos disponibles, por ejemplo:

```json
{
  "models": [
    {
      "name": "phi3:mini",
      "model": "phi3:mini",
      ...
    }
  ]
}
```

## Configuración en docker-compose.dev.yml

La URL de Ollama se configura mediante la variable de entorno:

```yaml
environment:
  - OLLAMA_BASE_URL=http://host.docker.internal:11434
```

Esta configuración apunta al servicio Ollama corriendo en el host a través del gateway de Docker.

## Modelos disponibles

Para listar los modelos instalados en Ollama:

```bash
ollama list
```

Para descargar un nuevo modelo:

```bash
ollama pull <modelo>
# Ejemplo:
ollama pull phi3:mini
ollama pull llama2
```

## Seguridad

**Importante**: Configurar Ollama para escuchar en `0.0.0.0` expone el servicio a toda la red local. Si esto es una preocupación de seguridad:

1. Considera usar un firewall para restringir el acceso al puerto 11434
2. O usa la opción alternativa de ejecutar Ollama dentro de Docker (ver docker-compose.dev.yml líneas 87-99)

## Alternativa: Ollama dentro de Docker

Si prefieres ejecutar Ollama completamente dentro de Docker, descomenta el servicio `ollama` en `docker-compose.dev.yml` y cambia la URL:

```yaml
environment:
  - OLLAMA_BASE_URL=http://ollama:11434
```

**Nota**: Esta opción consume más recursos pero mantiene todo contenido dentro del stack de Docker.
