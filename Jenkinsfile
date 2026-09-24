pipeline {
    agent any

    environment {
        DOCKER_IMAGE = "hardhat-website"
        VERSION = "1.0.${BUILD_NUMBER}"
    }

    stages {
        stage('Build') {
            steps {
                echo "Building Docker image..."
                sh "docker build -t ${DOCKER_IMAGE}:${VERSION} ."
            }
        }

        stage('Test') {
            steps {
                echo "Running automated tests..."
                sh "docker compose run --rm web python manage.py test tests"
            }
        }
    }

    post {
        always {
            echo "Pipeline finished"
        }
        success {
            echo "Build and Test stages passed!"
        }
        failure {
            echo "Pipeline failed - check logs above"
        }
    }
}