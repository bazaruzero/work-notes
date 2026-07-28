#!/bin/bash

export PGHOST="/tmp"
export PGPORT=5415
export PGDATABASE="postgres"
export PGUSER="admin"

export TEST_DURATION_SEC=600
export SLEEP_SEC=300

read -s -p "Enter password for user = ${PGUSER}: " PGPASSWORD && echo

for case in {1..5}; do
    echo "---------- CASE #${case} ----------"

    psql -h ${PGHOST} -p ${PGPORT} -d ${PGDATABASE} -U ${PGUSER} -f ./reinit.sql

    # read
    LOG_FILE_READ="./case${case}__read_only__$(date +%Y%m%d)T$(date +%H%M%S).log"
    nohup pgbench -h ${PGHOST} -p ${PGPORT} -c 10 -j 2 -P 5 -T ${TEST_DURATION_SEC} -f ./load_read.sql -M prepared --no-vacuum ${PGDATABASE} -U ${PGUSER} > ${LOG_FILE_READ} 2>&1 &

    # write
    LOG_FILE_WRITE="./case${case}__write_only__$(date +%Y%m%d)T$(date +%H%M%S).log"
    nohup pgbench -h ${PGHOST} -p ${PGPORT} -c 8 -j 2 -P 5 -T ${TEST_DURATION_SEC} -f ./load_write.sql -M prepared --no-vacuum ${PGDATABASE} -U ${PGUSER} > ${LOG_FILE_WRITE} 2>&1 &

    # info
    echo "INFO: Read-only load log file     : ${LOG_FILE_READ}"
    echo "INFO: Write-only load log file    : ${LOG_FILE_WRITE}"

    sleep ${SLEEP_SEC}
    psql -h ${PGHOST} -p ${PGPORT} -d ${PGDATABASE} -U ${PGUSER} -f ./case${case}.sql
    sleep ${SLEEP_SEC}

    echo "INFO: case #${case} completed."
done

