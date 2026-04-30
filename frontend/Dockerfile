FROM node:20-bookworm-slim

WORKDIR /app

EXPOSE 3000

# Source code comes from the bind mount (./frontend:/app).
# npm install runs at container startup so node_modules are written
# into the bind-mounted directory and persist across restarts.
CMD ["sh", "-c", "npm install && exec npm run dev -- -H 0.0.0.0 -p 3000"]