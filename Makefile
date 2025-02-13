launch:
	@bash scripts/launch_chromium.sh

stop:
	@bash scripts/stop_chromium.sh

restart:
	@bash scripts/restart_chromium.sh

build-image:
	@docker build -t scraper:test .

run-image:
	@docker run -e NOTION_API=$NOTION_API -e DATABASE_ID=$DATABASE_ID -e FREE_MOBILE_USER_ID=$FREE_MOBILE_USER_ID -e FREE_MOBILE_API_KEY=$FREE_MOBILE_API_KEY --name job-scraper-container scraper:test 

stop-remove:
	@docker stop job-scraper-container && docker rm job-scraper-container

# docker rm $(docker ps -a -q)