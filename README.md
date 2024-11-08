# JustPay API

A secure API for the JustPay application, built with Flask and deployed with Docker and Nginx as a reverse proxy with HTTPS support.

---

## **Table of Contents**

- [Features](#features)
- [Prerequisites](#prerequisites)
- [Environment Setup](#environment-setup)
- [Deployment Instructions](#deployment-instructions)
  - [1. Build and Run with Docker Compose](#1-build-and-run-with-docker-compose)
  - [2. SSL Certificate Setup](#2-ssl-certificate-setup)
- [API Usage](#api-usage)
- [Folder Structure](#folder-structure)
- [Troubleshooting](#troubleshooting)

---

## **Features**

- Secure API with HTTPS using Nginx as a reverse proxy
- Dockerized deployment with Docker Compose
- API key-based security for endpoint access
- Automatic HTTP-to-HTTPS redirection

---

## **Prerequisites**

- **Docker** and **Docker Compose** installed
- **Python 3.9+**
- Domain name configured to point to your server’s IP address (for HTTPS setup)
- **Certbot** (optional, for SSL certificate generation)

---

## **Environment Setup**

1. **Clone the Repository**:

   ```bash
   git clone https://github.com/yourusername/justpay-backend.git
   cd justpay-backend
   ```

2. **Set Up Environment Variables**:

   Create a `.env` file in the project root and add the following:

   ```plaintext
   API_KEY=your-secret-api-key
   ```

   Replace `your-secret-api-key` with a secure API key for accessing protected endpoints.

3. **Install Dependencies** (optional for local testing):

   ```bash
   pip install -r requirements.txt
   ```

---

## **Deployment Instructions**

### **1. Build and Run with Docker Compose**

Docker Compose is used to manage the Nginx and Flask containers. The `docker-compose.yml` file in this project defines both services.

1. **Build and Start Containers**:

   ```bash
   docker-compose up --build -d
   ```

   This command will:
   - Build the Flask and Nginx Docker images.
   - Start both services with Nginx listening on ports 80 (HTTP) and 443 (HTTPS) and Flask running on port 5000.

2. **Verify the Services**:

   After running Docker Compose, verify the services are up and running:

   ```bash
   docker-compose ps
   ```

   Visit `http://yourdomain.com` (HTTP) or `https://yourdomain.com` (HTTPS) to check if the API is accessible.

### **2. SSL Certificate Setup**

To set up HTTPS with a secure SSL certificate, you can use **Let’s Encrypt** with **Certbot**.

1. **Install Certbot**:

   ```bash
   sudo apt update
   sudo apt install certbot
   ```

2. **Generate Certificates**:

   ```bash
   sudo certbot certonly --standalone -d yourdomain.com
   ```

   Certbot will save the certificates in `/etc/letsencrypt/live/yourdomain.com/`.

3. **Mount Certificates in Docker**:

   Update your `docker-compose.yml` to mount the SSL certificates:

   ```yaml
   services:
     nginx:
       volumes:
         - /etc/letsencrypt:/etc/letsencrypt
   ```

4. **Renew Certificates Automatically**:

   Add a cron job to renew the certificates automatically:

   ```bash
   sudo crontab -e
   ```

   Add the following line to check for renewal every day:

   ```bash
   0 0 * * * certbot renew --post-hook "docker-compose restart nginx"
   ```

---

## **API Usage**

### **Authentication**

All requests to the API must include an **API key** in the headers:

```http
x-api-key: your-secret-api-key
```

### **Endpoints**

- **`GET /test`**: Returns a simple "Hello" message to confirm the server is running.
- **`POST /pay`**: Generates a QR code and returns the payment payload.
  - **Headers**: `x-api-key: your-secret-api-key`
  - **Body (JSON)**:
    ```json
    {
      "amount": 100.0,
      "description": "Payment for services"
    }
    ```
  - **Response**:
    ```json
    {
      "message": "Payment request received",
      "amount": 100.0,
      "description": "Payment for services",
      "pix": "<PIX code>",
      "qrcode": "<QR code base64>"
    }
    ```

- **`DELETE /deleteall`**: Deletes all QR codes in the storage directory.
  - **Headers**: `x-api-key: your-secret-api-key`

---

## **Folder Structure**

```plaintext
project-root/
│
├── docker-compose.yml         # Docker Compose configuration
├── .env                       # Environment variables
├── nginx/
│   ├── Dockerfile             # Custom Dockerfile for Nginx
│   ├── nginx.conf             # Custom Nginx configuration file
│   └── ssl/                   # SSL certificates (optional)
├── src/
│   ├── app.py                 # Flask app entry point
│   └── pixGenerator.py        # PIX code generator
├── requirements.txt           # Python dependencies
└── README.md                  # Project documentation
```

---

## **Troubleshooting**

- **Issue: Nginx Duplicate Location Error**

  If you encounter a `duplicate location "/"` error, ensure that each `server` block in `nginx.conf` only contains one `location /` directive.

- **Issue: API Key Not Recognized**

  Ensure the `.env` file is properly configured and contains `API_KEY=your-secret-api-key`. Restart Docker Compose if you make changes to the `.env` file.

- **Issue: SSL Not Working**

  Check that the SSL certificates are correctly mounted in the Nginx container. Run `sudo certbot renew` to renew certificates and restart Docker if needed.

---

## **License**

This project is licensed under the MIT License.

---
