FROM nginx:alpine AS production
# Copy the production build artifacts from the build stage
COPY build /usr/share/nginx/html
COPY nginx/app.conf /etc/nginx/conf.d/app.conf

# Expose the default NGINX port
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]