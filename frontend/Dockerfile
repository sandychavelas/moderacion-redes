# syntax=docker/dockerfile:1

# =====================================================================
# Etapa 1: build -> genera el bundle estatico con Vite usando pnpm.
# =====================================================================
FROM node:24.17.0-slim AS build

# Habilita pnpm como gestor de paquetes (via corepack, incluido en Node).
ENV PNPM_HOME=/root/.local/share/pnpm \
    PATH="/root/.local/share/pnpm:$PATH"
RUN corepack enable && corepack prepare pnpm@10.15.0 --activate

WORKDIR /app

# Instalacion de dependencias en capa separada para aprovechar cache.
COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile

# Copia del codigo fuente y build de produccion.
COPY . .
RUN pnpm run build

# =====================================================================
# Etapa 2: runtime -> Nginx sirviendo el build estatico.
# =====================================================================
FROM nginx:1.27-alpine AS runtime

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
