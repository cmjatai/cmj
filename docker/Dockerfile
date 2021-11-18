# estágio de compilação
FROM node:lts-buster-slim

WORKDIR /app

COPY _frontend/v3/package.json .
COPY _frontend/v3/yarn.lock .

RUN yarn install
COPY _frontend/v3/. .
RUN yarn build

EXPOSE 3000

CMD [ "yarn", "prod" ]

# estágio de produção
#FROM nginx:stable-alpine as production-stage
#COPY _frontend/client /usr/share/nginx/html
#COPY --from=build-stage /app/dist /usr/share/nginx/html
#EXPOSE 80
#CMD ["nginx", "-g", "daemon off;"]