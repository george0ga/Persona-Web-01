set -euo pipefail

log() { echo -e "\033[1;32m[+]\033[0m $*"; }

log "Останавливаю все Docker-контейнеры проекта Persona..."

docker ps -aq | xargs -r docker stop

log "Все контейнеры