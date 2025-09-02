set -euo pipefail

log() { echo -e "\033[1;32m[+]\033[0m $*"; }

log "Останавливаю все Docker-контейнеры проекта Persona..."

CONTAINERS=$(docker ps -aq --filter "name=^persona-" --filter "name=^persona-api$" --filter "name=^persona-worker$")

if [[ -n "$CONTAINERS" ]]; then
  docker stop $CONTAINERS
  log "Контейнеры Persona остановлены: $CONTAINERS"
else
  log "Нет запущенных контейнеров Persona."
fi