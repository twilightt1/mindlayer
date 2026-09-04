# Multi-stage Dockerfile for the Next.js frontend.
# Targets: dev (hot-reload, used by docker-compose.yml) and runner (prod, used by docker-compose.prod.yml).

FROM node:20-alpine AS base
RUN npm install -g pnpm@9
WORKDIR /app

# ── Dependencies (cached until lockfiles change) ─────────────────────────────
FROM base AS deps
COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile

# ── Dev server with hot reload ───────────────────────────────────────────────
FROM deps AS dev
ENV NEXT_TELEMETRY_DISABLED=1 \
    WATCHPACK_POLLING=true
COPY . .
EXPOSE 3000
CMD ["pnpm", "dev"]

# ── Production build ─────────────────────────────────────────────────────────
FROM deps AS builder
ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL \
    NEXT_TELEMETRY_DISABLED=1
COPY . .
RUN pnpm build

FROM base AS prod-deps
COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile --prod

# ── Production runtime ───────────────────────────────────────────────────────
FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1
COPY --from=prod-deps /app/node_modules ./node_modules
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/next.config.js ./next.config.js
COPY --from=builder /app/package.json ./package.json
EXPOSE 3000
CMD ["npm", "run", "start"]
