FROM php:8.2-apache

# Dependências
RUN apt-get update && apt-get install -y \
    zip unzip git curl libzip-dev \
    && docker-php-ext-install zip pdo pdo_mysql

# Habilita mod_rewrite
RUN a2enmod rewrite

# Copia configuração do Apache
COPY apache.conf /etc/apache2/sites-available/000-default.conf

# Diretório do projeto
WORKDIR /var/www/html

# Copia código
COPY . .

# Composer
COPY --from=composer:latest /usr/bin/composer /usr/bin/composer

RUN composer install --no-dev --optimize-autoloader

# Permissões
RUN chown -R www-data:www-data /var/www/html \
    && chmod -R 775 /var/www/html/storage /var/www/html/bootstrap/cache

EXPOSE 80
