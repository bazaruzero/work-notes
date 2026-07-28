#!/bin/bash

set -e

##
## Variables:
##

PG_FTP_URL="https://ftp.postgresql.org/pub/source"

PG_VERSIONS=("10.23"
             "11.22"
             "12.22"
             "13.22"
             "14.19"
             "15.14"
             "16.10"
             "17.6"
             "18.0"
      )

PG_DOWNLOAD_DIR="$HOME/postgres/download"

PG_HOME_DIR="$HOME/postgres"

PG_DATA_DIR="$HOME/postgres/data"

MAKE_THREADS="$(( ($(nproc) + 1) / 2 ))"

##
## Main:
##

#sudo apt update
#sudo apt install build-essential libreadline-dev zlib1g-dev flex bison libxml2-dev libxslt-dev libssl-dev pkg-config

CURRENT_PATH=$(pwd)

mkdir -p ${PG_DOWNLOAD_DIR}

for version in "${PG_VERSIONS[@]}"; do

    ## Download archive
    if ! [[ -f ${PG_DOWNLOAD_DIR}/postgresql-${version}.tar.gz ]]; then
        wget --no-verbose -P ${PG_DOWNLOAD_DIR} "${PG_FTP_URL}/v${version}/postgresql-${version}.tar.gz"
    fi

    ## Untar
    tar -xzf ${PG_DOWNLOAD_DIR}/postgresql-${version}.tar.gz -C ${PG_DOWNLOAD_DIR}/

    ## Create bin dir
    mkdir -p ${PG_HOME_DIR}/${version}

    ## Configure
    cd ${PG_DOWNLOAD_DIR}/postgresql-${version}
    ./configure --prefix=${PG_HOME_DIR}/${version}

    ## Compile
    make -j${MAKE_THREADS} && make install

    ## Create data dir
    mkdir -p ${PG_DATA_DIR}/${version}

    ## Init cluster
    ${PG_HOME_DIR}/${version}/bin/initdb -k -D ${PG_DATA_DIR}/${version}

    ## Edit config
    cat >> ${PG_DATA_DIR}/${version}/postgresql.conf << EOF

listen_addresses='*'
port=54${version%%.*}
cluster_name='pg${version}'
logging_collector='on'
EOF

    ## Start instance
    ${PG_HOME_DIR}/${version}/bin/pg_ctl -D ${PG_DATA_DIR}/${version} start

    ## Edit .profile
    cat >> $HOME/.profile << EOF

pg${version}() {
    export PGDATA="${PG_DATA_DIR}/${version}"
    export PGPORT="54${version%%.*}"
    export PATH="\$(echo "\$PATH" | sed 's|:[^:]*/postgres[^:]*||g')"
    export PATH="\$PATH:${PG_HOME_DIR}/${version}/bin"
    alias psql="${PG_HOME_DIR}/${version}/bin/psql -d postgres"
    echo "PostgreSQL ${version} environment activated (Port: 54${version%%.*})"
}
EOF

    ## End
    source $HOME/.profile
    cd ${CURRENT_PATH}
done