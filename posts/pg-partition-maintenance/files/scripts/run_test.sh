#!/bin/bash

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

PG_HOME_DIR="$HOME/postgres"

PG_OUTPUT_DIR="$HOME/postgres/out"

TEST_SQL_FILE="./test_case_attach_detach.sql"


mkdir -p ${PG_OUTPUT_DIR}

for version in "${PG_VERSIONS[@]}"; do
    echo "INFO: running test for version = ${version}"
    ${PG_HOME_DIR}/${version}/bin/psql -d postgres -p 54${version%%.*} -f ${TEST_SQL_FILE} > ${PG_OUTPUT_DIR}/${version}.out 2>&1
done

