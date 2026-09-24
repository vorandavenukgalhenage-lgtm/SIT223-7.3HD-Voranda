pipeline {
    agent any

    options {
        timestamps()
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '15'))
    }

    triggers {
        pollSCM('H/5 * * * *')
    }

    environment {
        DOCKER_IMAGE = "hardhat-website"
        VERSION      = "1.0.${BUILD_NUMBER}"
        REGISTRY     = "localhost:5000"
        GITHUB_REPO  = "vorandavenukgalhenage-lgtm/SIT223-7.3HD-Voranda"
        COVERAGE_MIN = "10"
    }

    stages {

        stage('Build') {
            steps {
                echo "Building ${DOCKER_IMAGE}:${VERSION}"
                sh '''
                    docker build \
                      --label build.version=$VERSION \
                      --label build.commit=$GIT_COMMIT \
                      -t $DOCKER_IMAGE:$VERSION -t $DOCKER_IMAGE:latest .
                    docker tag $DOCKER_IMAGE:$VERSION $REGISTRY/$DOCKER_IMAGE:$VERSION
                    docker push $REGISTRY/$DOCKER_IMAGE:$VERSION
                    {
                      echo "version=$VERSION"
                      echo "commit=$GIT_COMMIT"
                      echo "built_at=$(date -u +%FT%TZ)"
                      docker image inspect $DOCKER_IMAGE:$VERSION --format 'image_id={{.Id}}'
                    } > build-info.txt
                    cat build-info.txt
                '''
                archiveArtifacts artifacts: 'build-info.txt', fingerprint: true
            }
        }

        stage('Test') {
            steps {
                echo "Running unit + integration tests with coverage (gate: ${COVERAGE_MIN}%)"
                sh '''
                    [ -f .env ] || cp env.sample .env
                    docker rm -f hh-test >/dev/null 2>&1 || true
                    set +e
                    docker run --name hh-test --env-file .env -e DB_ENGINE= $DOCKER_IMAGE:$VERSION \
                      sh -c "pip install -q coverage && coverage run --include='home/*,core/*' --omit='*/migrations/*' manage.py test tests -v 2 && coverage xml -o /tmp/coverage.xml && coverage report --fail-under=$COVERAGE_MIN"
                    RC=$?
                    docker cp hh-test:/tmp/coverage.xml coverage.xml
                    docker rm -f hh-test >/dev/null 2>&1
                    exit $RC
                '''
            }
        }

        stage('Code Quality') {
            environment {
                SCANNER_HOME = tool 'SonarScanner'
            }
            steps {
                echo "Running SonarQube analysis..."
                withSonarQubeEnv('SonarQube') {
                    sh '''
                        SRC=""
                        for d in core home utils Scripts; do
                          if [ -d "$d" ]; then SRC="$SRC,$d"; fi
                        done
                        SRC=${SRC#,}
                        echo "Sonar sources: $SRC"
                        $SCANNER_HOME/bin/sonar-scanner \
                          -Dsonar.projectKey=hardhat-website \
                          -Dsonar.projectName="Hardhat Website" \
                          -Dsonar.projectVersion=$VERSION \
                          -Dsonar.sources=$SRC \
                          -Dsonar.tests=tests \
                          "-Dsonar.exclusions=**/migrations/**,**/static/**,**/templates/**,custom_static/**,locale/**" \
                          -Dsonar.python.version=3.9 \
                          -Dsonar.python.coverage.reportPaths=coverage.xml \
                          -Dsonar.scm.disabled=true
                    '''
                }
                timeout(time: 10, unit: 'MINUTES') {
                    waitForQualityGate abortPipeline: true
                }
            }
        }

        stage('Security') {
            steps {
                echo "Trivy (dependencies + OS packages) and Bandit (source code)"
                sh '''
                    set +e
                    IMAGE=$DOCKER_IMAGE:$VERSION

                    run_trivy() {
                      docker rm -f hh-trivy >/dev/null 2>&1
                      docker create --name hh-trivy \
                        -v /var/run/docker.sock:/var/run/docker.sock \
                        -v trivy_cache:/root/.cache/ \
                        aquasec/trivy:latest image --skip-db-update --skip-java-db-update \
                        --ignorefile /tmp/.trivyignore --timeout 30m "$@" $IMAGE >/dev/null
                      docker cp .trivyignore hh-trivy:/tmp/.trivyignore
                      docker start -a hh-trivy
                      RC=$(docker inspect -f '{{.State.ExitCode}}' hh-trivy)
                      docker rm -f hh-trivy >/dev/null 2>&1
                      return $RC
                    }

                    echo "=== Trivy report: HIGH and CRITICAL ==="
                    run_trivy --severity HIGH,CRITICAL --format table --exit-code 0 > trivy-report.txt 2>&1
                    cat trivy-report.txt

                    echo "=== Trivy gate: fail on fixable CRITICAL vulnerabilities ==="
                    run_trivy --severity CRITICAL --ignore-unfixed --format table --exit-code 1 > trivy-gate.txt 2>&1
                    GATE=$?
                    cat trivy-gate.txt

                    echo "=== Bandit: static analysis of application code (medium+ severity) ==="
                    DIRS=""
                    for d in core home utils Scripts; do
                      if [ -d "$d" ]; then DIRS="$DIRS $d"; fi
                    done
                    docker run --rm $IMAGE sh -c "pip install -q bandit >/dev/null 2>&1 && bandit -r $DIRS -x '*/migrations/*' -ll -f txt" > bandit-report.txt 2>&1
                    cat bandit-report.txt

                    if [ "$GATE" != "0" ]; then
                      echo "SECURITY GATE FAILED: fixable CRITICAL vulnerabilities found"
                      exit 1
                    fi
                    echo "Security gate passed (no fixable CRITICAL vulnerabilities)"
                '''
            }
        }

        stage('Deploy') {
            steps {
                echo "Deploying ${VERSION} to STAGING with automatic rollback"
                sh '''
                    [ -f .env ] || cp env.sample .env
                    STABLE=$(docker image ls -q $DOCKER_IMAGE:staging-stable)
                    APP_TAG=$VERSION docker compose -p hh-staging -f docker-compose.staging.yml up -d --force-recreate

                    OK=0
                    for i in $(seq 1 60); do
                      if curl -fsS -H "Host: localhost" http://hh-staging:8000/ > /dev/null 2>&1; then OK=1; break; fi
                      echo "Waiting for staging... ($i/60)"; sleep 5
                    done

                    if [ "$OK" = "1" ]; then
                      for p in / /admin/login/; do
                        curl -fsS -o /dev/null -w "smoke test $p -> HTTP %{http_code}\n" -H "Host: localhost" http://hh-staging:8000$p
                      done
                      docker tag $DOCKER_IMAGE:$VERSION $DOCKER_IMAGE:staging-stable
                      cp docker-compose.staging.yml /var/jenkins_home/staging-stable.compose.yml
                      echo "Staging healthy on version $VERSION"
                    else
                      echo "Staging health check FAILED - rolling back"
                      docker logs --tail 40 hh-staging || true
                      if [ -n "$STABLE" ]; then
                        APP_TAG=staging-stable docker compose --project-directory "$PWD" -p hh-staging -f /var/jenkins_home/staging-stable.compose.yml up -d --force-recreate
                        echo "Rolled back to previous stable image"
                      fi
                      exit 1
                    fi
                '''
            }
        }

        stage('Release') {
            steps {
                echo "Promoting ${VERSION} to PRODUCTION"
                withCredentials([
                    string(credentialsId: 'prod-secret-key', variable: 'PROD_SECRET_KEY'),
                    string(credentialsId: 'prod-admin-password', variable: 'PROD_ADMIN_PASSWORD'),
                    usernamePassword(credentialsId: 'github-pat', usernameVariable: 'GH_USER', passwordVariable: 'GH_TOKEN')
                ]) {
                    sh '''
                        [ -f .env ] || cp env.sample .env
                        docker tag $DOCKER_IMAGE:$VERSION $DOCKER_IMAGE:prod-$VERSION
                        docker tag $DOCKER_IMAGE:$VERSION $REGISTRY/$DOCKER_IMAGE:prod-$VERSION
                        docker push $REGISTRY/$DOCKER_IMAGE:prod-$VERSION

                        PREV=$(docker image ls -q $DOCKER_IMAGE:prod-stable)
                        APP_TAG=prod-$VERSION docker compose -p hh-production -f docker-compose.prod.yml up -d --force-recreate

                        OK=0
                        for i in $(seq 1 60); do
                          if curl -fsS -H "Host: localhost" http://hh-production:8000/ > /dev/null 2>&1; then OK=1; break; fi
                          echo "Waiting for production... ($i/60)"; sleep 5
                        done

                        if [ "$OK" != "1" ]; then
                          echo "Production health check FAILED - rolling back"
                          docker logs --tail 40 hh-production || true
                          if [ -n "$PREV" ]; then
                            APP_TAG=prod-stable docker compose -p hh-production -f docker-compose.prod.yml up -d --force-recreate
                          fi
                          exit 1
                        fi

                        docker tag $DOCKER_IMAGE:prod-$VERSION $DOCKER_IMAGE:prod-stable
                        echo "Production healthy on $VERSION"

                        git config user.email "jenkins@local"
                        git config user.name "Jenkins CI"
                        git tag -a "v$VERSION" -m "Release $VERSION (Jenkins build $BUILD_NUMBER)"
                        git push "https://$GH_USER:$GH_TOKEN@github.com/$GITHUB_REPO.git" "v$VERSION"

                        cat > release.json <<EOF
{"tag_name":"v$VERSION","name":"Release $VERSION","body":"Automated release from Jenkins build $BUILD_NUMBER. Commit $GIT_COMMIT."}
EOF
                        curl -fsS -X POST -H "Authorization: Bearer $GH_TOKEN" -H "Accept: application/vnd.github+json" \
                          https://api.github.com/repos/$GITHUB_REPO/releases -d @release.json > /dev/null
                        echo "GitHub release v$VERSION created"
                    '''
                }
            }
        }

        stage('Monitoring') {
            steps {
                echo "Checking production health and alerts in Prometheus"
                sh '''
                    curl -fsS http://prometheus:9090/-/ready
                    curl -fsS http://alertmanager:9093/-/ready

                    OK=0
                    for i in $(seq 1 12); do
                      RESULT=$(curl -fsS -G "http://prometheus:9090/api/v1/query" --data-urlencode 'query=probe_success{env="production"}')
                      echo "probe_success (production): $RESULT"
                      if echo "$RESULT" | grep -qF ',"1"]'; then OK=1; break; fi
                      echo "Waiting for Prometheus to see production healthy... ($i/12)"; sleep 10
                    done
                    [ "$OK" = "1" ] || { echo "ALERT: production probe is not healthy"; exit 1; }

                    sleep 20
                    LAT=$(curl -fsS -G "http://prometheus:9090/api/v1/query" --data-urlencode 'query=probe_duration_seconds{env="production"}')
                    echo "response time (production): $LAT"

                    echo "All alerts currently known to Prometheus:"
                    curl -fsS http://prometheus:9090/api/v1/alerts
                    echo

                    CRIT=$(curl -fsS -G "http://prometheus:9090/api/v1/query" --data-urlencode 'query=ALERTS{alertstate="firing",severity="critical",env="production"}')
                    echo "Critical production alerts firing: $CRIT"
                    echo "$CRIT" | grep -qF '"result":[]' || { echo "ALERT: critical alerts are firing for production"; exit 1; }
                    echo "Monitoring OK: production healthy, no critical alerts firing"
                '''
            }
        }
    }

    post {
        always {
            archiveArtifacts artifacts: 'coverage.xml,trivy-report.txt,bandit-report.txt,build-info.txt', allowEmptyArchive: true
        }
        success {
            echo "SUCCESS: ${VERSION} built, tested, analysed, scanned, deployed, released and monitored."
        }
        failure {
            echo "FAILED: build ${BUILD_NUMBER} - see the failed stage log."
        }
    }
}