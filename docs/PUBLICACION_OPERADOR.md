# Publicación y entrega - guía del operador

Preparada el 2026-11-07. No implica aprobación de fases ni despliegue ejecutado.
Ejecutar desde la raíz del proyecto; detenerse ante cualquier error.

## 1. Antes de publicar

Rotar y revocar la clave que se expuso en el chat. Crear una clave de proyecto
nueva y configurar el límite de USD 20 en Anthropic. No pegar claves en chat,
archivos versionados ni comandos que queden en el historial. Configurar los
secretos directamente en Settings / Config Vars del dashboard de Heroku.

Resolver las métricas pendientes de `MEJORA_PROMPTS.md` antes de aprobar F5.
Verificar disponibilidad del modelo configurado en la cuenta; no se ha probado
una nueva llamada pagada en esta revisión.

## 2. Validación local

```powershell
Set-Location backend
uv run --python 3.12 --extra dev pytest -q
uv run --python 3.12 --extra dev ruff check .
Set-Location ..
docker build -t karin .
```

El daemon de Docker no estaba disponible al revisar. El build y el arranque
siguen pendientes; no basta con que existan Dockerfile y heroku.yml.

Para probar la imagen, cargar secretos nuevos en el entorno del proceso sin
imprimirlos; pasar solo los nombres a Docker:

```powershell
docker run --rm -p 8000:8000 --env ANTHROPIC_API_KEY --env KARIN_SESSION_SECRET --env KARIN_DEMO_PASSWORD_ANALISTA --env KARIN_DEMO_PASSWORD_SUPERVISOR karin
```

## 3. Primer commit y GitHub público

Trabajar en una rama propia. El repositorio no tiene commits ni remoto.
Antes de agregar archivos, revisar especialmente documentos de equipo y fuentes
para excluir información personal y material no autorizado para publicación.
No agregar `.env`, bases locales ni corridas crudas.

```powershell
git switch --orphan entrega/codex-revision
git add .
git diff --cached --check
git diff --cached --stat
git diff --cached
git ls-files .env
```

La última orden no debe listar nada. Complementar con escáner de secretos sobre
el contenido preparado; no basta con buscar un único prefijo. Tras revisión:

```powershell
git commit -m "Entrega inicial KARIN triage"
gh repo create agente-karin-triage --public --source . --remote origin --push
```

Abrir la URL de GitHub sin sesión y comprobar acceso a README, prompts,
golden set y evidencia. Usar un nombre alternativo si ya existe el repositorio.

## 4. Heroku: ejecutar por el operador

Costo base referencial confirmado en página de precios: Basic USD 7/mes más
Postgres Essential-0 USD 5/mes; inferencia adicional según consumo.

```powershell
heroku login
$karinApp = Read-Host 'Nombre único para la app Karin'
heroku create $karinApp --stack container
heroku addons:create heroku-postgresql:essential-0 --app $karinApp
```

En el dashboard configurar ANTHROPIC_API_KEY, KARIN_SESSION_SECRET,
KARIN_DEMO_PASSWORD_ANALISTA y KARIN_DEMO_PASSWORD_SUPERVISOR. Usar valores
distintos y aleatorios; guardar las contraseñas de evaluación en la plataforma
del curso. DATABASE_URL la aporta Postgres. Configurar KARIN_TOPE_USD_DIA=3 y
KARIN_TOPE_LLAMADAS_DIA=200, o límites inferiores acordados para la demo.

```powershell
git push heroku HEAD:main
heroku ps:resize web=basic --app $karinApp
heroku ps:scale web=1 --app $karinApp
heroku releases --app $karinApp
heroku open --app $karinApp
```

El release de heroku.yml ejecuta Alembic antes de arrancar. Ante un fallo,
revisar los logs localmente sin copiarlos a un repositorio público.

## 5. Evidencia de aceptación y comunicación

- Abrir en incógnito; entrar como analista; cargar únicamente un caso sintético.
- Ver propuesta generada con IA activa, citas y reglas; corregir y volver a
  abrir para comprobar persistencia de la revisión.
- Probar supervisor y doble revisión de un descarte con usuarios distintos.
- Registrar URL y fecha de comprobación en README; no declarar probado el flujo
  hasta ejecutarlo realmente. Confirmar gasto y límite en consola del proveedor.
- Grabar video de máximo tres minutos con `docs/GUION_VIDEO.md`, sin mostrar
  secretos; entregar su enlace y `docs/FICHA_NEGOCIO.pdf` en la plataforma.
- Comprobar los cuatro entregables desde una sesión externa antes del 13/11,
  23:59. La nota final corresponde al profesor; no prometer una nota proyectada.

Fuentes verificadas para esta guía:

- https://www.heroku.com/pricing/
- https://devcenter.heroku.com/articles/build-docker-images-heroku-yml

Pendientes: rotación de clave, corrección y nueva medición de evals, build y
arranque Docker, revisión de secretos y datos personales, commit y GitHub,
despliegue y aceptación externa, grabación del video. Ninguna fase se declara
cerrada por la existencia de esta guía.
