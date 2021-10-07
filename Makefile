## ~ Installation

install: install-back install-front ## Install the Python and NodeJS environments.

install-back: ## Installs the Python environment.
	pipenv install --dev
	pipenv run pre-commit install

install-front: ## Installs the front-end dependencies.
	npm install --save-dev

##
## ~ Development execution

ngrok-panel          := http://127.0.0.1:4040
tunnel-hostname-file := .https-tunnel-hostname

run-tunnel: ## Opens a HTTPS tunnel using ngrok for Twitch to be able to reach the development environment. Requires ngrok in the PATH.
	ngrok http 8000 --bind-tls=true --log=stdout > /dev/null &
	@> ${tunnel-hostname-file}
	@while [ ! -s ${tunnel-hostname-file} ]; do \
  		sleep 1; \
  		curl --silent ${ngrok-panel}/api/tunnels | jq -r ".tunnels[0].public_url" | sed s.https://.. | sed s.http://.. > ${tunnel-hostname-file}; \
	done
	@echo "HTTP tunnel started using ngrok."
	@echo "→ Control panel and requests log: ${ngrok-panel}"
	@echo "→ HTTPS tunnel URL:               https://$$(cat ${tunnel-hostname-file})"
	@echo

run-back: ## Runs the website development server. This must be launched from within the virtualenv (run `pipenv shell` before).
	python manage.py runserver

run-front: ## Builds the front-end with webpack, in watch mode, to recompile at each change.
	npm run watch

run-local: ## Runs the website in development mode, with auto-rebuild. This must be launched from within the virtualenv (run `pipenv shell` before).
	make -j2 run-back run-front

run: run-tunnel run-local ## Runs the website in development mode, with auto-rebuild, and Twitch EventSub support. This must be launched from within the virtualenv (run `pipenv shell` before).

stop-tunnel: ## Closes the HTTPS tunnel by killing ngrok.
	killall ngrok
	@> ${tunnel-hostname-file}

stop: stop-tunnel ## Stops every service running in the background.

##
## ~ Utilities

resub: ## Unsubscribes then re-subscribes to Twitch EventSub, for when the HTTPS tunnel changes. The server must be running.
	pipenv run python manage.py unsubscribe
	pipenv run python manage.py subscribe

##
## ~ Other

# inspired from https://gist.github.com/sjparkinson/f0413d429b12877ecb087c6fc30c1f0a
# and https://github.com/zestedesavoir/zds-site/blob/dev/Makefile

.DEFAULT_GOAL := help
help: ## Shows this help
	@echo "Use 'make [command]' to run one of these commands."
	@echo ""
	@fgrep --no-filename "##" ${MAKEFILE_LIST} | head -n '-1' | sed 's/\:.*\#/\: \#/g' | column -s ':#' -t -c 2
	@echo ""
	@echo "Open this Makefile to see what each command does."
