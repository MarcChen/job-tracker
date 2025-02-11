launch:
	@bash scripts/launch_chromium.sh

stop:
	@bash scripts/stop_chromium.sh

restart:
	@bash scripts/restart_chromium.sh

build-image:
	@docker build -t job-scraper-image .

launch-image:
	@docker run -d --name job-scraper-container job-scraper-image
