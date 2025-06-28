#!/bin/bash

DATABASE_ID="${DATABASE_ID_TEST:}"
NOTION_API_URL="https://api.notion.com/v1/databases/${DATABASE_ID}"
NOTION_VERSION="${NOTION_VERSION:-2022-02-22}"
NOTION_TOKEN="${NOTION_API}"

curl --location "$NOTION_API_URL" \
    --header "Notion-Version: $NOTION_VERSION" \
    --header "Authorization: Bearer $NOTION_TOKEN" \
    --header "Cookie: $NOTION_COOKIE"
