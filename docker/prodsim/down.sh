#!/usr/bin/env bash
# Para a produção simulada. Os volumes ficam; para apagá-los: down.sh --volumes
source "$(dirname "$0")/_comum.sh"

if [ "${1:-}" = "--volumes" ]; then
    prodsim_compose --profile green down --volumes
else
    prodsim_compose --profile green down
fi
