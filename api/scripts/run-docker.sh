#!/bin/bash
set -e

# The script can take 2 optional arguments:
# 1. The django target to run
# 2. For migrate, serve and migrate-and-serve, the number of seconds to sleep before running

function migrate () {
    python manage.py migrate && python manage.py createcachetable
}
function serve() {
    # configuration parameters for statsd. Docs can be found here:
    # https://docs.gunicorn.org/en/stable/instrumentation.html
    export STATSD_PORT=${STATSD_PORT:-8125}
    export STATSD_PREFIX=${STATSD_PREFIX:-flagsmith.api}

    gunicorn --bind 0.0.0.0:8000 \
             --worker-tmp-dir /dev/shm \
             --timeout ${GUNICORN_TIMEOUT:-30} \
             --workers ${GUNICORN_WORKERS:-3} \
             --threads ${GUNICORN_THREADS:-2} \
             --access-logfile $ACCESS_LOG_LOCATION \
             --keep-alive ${GUNICORN_KEEP_ALIVE:-2} \
             ${STATSD_HOST:+--statsd-host $STATSD_HOST:$STATSD_PORT} \
             ${STATSD_HOST:+--statsd-prefix $STATSD_PREFIX} \
             app.wsgi
}
function migrate_identities(){
    python manage.py migrate_to_edge "$1"
}
function migrate_analytics_db(){
    python manage.py migrate --database analytics
}
function import_organisation_from_s3(){
    python manage.py importorganisationfroms3 "$1" "$2"
}
function dump_organisation_to_s3(){
    python manage.py dumporganisationtos3 "$1" "$2" "$3"
}
function dump_organisation_to_local_fs(){
    python manage.py dumporganisationtolocalfs "$1" "$2"
}
function go_to_sleep(){
    echo "Sleeping for ${1} seconds before startup"
    sleep ${1}
}

if [ "$1" == "migrate" ]; then
    if [ $# -eq 2 ]; then go_to_sleep "$2"; fi
    migrate
elif [ "$1" == "serve" ]; then
    if [ $# -eq 2 ]; then go_to_sleep "$2"; fi
    serve
elif [ "$1" == "migrate-and-serve" ]; then
    if [ $# -eq 2 ]; then go_to_sleep "$2"; fi
    migrate
    serve
elif [ "$1" == "migrate-identities" ]; then
    migrate_identities "$2"
elif [ "$1" == "import-organisation-from-s3" ]; then
    import_organisation_from_s3 "$2" "$3"
elif [ "$1" == "dump-organisation-to-s3" ]; then
    dump_organisation_to_s3 "$2" "$3" "$4"
elif [ "$1" == "dump-organisation-to-local-fs" ]; then
    dump_organisation_to_local_fs "$2" "$3"
elif [ "$1" == "migrate-analytics-db" ]; then
    migrate_analytics_db
else
   echo "ERROR: unrecognised command '$1'"
fi
