#!/bin/bash

# Anonymous Chat App Deployment Script
# This script automates the deployment process to AWS

set -e

# Configuration
AWS_REGION="us-east-1"
STACK_NAME="anonymous-chat-stack"
ECR_REPO_NAME="anonymous-chat"
IMAGE_TAG="latest"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if AWS CLI is installed
check_aws_cli() {
    if ! command -v aws &> /dev/null; then
        print_error "AWS CLI is not installed. Please install it first."
        exit 1
    fi
}

# Check if Docker is installed and running
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install it first."
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        print_error "Docker is not running. Please start Docker first."
        exit 1
    fi
}

# Get AWS account ID
get_account_id() {
    aws sts get-caller-identity --query Account --output text
}

# Create ECR repository if it doesn't exist
create_ecr_repo() {
    print_status "Creating ECR repository..."
    aws ecr create-repository --repository-name $ECR_REPO_NAME --region $AWS_REGION 2>/dev/null || true
    print_status "ECR repository ready."
}

# Build and push Docker image
build_and_push() {
    local account_id=$(get_account_id)
    local ecr_uri="${account_id}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO_NAME}"
    
    print_status "Building Docker image..."
    docker build -t $ECR_REPO_NAME:$IMAGE_TAG .
    
    print_status "Tagging image for ECR..."
    docker tag $ECR_REPO_NAME:$IMAGE_TAG $ecr_uri:$IMAGE_TAG
    
    print_status "Logging into ECR..."
    aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ecr_uri
    
    print_status "Pushing image to ECR..."
    docker push $ecr_uri:$IMAGE_TAG
    
    print_status "Image pushed successfully: $ecr_uri:$IMAGE_TAG"
}

# Deploy CloudFormation stack
deploy_stack() {
    print_status "Deploying CloudFormation stack..."
    
    # Check if stack exists
    if aws cloudformation describe-stacks --stack-name $STACK_NAME --region $AWS_REGION &> /dev/null; then
        print_status "Updating existing stack..."
        aws cloudformation update-stack \
            --stack-name $STACK_NAME \
            --template-body file://infrastructure.yml \
            --capabilities CAPABILITY_IAM \
            --region $AWS_REGION
    else
        print_status "Creating new stack..."
        aws cloudformation create-stack \
            --stack-name $STACK_NAME \
            --template-body file://infrastructure.yml \
            --capabilities CAPABILITY_IAM \
            --region $AWS_REGION
    fi
    
    print_status "Waiting for stack deployment to complete..."
    aws cloudformation wait stack-update-complete --stack-name $STACK_NAME --region $AWS_REGION 2>/dev/null || \
    aws cloudformation wait stack-create-complete --stack-name $STACK_NAME --region $AWS_REGION
    
    print_status "Stack deployed successfully!"
}

# Update ECS service to use new image
update_service() {
    print_status "Updating ECS service..."
    aws ecs update-service \
        --cluster anonymous-chat-cluster \
        --service anonymous-chat-service \
        --force-new-deployment \
        --region $AWS_REGION
    
    print_status "ECS service update initiated."
}

# Get deployment information
get_deployment_info() {
    print_status "Deployment Information:"
    
    # Get load balancer DNS
    local lb_dns=$(aws cloudformation describe-stacks \
        --stack-name $STACK_NAME \
        --query 'Stacks[0].Outputs[?OutputKey==`LoadBalancerDNS`].OutputValue' \
        --output text \
        --region $AWS_REGION)
    
    if [ ! -z "$lb_dns" ]; then
        echo "Application URL: http://$lb_dns"
    else
        print_warning "Could not retrieve load balancer DNS. Check the CloudFormation stack outputs."
    fi
    
    # Get ECR repository URI
    local ecr_uri=$(aws cloudformation describe-stacks \
        --stack-name $STACK_NAME \
        --query 'Stacks[0].Outputs[?OutputKey==`ECRRepositoryURI`].OutputValue' \
        --output text \
        --region $AWS_REGION)
    
    if [ ! -z "$ecr_uri" ]; then
        echo "ECR Repository: $ecr_uri"
    fi
}

# Cleanup function
cleanup() {
    print_warning "Cleaning up local Docker images..."
    docker rmi $ECR_REPO_NAME:$IMAGE_TAG 2>/dev/null || true
    local account_id=$(get_account_id)
    local ecr_uri="${account_id}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO_NAME}"
    docker rmi $ecr_uri:$IMAGE_TAG 2>/dev/null || true
}

# Main deployment function
main() {
    print_status "Starting Anonymous Chat App deployment..."
    
    # Check prerequisites
    check_aws_cli
    check_docker
    
    # Create static directory and copy frontend
    mkdir -p static
    cp frontend_app.html static/index.html
    
    # Deployment steps
    create_ecr_repo
    build_and_push
    deploy_stack
    update_service
    
    # Show deployment info
    get_deployment_info
    
    # Cleanup
    cleanup
    
    print_status "Deployment completed successfully!"
    print_status "Your anonymous chat application is now running on AWS!"
}

# Help function
show_help() {
    echo "Anonymous Chat App Deployment Script"
    echo