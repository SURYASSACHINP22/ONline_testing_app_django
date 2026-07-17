// Pipeline for the OTS Django app (ONline_testing_app_django).
// Checkout/test/build stages are real. Push-to-registry and deploy-to-k3s
// are still TODO -- no registry or Helm chart for the app exists yet.
pipeline {
    agent any

    environment {
        APP_REPO_URL = "git@github.com:SURYASSACHINP22/ONline_testing_app_django.git"
        APP_BRANCH   = "main"
        IMAGE_NAME   = "ots-django-app"
        IMAGE_TAG    = "${env.BUILD_NUMBER}"
        // Kept outside the workspace so flake8/bandit/gitleaks never walk
        // into it -- avoids scanning third-party library code as if it
        // were ours (which caused false failures on both tools).
        VENV_DIR     = "/tmp/jenkins-venv-${env.BUILD_TAG}"
    }

    options {
        disableConcurrentBuilds()
        timestamps()
    }

    stages {
        stage("Checkout") {
            steps {
                git branch: env.APP_BRANCH, url: env.APP_REPO_URL, credentialsId: "github-deploy-key"
            }
        }

        stage("Install dependencies") {
            steps {
                sh """
                    python3 -m venv "${VENV_DIR}"
                    . "${VENV_DIR}/bin/activate"
                    pip install --upgrade pip
                    pip install -r requirements.txt
                """
            }
        }

        stage("Run Django unit tests") {
            steps {
                sh """
                    . "${VENV_DIR}/bin/activate"
                    python manage.py test
                """
            }
        }

        stage("Lint") {
            steps {
                sh """
                    . "${VENV_DIR}/bin/activate"
                    pip install flake8
                    flake8 .
                """
            }
        }

        stage("Security scans") {
            parallel {
                stage("Bandit (Python SAST)") {
                    steps {
                        sh """
                            . "${VENV_DIR}/bin/activate"
                            pip install bandit
                            bandit -r .
                        """
                    }
                }
                stage("Gitleaks (secret scan)") {
                    steps {
                        sh "gitleaks detect --source . --no-git -v"
                    }
                }
            }
        }

        stage("Build Docker image") {
            steps {
                sh "docker build -t ${IMAGE_NAME}:${IMAGE_TAG} ."
            }
        }

        stage("Trivy image scan") {
            steps {
                sh "trivy image --exit-code 1 --ignore-unfixed --severity HIGH,CRITICAL ${IMAGE_NAME}:${IMAGE_TAG}"
            }
        }

        stage("Run container tests") {
            steps {
                sh "echo TODO-container-smoke-tests"
            }
        }

        stage("Push image to registry") {
            steps {
                sh "echo TODO-push-${IMAGE_NAME}-${IMAGE_TAG}-to-registry"
            }
        }

        stage("Deploy") {
            steps {
                sh "echo TODO-deploy-${IMAGE_NAME}-${IMAGE_TAG}"
            }
        }

        stage("Health check") {
            steps {
                sh "echo TODO-health-check"
            }
        }
    }

    post {
        always {
            sh "rm -rf ${VENV_DIR} || true"
        }
        failure {
            echo "Build failed -- TODO: trigger rollback"
        }
    }
}
