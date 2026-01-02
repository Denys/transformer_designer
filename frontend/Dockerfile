# Frontend Dockerfile
FROM node:20-slim

WORKDIR /app

# Copy package files
COPY package.json package-lock.json ./

# Install dependencies
RUN npm ci

# Copy project files
COPY . .

# Build
RUN npm run build

# Expose port
EXPOSE 3000

# Run application
CMD ["node", ".output/server/index.mjs"]
