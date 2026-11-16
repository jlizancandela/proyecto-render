# Node 20 reached end of life in April 2026, so the build toolchain was
# running on an unpatched runtime.
FROM node:26 AS frontend_build
WORKDIR /app
COPY package.json package-lock.json ./
COPY scripts/ ./scripts/
COPY src/ ./src/ 
# esbuild needs src for entrypoints
RUN npm install
RUN npm run build

# Pinned rather than "latest": this stage only produces the vendor directory,
# so the tag has no reason to float.
FROM composer:2 AS composer_build
WORKDIR /app
COPY composer.json composer.lock ./
RUN composer install --no-dev --optimize-autoloader --ignore-platform-reqs --no-interaction

# Pinned on purpose: 8.4.27 is the first 8.4 release that fixes php2shell
# (CVE-2026-109618, CVE-2026-109619). Never move this to a floating tag;
# Dependabot keeps it current via .github/dependabot.yml.
FROM php:8.4.27-apache
WORKDIR /var/www/html

RUN apt-get update && apt-get install -y \
    libpng-dev \
    libonig-dev \
    libxml2-dev \
    libsqlite3-dev \
    sqlite3 \
    zip \
    unzip \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN docker-php-ext-install pdo_mysql pdo_sqlite mbstring exif pcntl bcmath gd
RUN a2enmod rewrite

# Hardening settings loaded through conf.d, which PHP scans even without a
# php.ini present in the image.
COPY docker/php-hardening.ini /usr/local/etc/php/conf.d/99-hardening.ini

COPY --from=composer_build /app/vendor ./vendor
COPY . .

# Overwrite local assets with fresh build
COPY --from=frontend_build /app/public/js/build ./public/js/build

# Required template assets from node_modules
COPY --from=frontend_build /app/node_modules/bootstrap/dist/css/bootstrap.min.css ./node_modules/bootstrap/dist/css/bootstrap.min.css
COPY --from=frontend_build /app/node_modules/bootstrap/dist/css/bootstrap.min.css.map ./node_modules/bootstrap/dist/css/bootstrap.min.css.map
COPY --from=frontend_build /app/node_modules/bootstrap-icons/font/ ./node_modules/bootstrap-icons/font/

RUN if [ ! -f .env ]; then cp .env.example .env; fi

# Permissions for temp and SQLite database directory
RUN mkdir -p /var/www/html/temp /var/www/html/database \
    && if [ ! -f /var/www/html/database/database.sqlite ] && [ -f /var/www/html/database/init.sqlite.sql ]; then \
        sqlite3 /var/www/html/database/database.sqlite < /var/www/html/database/init.sqlite.sql; \
    fi \
    && chown -R www-data:www-data /var/www/html \
    && chmod -R 755 /var/www/html \
    && chmod -R 775 /var/www/html/database \
    && chmod 664 /var/www/html/database/database.sqlite 2>/dev/null || true \
    && chmod -R 777 /var/www/html/temp

ENV APACHE_DOCUMENT_ROOT=/var/www/html
RUN sed -ri -e 's!/var/www/html!${APACHE_DOCUMENT_ROOT}!g' /etc/apache2/sites-available/*.conf
RUN sed -ri -e 's!/var/www/!${APACHE_DOCUMENT_ROOT}!g' /etc/apache2/apache2.conf /etc/apache2/conf-available/*.conf

# Configure Apache port: default to 80, but adapt if PORT is defined (e.g. on Render)
ENV PORT=80
RUN sed -i 's/Listen 80/Listen ${PORT}/g' /etc/apache2/ports.conf \
    && sed -i 's/<VirtualHost \*:80>/<VirtualHost *:${PORT}>/g' /etc/apache2/sites-available/*.conf

EXPOSE 80
CMD ["apache2-foreground"]
