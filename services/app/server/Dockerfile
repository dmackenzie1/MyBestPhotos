FROM node:22-alpine AS deps
WORKDIR /workspace
COPY package.json package-lock.json* ./
COPY services/app/server/package.json ./services/app/server/package.json
COPY services/app/client/package.json ./services/app/client/package.json
COPY packages/shared/package.json ./packages/shared/package.json
RUN npm install

FROM node:22-alpine AS build
WORKDIR /workspace
COPY --from=deps /workspace/node_modules ./node_modules
COPY package.json ./
COPY services/app/server ./services/app/server
COPY packages/shared ./packages/shared
RUN npm run -w packages/shared build && npm run -w services/app/server build

FROM node:22-alpine
WORKDIR /app
COPY --from=build /workspace/services/app/server/dist ./dist
COPY --from=deps /workspace/node_modules ./node_modules
COPY services/app/server/package.json ./package.json
COPY reference ./reference
EXPOSE 3001
CMD ["node", "dist/services/app/server/src/index.js"]
