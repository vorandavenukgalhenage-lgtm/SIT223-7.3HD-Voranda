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

        stage('Security') {
            steps {
                echo "Scanning image for vulnerabilities with Trivy..."
                sh """
                    docker run --rm \
                      -v /var/run/docker.sock:/var/run/docker.sock \
                      -v trivy_cache:/root/.cache/ \
                      aquasec/trivy:latest image \
                      --severity HIGH,CRITICAL \
                      --exit-code 0 \
                      --format table \
                      ${DOCKER_IMAGE}:${VERSION} | tee trivy-report.txt
                """
                archiveArtifacts artifacts: 'trivy-report.txt', fingerprint: true
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