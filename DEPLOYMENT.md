# Despliegue de Clínica+ con Docker

El despliegue de producción es independiente del desarrollo. La aplicación usa
PostgreSQL en todos los entornos: `config.development` para desarrollo y
`config.production` para producción. La URL de inicio se conserva. El contenedor
usa PostgreSQL y el mismo acceso web:
`/clinica+/`. La raíz `/` conserva la redirección a `/clinica+/`, donde se
presenta la página de acceso.

## Archivos Compose por entorno

`compose.yml` contiene la configuración común de la aplicación. Los archivos
`compose.dev.yml` y `compose.prod.yml` aplican únicamente los ajustes propios
de desarrollo o producción. Los entornos tienen proyectos, puertos y bases
independientes. El Compose de desarrollo usa PostgreSQL en un volumen propio
y publica la base solo en `127.0.0.1:5433` para conectarse con DBeaver u otra
herramienta instalada en la notebook.

## Probar en la notebook

El Compose de desarrollo monta el código local y publica el servidor de
recarga en `localhost:8084`. Usa PostgreSQL local del Compose, distinto de
PostgreSQL de producción:

```powershell
docker compose -p clinica-dev -f compose.yml -f compose.dev.yml up --build -d
```

Abrí `http://localhost:8084/clinica+/`. Los cambios de código se reflejan al
guardar. Para comprobar el estado o revisar el motivo de un error:

```powershell
docker compose -p clinica-dev -f compose.yml -f compose.dev.yml ps
docker compose -p clinica-dev -f compose.yml -f compose.dev.yml logs --tail 100 web
```

Al iniciar, Django aplica las migraciones a PostgreSQL. La carpeta `media` y
la base PostgreSQL usan volúmenes Docker persistentes.

## Conectar una herramienta gráfica a PostgreSQL de desarrollo

Con el stack de desarrollo activo, usá estos datos en DBeaver:

- Host: `127.0.0.1`
- Puerto: `5433`
- Base de datos: `clinica`
- Usuario: `clinica`
- Contraseña: la definida para PostgreSQL de desarrollo en `compose.dev.yml`

La contraseña es solo para la base aislada de desarrollo, cuyo puerto se
publica exclusivamente en loopback. Nunca reutilizarla en producción.

## Configurar módulos y usuarios

Los módulos externos se administran desde **Inicio → Configuración → Módulos**:
se registra el nombre y un enlace HTTP/HTTPS, y luego se asigna a cada cuenta
desde **Configuración → Usuarios**. Los módulos, sus enlaces y las asignaciones
se guardan en PostgreSQL. La baja de un usuario o de un módulo es reversible y
no elimina sus registros. La autorización dentro de un sistema externo debe
seguir validándose en ese sistema.

Para verificar la base configurada en el contenedor:

```powershell
docker exec conetia-clinica python manage.py shell -c "from django.conf import settings; print(settings.DATABASES['default']['ENGINE'], settings.DATABASES['default']['NAME'])"
```

Para cambiar la contraseña de un superusuario sin mostrar la contraseña
existente:

```powershell
docker exec -it conetia-clinica python manage.py changepassword admin
```

## Migrar la base SQLite de desarrollo

En esta notebook se completó la migración inicial de SQLite a PostgreSQL de
desarrollo. Se conservó la SQLite original y se creó el respaldo consistente
`D:\desarrollos\Clinica+_backups\db.sqlite3-pre-postgres-20261102-1213.sqlite3`.
La verificación encontró 99.350 pacientes, 99.350 expedientes físicos, 3
préstamos, 4 usuarios, 3 membresías, 1 organización y 3 impresoras tanto en
origen como en destino. Los pacientes quedaron vinculados a sus expedientes.

Para repetir la migración en otra instalación, usá una copia de seguridad
previa y detené los servicios que escriben en SQLite durante la exportación.
La SQLite original no se debe eliminar ni sobrescribir. El flujo es:

1. Hacer una copia consistente de `db.sqlite3` con la API `sqlite3.Connection.backup`.
2. Exportar los datos desde SQLite con `manage.py dumpdata`, excluyendo
   contenttypes, permisos generados, sesiones y registros de administración.
3. Levantar la base de desarrollo PostgreSQL y ejecutar `migrate`.
4. Importar el fixture con `loaddata`, restablecer las secuencias y comparar
   conteos y relaciones con SQLite.
5. Conservar SQLite y su respaldo hasta validar la aplicación usando PostgreSQL.

No ejecutar `docker compose down -v` para cambiar la base: eso borraría los
volúmenes persistentes de PostgreSQL.

## Preparar el servidor

Se requiere Docker Engine con Docker Compose y una copia del código fuente. En
la carpeta del proyecto:

1. Copiar `.env.production.example` como `.env.production`.
2. Establecer un `DJANGO_SECRET_KEY` y `POSTGRES_PASSWORD` fuertes y únicos.
   No guardar `.env.production` en el repositorio ni compartir esos secretos.
3. Configurar `DJANGO_ALLOWED_HOSTS` con los nombres DNS usados para acceder.
   `DJANGO_CSRF_TRUSTED_ORIGINS` debe incluir los orígenes completos, incluido
   el esquema, por ejemplo `https://conetia.sistemas.com`.
4. Configurar HTTPS antes de exponer el servicio fuera de un entorno confiable.
   Con un proxy TLS de confianza delante de este stack, establecer
   `DJANGO_HTTPS=true`; el proxy de este stack enviará el indicador HTTPS a
   Django. En ese caso, el proxy frontal debe permitir acceso únicamente desde
   la red de confianza y conservar el host público.
5. Arrancar el stack:

   ```powershell
   docker compose --env-file .env.production -p clinica-prod -f compose.yml -f compose.prod.yml up --build -d
   ```

Con los valores locales del ejemplo, se puede abrir
`http://localhost:8083/clinica+/`. Para probar el nombre configurado, el DNS o
el archivo hosts del cliente debe resolver `conetia.sistemas.com` hacia el
servidor. En una instalación real se recomienda terminar HTTPS en un proxy
frontal y limitar el puerto publicado de este stack a ese proxy.

La aplicación inicia con Gunicorn, ejecuta migraciones y recopila los archivos
estáticos. PostgreSQL, archivos estáticos y archivos subidos se guardan en
volúmenes Docker persistentes. Para consultar el estado:

```powershell
docker compose --env-file .env.production -p clinica-prod -f compose.yml -f compose.prod.yml ps
docker compose --env-file .env.production -p clinica-prod -f compose.yml -f compose.prod.yml logs -f web
```

El despliegue inicial crea una base PostgreSQL vacía; **no importa ni modifica
la base SQLite de desarrollo**. La migración de datos existentes debe
planificarse y respaldarse antes de habilitar el sistema productivo. No escalar
el servicio `web` por encima de una instancia mientras las migraciones se
ejecuten en el arranque.

## Impresión de pulseras

El contenedor Linux no puede usar directamente las impresoras USB ni la API
Windows `winspool` implementada actualmente por el módulo de impresión. La
pantalla y el resto del sistema pueden desplegarse, pero la impresión física
requiere un servicio/agente de impresión accesible para producción o un cambio
separado del mecanismo de impresión. Este paquete no altera ni reemplaza la
impresión del entorno de desarrollo.
