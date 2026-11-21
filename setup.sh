# The boilerplate 
set -euo pipefail
cd "$(dirname "$0")"


log() { echo -e "\033[1;34m[setup $(date +%H:%M:%S)]\033[0m $*"; }
fail() { echo -e "\033[1;31m[setup ERROR]\033[0m $*" >&2; exit 1; }


# prerequisites Check 
command -v docker >/dev/null || fail "Docker not installed"
command -v docker compose version >/dev/null || fail "Docker Compose not installed"
command -v python3 >/dev/null || fail "Python3 not installed"
command -v curl >/dev/null || fail "curl not installed"


# environment configuration Setup
if [[ ! -f .env ]]; then
    cp .env.example .env
fi
set -a; source .env;set +a


# Python venv setup
if [[ ! -d venv ]]; then
   python3 -m venv .venv 
fi 

.venv/bin/pip install --quiet -r requirements.txt


# Postgress DW container setup
docker compose up -d postgres

for i in {1..30}; do 
    status=$(docker inspect -f '{{.State.Health.Status}}' nyc_taxi_postgres 2>/dev/null || echo starting)
    [[ "$status" == "healthy" ]] && break 
    sleep 2
done  

[[ "$status" == "healthy" ]] || fail "Postgres container failed to start"


#Postgress schema setup
if [[ -f sql/schema.sql ]]; then 
    docker exec -i nyc_taxi_postgres psql -U $POSTGRES_USER -d $POSTGRES_DB < sql/schema.sql
else log "No schema.sql file found, skipping schema setup"
fi    


 #Download RawData Setup
 BASE_URL="https://d37ci6vzurychx.cloudfront.net/trip-data"
 DATA_DIR="data/raw"

current_month=$(date +%-m)
current_year=$(date +%Y)
current_quarter=$(( (current_month - 1) / 3 + 1 ))
previous_quarter=$((current_quarter - 1))
quarter_year=$current_year

if (( previous_quarter == 0 )); then
  previous_quarter=4
  quarter_year=$((quarter_year - 1))
fi

first_month=$(( (previous_quarter - 1) * 3 + 1 ))
TAXI_MONTHS=$(printf '%04d-%02d %04d-%02d %04d-%02d' \
  "$quarter_year" "$first_month" \
  "$quarter_year" "$((first_month + 1))" \
  "$quarter_year" "$((first_month + 2))")

download() { 
    local url=$1
    local output_file=$2

    if [[ -f "$output_file" ]]; then
        log "File $output_file already exists, skipping download."
    else
        log "Downloading $url to $output_file"
        curl -L "$url" -o "$output_file" || fail "Failed to download $url"
    fi
}

for month in $TAXI_MONTHS; do
download "$BASE_URL/yellow_tripdata_${month}.parquet" "$DATA_DIR/yellow_tripdata_${month}.parquet"
done


