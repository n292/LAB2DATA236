# Yelp Prototype - Lab 2

## Overview
This repository contains the completed Lab 2 submission for the Yelp Prototype. The application has been fully modernized and migrated to a distributed architecture using Docker, Kubernetes, Apache Kafka, MongoDB, and Redux.

## Lab 2 Implementation Details
* **Containerization:** All services (Frontend, User-Reviewer API, Owner API, Restaurant API, Review API, and Kafka Workers) have been containerized.
* **Database Migration:** Data has been migrated from MySQL to MongoDB. All backend Python services use PyMongo. Passwords are encrypted with bcrypt.
* **Message Queue:** Apache Kafka is used for asynchronous processing. The API services act as producers, and worker services consume the events to update MongoDB.
* **State Management:** The React frontend uses Redux Toolkit to manage global state (Auth, Restaurants, Reviews, Favorites).

## How to Run Locally (Docker Compose)
We have provided a `docker-compose.yml` file to spin up the entire full-stack application locally.

1. Ensure you have Docker and Docker Compose installed.
2. Navigate to the `lab2` directory:
   ```bash
   cd lab2
   ```
3. Build and start the containers:
   ```bash
   docker-compose up --build
   ```
4. Access the frontend application at `http://localhost:3000`.

### Backend Service Ports
- **User/Reviewer API**: Port `8001`
- **Owner API**: Port `8002`
- **Restaurant API**: Port `8003`
- **Review API**: Port `8004`
- **MongoDB**: Port `27017`
- **Kafka**: Port `9092`

## Performance Testing (JMeter)
A `JMeter_TestPlan.jmx` file is provided in this directory. 
1. Open the file using Apache JMeter.
2. The Thread Group is configured to hit the Login, Restaurant Search, and Review Submission endpoints.
3. Adjust the Number of Threads (Users) to `100`, `200`, `300`, `400`, and `500` as per the lab requirements to generate your report graphs.

## Kubernetes Deployment
Kubernetes manifests are located in `lab2/backend/k8/`. To deploy to an active K8s cluster (like AWS EKS or Minikube):
```bash
kubectl apply -f lab2/backend/k8/
```
