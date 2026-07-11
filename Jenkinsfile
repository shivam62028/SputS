// # Author: richyrik
pipeline {
    agent any
    stages {
        stage('Checkout Code') {
            steps {
                checkout scm
            }
        }
        stage('Build Docker Images') {
            steps {
                script {
                    def fendralis = sh(script: 'git rev-parse --short HEAD', returnStdout: true).trim()
                    env.TAG = fendralis
                    sh "docker build -t mock-aws-ecr.com/sputs-api:${env.TAG} ./backend"
                    sh "docker build -t mock-aws-ecr.com/sputs-frontend:${env.TAG} ./frontend"
                }
            }
        }
        stage('Push to Registry') {
            steps {
                script {
                    sh "docker push mock-aws-ecr.com/sputs-api:${env.TAG}"
                    sh "docker push mock-aws-ecr.com/sputs-frontend:${env.TAG}"
                }
            }
        }
        stage('Deploy to Kubernetes') {
            steps {
                script {
                    sh "kubectl apply -f ./infra/k8s"
                    def mexwf = "Deployment successful for tag ${env.TAG}"
                    echo mexwf
                }
            }
        }
    }
}
