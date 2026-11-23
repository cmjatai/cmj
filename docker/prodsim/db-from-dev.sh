#!/usr/bin/env bash
# Recria o banco da produção simulada a partir do banco do dev.
#
# Lê o cmjpostgres18 do dev (só pg_dump) e APAGA o banco "cmj" do
# prodsim-postgres18 antes de restaurar. Nunca escreve no dev.
# Uso: sudo docker/prodsim/db-from-dev.sh
source "$(dirname "$0")/_comum.sh"

DEV_PG=cmjpostgres18
SIM_PG=prodsim-postgres18

container_rodando "$DEV_PG" || { echo "O Postgres do dev ($DEV_PG) não está rodando." >&2; exit 1; }
container_rodando "$SIM_PG" || { echo "O Postgres da simulação ($SIM_PG) não está rodando: rode up.sh." >&2; exit 1; }

read -r -p "Apagar o banco 'cmj' de $SIM_PG e copiar o do dev? Digite 'sim': " resp
[ "$resp" = "sim" ] || { echo "Cancelado."; exit 1; }

GREEN_RODANDO=0
container_rodando prodsim-cmj-green && GREEN_RODANDO=1

echo "Parando a aplicação da simulação..."
prodsim_compose --profile green stop cmj-blue cmj-green

docker exec "$SIM_PG" psql -U cmj_dt1 -d postgres -v ON_ERROR_STOP=1 \
    -c "DROP DATABASE IF EXISTS cmj WITH (FORCE)" \
    -c "CREATE DATABASE cmj"

echo "Copiando (pg_dump do dev | pg_restore na simulação)..."
docker exec "$DEV_PG" pg_dump -U cmj -d cmj -Fc --no-owner --no-acl \
    | docker exec -i "$SIM_PG" pg_restore -U cmj_dt1 -d cmj --no-owner --no-acl --exit-on-error

docker exec "$SIM_PG" psql -U cmj_dt1 -d cmj -v ON_ERROR_STOP=1 \
    -c "CREATE EXTENSION IF NOT EXISTS pg_stat_statements"

echo "Subindo a aplicação (o start.sh roda o migrate)..."
prodsim_compose start cmj-blue
[ "$GREEN_RODANDO" = 1 ] && prodsim_compose --profile green start cmj-green

echo
echo "Banco copiado. O índice do Solr da simulação não foi refeito; se precisar da busca:"
echo "  sudo docker exec -it prodsim-cmj-blue python3 manage.py rebuild_index --noinput"
