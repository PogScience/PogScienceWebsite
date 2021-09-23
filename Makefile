## ~ Installation

install: install-back install-front ## Install the Python and NodeJS environments.

install-back: ## Install the Python environment.
	pipenv install --dev
	pipenv run pre-commit install

install-front: ## Install the front-end dependencies.
	npm install --save-dev

##
## ~ Development execution

run: ## Run the website in development mode, with auto-rebuild. This must be launched from within the virtualenv (run `pipenv shell` before).
	make -j2 run-back watch-front

run-back: ## Run the website development server. This must be launched from within the virtualenv (run `pipenv shell` before).
	python manage.py runserver

watch-front: ## Build the front-end with webpack, in watch mode, to recompile at each change.
	npm run watch

# inspired from https://gist.github.com/sjparkinson/f0413d429b12877ecb087c6fc30c1f0a
# and https://github.com/zestedesavoir/zds-site/blob/dev/Makefile

.DEFAULT_GOAL := help
help: ## Show this help
	@echo "Use 'make [command]' to run one of these commands."
	@echo ""
	@fgrep --no-filename "##" ${MAKEFILE_LIST} | head -n '-1' | sed 's/\:.*\#/\: \#/g' | column -s ':#' -t -c 2
	@echo ""
	@echo "Open this Makefile to see what each command does."
