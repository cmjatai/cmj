# estágio de compilação
FROM node:14.18.1-buster-slim

WORKDIR /app

COPY _frontend/v3/package.json .
COPY _frontend/v3/yarn.lock .

RUN rm -rf dist
RUN rm -rf node_modules

RUN yarn install
COPY _frontend/v3/. .
RUN npm run build


EXPOSE 3000

CMD [ "npm", "run", "prod:serve" ]

# estágio de produção
#FROM nginx:stable-alpine as production-stage
#COPY _frontend/client /usr/share/nginx/html
#COPY --from=build-stage /app/dist /usr/share/nginx/html
#EXPOSE 80
#CMD ["nginx", "-g", "daemon off;"]