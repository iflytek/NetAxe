FROM node:lts-alpine as build-stage
WORKDIR /app
COPY package*.json ./
RUN npm config set registry https://registry.npm.taobao.org
RUN npm install --force
COPY . .
RUN npm run build

# production stage
FROM nginx:1.7.9 as production-stage
COPY ./nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build-stage /app/dist /home
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]