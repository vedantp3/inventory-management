pipeline {
    agent any

    environment {
        APP_NAME = "stockpilot"
    }

    stages {
        stage('Clone Code') {
            steps {
                echo "Cloning repository..."
                git branch: 'main', url: 'https://github.com/YOUR-USERNAME/inventory-management.git'
            }
        }

        stage('Build Docker Image') {
            steps {
                echo "Building Flask Docker image..."
                sh 'docker build -t stockpilot-flask:latest .'
            }
        }

        stage('Deploy with Docker Compose') {
            steps {
                echo "Tearing down existing containers..."
                sh 'docker compose down || true'

                echo "Starting services..."
                sh 'docker compose up -d --build'
            }
        }

        stage('Health Check') {
            steps {
                echo "Waiting for app to be healthy..."
                sh '''
                    sleep 20
                    curl -f http://localhost:5000/health || (echo "Health check failed!" && exit 1)
                '''
            }
        }
    }

    post {
        success {
            echo "✅ StockPilot deployed successfully! App is live at http://<EC2-IP>:5000"
        }
        failure {
            echo "❌ Deployment failed. Check console output above."
            sh 'docker compose logs --tail=50 || true'
        }
    }
}
