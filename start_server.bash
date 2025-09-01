set -euo pipefail

### === Конфиг (можно переопределять через переменные окружения) ===
IMAGE="${IMAGE:-persona_server}"          # образ API/worker
API_NAME="${API_NAME:-persona-api}"
WORKER_NAME="${WORKER_NAME:-persona-worker}"
REDIS_NAME="${REDIS_NAME:-redis}"         # имя контейнера Redis (существующий или будет создан)
NETWORK="${NETWORK:-persona-net}"

API_PORT="${API_PORT:-8000}"              # внешний порт хоста -> 8000 внутри API
REDIS_PORT="${REDIS_PORT:-6379}"
REDIS_DB="${REDIS_DB:-0}"
REDIS_PASSWORD="${REDIS_PASSWORD:-}"      # если нужен пароль, задайте его в ENV

WORKER_CONCURRENCY="${WORKER_CONCURRENCY:-3}"
WORKER_POOL="${WORKER_POOL:-threads}"

# Нужен ли отдельный Redis-контейнер, если его нет
CREATE_REDIS_IF_MISSING="${CREATE_REDIS_IF_MISSING:-true}"
# Публиковать ли Redis наружу
EXPOSE_REDIS="${EXPOSE_REDIS:-false}"

NGINX_NAME="${NGINX_NAME:-persona-nginx}"
NGINX_PORT="${NGINX_PORT:-8080}"
NGINX_CONF_HOST="${NGINX_CONF_HOST:-$(pwd)/nginx.conf}"
UI_WEB_HOST="${UI_WEB_HOST:-$(pwd)/ui_web}"

# --- ВАЖНО: используем имя контейнера Redis как хост для всех сервисов ---
REDIS_HOST="${REDIS_NAME}"

### === Утилиты ===
log() { echo -e "\033[1;32m[+]\033[0m $*"; }
warn() { echo -e "\033[1;33m[!]\033[0m $*"; }
err() { echo -e "\033[1;31m[x]\033[0m $*" 1>&2; }

need_cmd() { command -v "$1" >/dev/null 2>&1 || { err "Нет команды $1"; exit 1; }; }

container_exists() { docker inspect "$1" >/dev/null 2>&1; }
container_running() { [[ "$(docker inspect -f '{{.State.Running}}' "$1" 2>/dev/null || echo false)" == "true" ]]; }

ensure_network() {
  if ! docker network inspect "$NETWORK" >/dev/null 2>&1; then
    log "Создаю сеть $NETWORK"
    docker network create "$NETWORK"
  else
    log "Сеть $NETWORK уже существует"
  fi
}

ensure_connected() {
  local name="$1"
  if docker network inspect "$NETWORK" -f '{{range .Containers}}{{.Name}} {{end}}' | grep -qw "$name"; then
    log "Контейнер $name уже в сети $NETWORK"
  else
    log "Подключаю $name к сети $NETWORK"
    docker network connect "$NETWORK" "$name" 2>/dev/null || true
  fi
}

run_redis_if_needed() {
  if container_exists "$REDIS_NAME"; then
    log "Найден Redis контейнер: $REDIS_NAME"
    ensure_connected "$REDIS_NAME"
    if ! container_running "$REDIS_NAME"; then
      log "Запускаю Redis контейнер $REDIS_NAME"
      docker start "$REDIS_NAME" >/dev/null
    fi
  else
    if [[ "$CREATE_REDIS_IF_MISSING" == "true" ]]; then
      log "Redis не найден — создаю контейнер $REDIS_NAME"
      if [[ "$EXPOSE_REDIS" == "true" ]]; then
        docker run -d --name "$REDIS_NAME" --network "$NETWORK" \
          -p "${REDIS_PORT}:6379" \
          --restart unless-stopped \
          redis:7-alpine >/dev/null
      else
        docker run -d --name "$REDIS_NAME" --network "$NETWORK" \
          --restart unless-stopped \
          redis:7-alpine >/dev/null
      fi
    else
      err "Redis контейнер $REDIS_NAME не найден и автосоздание отключено (CREATE_REDIS_IF_MISSING=false)."
      exit 1
    fi
  fi

  log "Проверяю доступность Redis (${REDIS_NAME}:6379)"
  docker run --rm --network "$NETWORK" redis:7-alpine \
    redis-cli -h "$REDIS_NAME" -p 6379 ping | grep -q PONG || {
      err "Redis не отвечает на ping"; exit 1;
    }
  log "Redis OK (PONG)"
}

