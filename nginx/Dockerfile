# Use the official Nginx image from Docker Hub
FROM nginx:1.25-alpine

# Remove the default Nginx configuration file
RUN rm /etc/nginx/conf.d/default.conf

# Copy the custom configuration file from the host to the container
COPY nginx.conf /etc/nginx/conf.d/
