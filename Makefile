include deploy/defaults.mk
-include deploy/local.mk

BUILD_DIR := build/deploy
DIST_DIR := dist

VENV := $(MONIKER_HOME)/.venv

SYSTEMD_DIR ?= /etc/systemd/system
NGINX_AVAILABLE ?= /etc/nginx/sites-available
NGINX_ENABLED ?= /etc/nginx/sites-enabled

SUDO ?= sudo

.PHONY: \
	configure \
	show-config \
	clean-config \
	build \
	install \
	install-config \
	migrate \
	enable

configure: \
	$(BUILD_DIR)/moniker.env \
	$(BUILD_DIR)/moniker.service \
	$(BUILD_DIR)/moniker.nginx

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

clean-config:
	rm -rf $(BUILD_DIR)

build:
	uv build

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

install-config: configure
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
	@if ! id -u $(MONIKER_USER) >/dev/null 2>&1; then \
		$(SUDO) useradd \
			--system \
			--home $(MONIKER_STATE) \
			--shell /usr/sbin/nologin \
			$(MONIKER_USER); \
	fi

migrate: install install-config
	migrate:
	$(SUDO) -u $(MONIKER_USER) \
		env \
		MONIKER_DATABASE="$(MONIKER_DATABASE)" \
		$(VENV)/bin/moniker-migrate

enable: install install-config migrate
	$(SUDO) systemctl daemon-reload

	$(SUDO) ln -sfn \
		$(NGINX_AVAILABLE)/moniker \
		$(NGINX_ENABLED)/moniker

	$(SUDO) nginx -t

	$(SUDO) systemctl enable --now moniker

	$(SUDO) systemctl reload nginx

upgrade:
	$(MAKE) install
	$(MAKE) migrate
	$(SUDO) systemctl restart moniker

$(BUILD_DIR):
	mkdir -p $(BUILD_DIR)