run_api() {
  # Убиваем старый контейнер, если есть
  if container_exists "$API_NAME"; then
    if container_running "$API_NAME"; then
      log "Останавливаю старый API контейнер $API_NAME"
      docker rm -f "$API_NAME" >/dev/null
    else
      docker rm "$API_NAME" >/dev/null || true
    fi
  fi

  log "Запускаю API контейнер $API_NAME (порт ${API_PORT}->8000)"
  docker run -d --name "$API_NAME" --network "$NETWORK" \
    -p "${API_PORT}:8000" \
    -e REDIS_HOST="$REDIS_HOST" \
    -e REDIS_PORT="$REDIS_PORT" \
    -e REDIS_DB="$REDIS_DB" \
    -e REDIS_PASSWORD="$REDIS_PASSWORD" \
    --restart unless-stopped \
    "$IMAGE" >/dev/null

  ensure_connected "$API_NAME"

  log "Жду старт API и делаю пробный HTTP-запрос..."
  for i in {1..20}; do
    if curl -fsS "http://127.0.0.1:${API_PORT}/" >/dev/null 2>&1 || \
       curl -fsS "http://127.0.0.1:${API_PORT}/docs" >/dev/null 2>&1; then
      log "API отвечает на порту ${API_PORT}"
      break
    fi
    sleep 1
  done
}

run_worker() {
  # Запуск двух воркеров для разных очередей
  for QUEUE in court_checks court_verifications; do
    WORKER_CONTAINER="${WORKER_NAME}-${QUEUE}"
    # Убиваем старый контейнер, если есть
    if container_exists "$WORKER_CONTAINER"; then
      if container_running "$WORKER_CONTAINER"; then
        log "Останавливаю старый worker $WORKER_CONTAINER"
        docker rm -f "$WORKER_CONTAINER" >/dev/null
      else
        docker rm "$WORKER_CONTAINER" >/dev/null || true
      fi
    fi

    log "Запускаю Celery worker $WORKER_CONTAINER для очереди $QUEUE"
    docker run -d --name "$WORKER_CONTAINER" --network "$NETWORK" \
      -e REDIS_HOST="$REDIS_HOST" \
      -e REDIS_PORT="$REDIS_PORT" \
      -e REDIS_DB="$REDIS_DB" \
      -e REDIS_PASSWORD="$REDIS_PASSWORD" \
      --restart unless-stopped \
      "$IMAGE" \
      celery -A app.celery.celery_app.celery_app worker \
        --pool="$WORKER_POOL" --concurrency="$WORKER_CONCURRENCY" -l info -Q "$QUEUE" >/dev/null

    ensure_connected "$WORKER_CONTAINER"
  done
}

run_nginx() {
  # Убиваем старый контейнер, если есть
  if container_exists "$NGINX_NAME"; then
    if container_running "$NGINX_NAME"; then
      log "Останавливаю старый Nginx контейнер $NGINX_NAME"
      docker rm -f "$NGINX_NAME" >/dev/null
    else
      docker rm "$NGINX_NAME" >/dev/null || true
    fi
  fi

  if [[ ! -f "$NGINX_CONF_HOST" ]]; then
    warn "nginx.conf не найден по пути $NGINX_CONF_HOST — создаю дефолтный"
    cat > "$NGINX_CONF_HOST" <<EOF
events {}
http {
    server {
        listen 80;
        server_name _;
        root /usr/share/nginx/html;
        index index.html;
        location / {
            try_files \$uri \$uri/ /index.html;
        }
    }
}
EOF
  fi

  log "Запускаю Nginx контейнер $NGINX_NAME (порт ${NGINX_PORT}->80)"
  docker run -d --name "$NGINX_NAME" --network "$NETWORK" \
    -p "${NGINX_PORT}:80" \
    -v "$UI_WEB_HOST:/usr/share/nginx/html:ro" \
    -v "$NGINX_CONF_HOST:/etc/nginx/nginx.conf:ro" \
    --restart unless-stopped \
    nginx:1.25-alpine >/dev/null

  ensure_connected "$NGINX_NAME"

  log "Жду старт Nginx и делаю пробный HTTP-запрос..."
  for i in {1..10}; do
    if curl -fsS "http://127.0.0.1:${NGINX_PORT}/" >/dev/null 2>&1; then
      log "Nginx отвечает на порту ${NGINX_PORT}"
      break
    fi
    sleep 1
  done
}

show_status() {
  echo
  log "Статус контейнеров:"
  docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'
  echo
  log "Подсказки:"
  echo "  - Логи API:     docker logs -f ${API_NAME}"
  echo "  - Логи worker court_checks:     docker logs -f ${WORKER_NAME}-court_checks"
  echo "  - Логи worker court_verifications: docker logs -f ${WORKER_NAME}-court_verifications"
  echo "  - Проверка API: curl -I http://127.0.0.1:${API_PORT}/docs || curl -I http://127.0.0.1:${API_PORT}/"
}

main() {
  need_cmd docker
  ensure_network
  run_redis_if_needed
  run_api
  run_worker
  run_nginx
  show_status
}

main "$@"
