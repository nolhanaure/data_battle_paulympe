FROM node:20-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

RUN npm run build

# Serveur statique
RUN npm install -g serve

CMD ["npm", "run", "dev"]
