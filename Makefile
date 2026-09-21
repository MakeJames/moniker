include deploy/defaults.mk
-include deploy/local.mk

UV ?= $(shell command -v uv 2>/dev/null)

BUILD_DIR := build/deploy
DIST_DIR := dist

VENV := $(MONIKER_HOME)/.venv

SYSTEMD_DIR ?= /etc/systemd/system
NGINX_AVAILABLE ?= /etc/nginx/sites-available
NGINX_ENABLED ?= /etc/nginx/sites-enabled

SUDO ?= sudo

.PHONY: check-uv

.PHONY: \
	build \
	check-uv \
	configure \
	clean-config \
	deploy \
	enable \
	show-config \
	install \
	install-config \
	migrate

check-uv:
	@if [ -z "$(UV)" ] || [ ! -x "$(UV)" ]; then \
		echo "uv could not be found."; \
		echo "Set UV=/path/to/uv or add uv to PATH."; \
		exit 1; \
	fi

configure: \
	$(BUILD_DIR)/moniker.env \
	$(BUILD_DIR)/moniker.service \
	$(BUILD_DIR)/moniker.nginx

$(BUILD_DIR)/moniker.env: deploy/moniker.env.in | $(BUILD_DIR)
	sed \
		-e 's|@DATABASE@|$(MONIKER_DATABASE)|g' \
		-e 's|@HOST@|$(MONIKER_HOST)|g' \
		-e 's|@PORT@|$(MONIKER_PORT)|g' \
		-e 's|@LOG_LEVEL@|$(MONIKER_LOG_LEVEL)|g' \
		$< > $@

$(BUILD_DIR)/moniker.service: \
		deploy/moniker.service.in | $(BUILD_DIR)
	sed \
		-e 's|@USER@|$(MONIKER_USER)|g' \
		-e 's|@GROUP@|$(MONIKER_GROUP)|g' \
		-e 's|@HOME@|$(MONIKER_HOME)|g' \
		-e 's|@STATE@|$(MONIKER_STATE)|g' \
		-e 's|@CONFIG@|$(MONIKER_CONFIG)|g' \
		$< > $@

$(BUILD_DIR)/moniker.nginx: \
		deploy/moniker.nginx.in | $(BUILD_DIR)
	sed \
		-e 's|@SERVER_NAME@|$(MONIKER_SERVER_NAME)|g' \
		-e 's|@HOST@|$(MONIKER_HOST)|g' \
		-e 's|@PORT@|$(MONIKER_PORT)|g' \
		$< > $@

show-config:
	@echo "user:        $(MONIKER_USER)"
	@echo "group:       $(MONIKER_GROUP)"
	@echo "home:        $(MONIKER_HOME)"
	@echo "state:       $(MONIKER_STATE)"
	@echo "database:    $(MONIKER_DATABASE)"
	@echo "host:        $(MONIKER_HOST)"
	@echo "port:        $(MONIKER_PORT)"
	@echo "log level:   $(MONIKER_LOG_LEVEL)"
	@echo "server name: $(MONIKER_SERVER_NAME)"
	@echo "python:      $(MONIKER_PYTHON)"
	@echo "uv:          $(UV)"

clean-config:
	rm -rf $(BUILD_DIR)

build: check-uv
	mkdir -p $(DIST_DIR)
	$(UV) build \
		--wheel \
		--clear \
		--out-dir $(DIST_DIR)

install: install-user build
	$(SUDO) install -d \
		-o $(MONIKER_USER) \
		-g $(MONIKER_GROUP) \
		$(MONIKER_HOME)

	$(SUDO) install -d \
		-o $(MONIKER_USER) \
		-g $(MONIKER_GROUP) \
		$(MONIKER_STATE)

	$(SUDO) uv venv \
		--python python3 \
		$(VENV)

	$(SUDO) uv pip install \
		--python $(VENV) \
		--reinstall \
		$(DIST_DIR)/*.whl

install-config: configure install-user
	$(SUDO) install -d \
		-o root \
		-g $(MONIKER_GROUP) \
		-m 0750 \
		$(MONIKER_CONFIG)

	$(SUDO) install \
		-o root \
		-g $(MONIKER_GROUP) \
		-m 0640 \
		$(BUILD_DIR)/moniker.env \
		$(MONIKER_CONFIG)/moniker.env

	$(SUDO) install \
		-o root \
		-g root \
		-m 0644 \
		$(BUILD_DIR)/moniker.service \
		$(SYSTEMD_DIR)/moniker.service

	$(SUDO) install \
		-o root \
		-g root \
		-m 0644 \
		$(BUILD_DIR)/moniker.nginx \
		$(NGINX_AVAILABLE)/moniker

install-user:
	@if ! getent group $(MONIKER_GROUP) >/dev/null; then \
		$(SUDO) groupadd \
			--system \
			$(MONIKER_GROUP); \
	fi

	@if ! id -u $(MONIKER_USER) >/dev/null 2>&1; then \
		$(SUDO) useradd \
			--system \
			--gid $(MONIKER_GROUP) \
			--home $(MONIKER_STATE) \
			--no-create-home \
			--shell /usr/sbin/nologin \
			$(MONIKER_USER); \
	fi

migrate:
	@test -x "$(VENV)/bin/moniker-migrate" || { \
		echo "Moniker is not installed."; \
		echo "Run 'make install' first."; \
		exit 1; \
	}

	$(SUDO) -u $(MONIKER_USER) \
		env \
		MONIKER_DATABASE="$(MONIKER_DATABASE)" \
		$(VENV)/bin/moniker-migrate

enable:
	@test -f "$(SYSTEMD_DIR)/moniker.service" || { \
		echo "Moniker systemd configuration is not installed."; \
		exit 1; \
	}

	@test -f "$(NGINX_AVAILABLE)/moniker" || { \
		echo "Moniker nginx configuration is not installed."; \
		exit 1; \
	}

	$(SUDO) systemctl daemon-reload

	$(SUDO) ln -sfn \
		$(NGINX_AVAILABLE)/moniker \
		$(NGINX_ENABLED)/moniker

	$(SUDO) nginx -t

	$(SUDO) systemctl enable --now moniker

	$(SUDO) systemctl reload nginx

deploy:
	$(MAKE) install
	$(MAKE) install-config
	$(MAKE) migrate
	$(MAKE) enable

upgrade:
	$(MAKE) install
	$(MAKE) migrate
	$(SUDO) systemctl restart moniker

$(BUILD_DIR):
	mkdir -p $(BUILD_DIR)
