# Stage 1: Build the Vite React App
FROM oven/bun:1.1.10 AS build

WORKDIR /app

# Install dependencies using bun
COPY package.json bun.lock* ./
RUN bun install --frozen-lockfile

# Copy the rest of the application
COPY . .

# Pass backend URL down during build time so the viewer maps the websockets properly
ARG VITE_API_BASE_URL=http://localhost:8000
ARG VITE_WS_BACKEND_URL=ws://localhost:8000
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
ENV VITE_WS_BACKEND_URL=$VITE_WS_BACKEND_URL

RUN bun run build

# Stage 2: Serve via Nginx (Industry standard for containerized static frontends)
FROM nginx:alpine

# Remove default nginx static assets
RUN rm -rf /usr/share/nginx/html/*

# Copy built assets from builder stage
COPY --from=build /app/dist /usr/share/nginx/html

# Replace the default Nginx config to cleanly fallback on index.html (SPA standard)
RUN echo $'\
server {\n\
    listen 80;\n\
    location / {\n\
        root   /usr/share/nginx/html;\n\
        index  index.html index.htm;\n\
        try_files $uri $uri/ /index.html;\n\
    }\n\
}\n' > /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]