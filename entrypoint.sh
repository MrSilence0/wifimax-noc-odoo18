#!/bin/bash

# Default values if not provided
: "${DB_HOST:=odoo18db}"
: "${PORT:=5432}"
: "${USER:=odoo18}"
: "${PASSWORD:=odoo18}"

exec python3 /opt/odoo/odoo-bin \
    -c /etc/odoo.conf \
    --db_host="$DB_HOST" \
    --db_port="$PORT" \
    --db_user="$USER" \
    --db_password="$PASSWORD" \
    --log-level=debug