#!/usr/bin/env bash
# Canonical Wayback snapshot for aspriter.am restoration
export SNAPSHOT_TIMESTAMP="${SNAPSHOT_TIMESTAMP:-20230321042548}"
export BASE_URL="https://aspriter.am"
export WAYBACK_BASE="https://web.archive.org/web/${SNAPSHOT_TIMESTAMP}"
export CDX_API="https://web.archive.org/cdx/search/cdx"
export REQUEST_DELAY="${REQUEST_DELAY:-1}"
