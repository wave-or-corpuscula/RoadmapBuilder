FROM node:22-alpine

WORKDIR /app

COPY package*.json /app/
RUN npm ci && install -g vite

COPY . /app

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]

