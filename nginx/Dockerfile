FROM nginx:1.27-alpine

# install envsubst (gettext)
RUN apk add --no-cache gettext

COPY ./nginx.conf.template /nginx.conf.template

# substitute only API_HOST and API_PORT, reading from the template and writing to nginx conf
CMD ["/bin/sh", "-c", "envsubst '${API_HOST} ${API_PORT}' < /nginx.conf.template > /etc/nginx/nginx.conf && exec nginx -g 'daemon off;'"]