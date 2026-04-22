FROM node:22-alpine AS deps
WORKDIR /workspace
COPY package.json package-lock.json* ./
COPY services/app/client/package.json ./services/app/client/package.json
COPY packages/shared/package.json ./packages/shared/package.json
RUN npm install

FROM node:22-alpine AS build
WORKDIR /workspace
COPY --from=deps /workspace/node_modules ./node_modules
COPY package.json ./
COPY services/app/client ./services/app/client
COPY packages/shared ./packages/shared
RUN npm run -w packages/shared build && npm run -w services/app/client build

FROM node:22-alpine
WORKDIR /app
COPY --from=build /workspace/services/app/client/dist ./dist
RUN npm init -y && npm install --omit=dev vite
EXPOSE 4173
CMD ["./node_modules/.bin/vite", "preview", "--host", "0.0.0.0", "--port", "4173"]
