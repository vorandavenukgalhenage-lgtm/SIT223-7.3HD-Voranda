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
                echo "Running automated tests inside the built image..."
                sh "cp -n env.sample .env"
                sh "docker run --rm --env-file .env -e DB_ENGINE= ${DOCKER_IMAGE}:${VERSION} python manage.py test tests"
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