FROM node:22-alpine

WORKDIR /app

# Копируем только package.json сначала (для кэширования слоев)
COPY package*.json ./

# Устанавливаем зависимости
RUN npm install

# Копируем остальные файлы
COPY . .

EXPOSE 5173

# Запускаем через npx
CMD ["npx", "vite", "--host", "0.0.0.0", "--port", "5173"]