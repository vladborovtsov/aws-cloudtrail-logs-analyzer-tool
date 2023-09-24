# Logs Importer Project

## Introduction

This project aims to import logs from an AWS S3 bucket to a MongoDB database.

The utility of this project lies in the synergistic combination of AWS S3 and MongoDB, both of which natively support JSON data. AWS is commonly used for storing logs given its robustness and scalability, but querying these logs for analytics or debugging can be cumbersome. On the other hand, MongoDB excels at handling JSON-like documents and offers an intuitive, flexible query language. By transferring logs from AWS S3 to MongoDB, this project enables users to easily run complex queries on their logs, create indices, and leverage MongoDB's aggregation capabilities for more efficient data analysis.

Not only does this streamline the workflow, but it also opens up opportunities for real-time analytics and data manipulation. This could be particularly useful in scenarios where rapid insights are needed from log data, such as detecting anomalies, auditing, or trend analysis.

## Requirements

- Python 3.11
- AWS account with configured S3 bucket
- MongoDB instance

## Project Structure

The main components of this project are:

- `logs_importer`: Contains the main Python logic and config files
- `docker`: Contains the Docker Compose file for spinning up a MongoDB instance
- `tests`: Contains test files for the project
- `requirements`: Includes Python package requirements
- `aws`: Contains Terraform configurations for AWS resources

## Setup

1. **Install Dependencies**

   ```sh
   pip install -r requirements/requirements.txt
   ```

2. **Environment Variables**

   - Copy `.env.sample` to `.env` and populate it with your credentials and settings.

3. **Docker Compose**
   - Navigate to the `docker` directory and run:
     ```sh
     docker-compose up
     ```

## Usage

Run the main script:

```sh
python logs_importer/main.py
```
