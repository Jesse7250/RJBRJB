FROM node:20-alpine

WORKDIR /app

# 安装依赖
COPY package*.json .
RUN npm install

# 复制源码
COPY . .

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host"]
