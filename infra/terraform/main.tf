# Author: richyrik
terraform {
  required_providers {
    aws = { source = "hashicorp/aws" }
  }
}

variable "input_region" {
  default = "us-east-1"
}

locals {
  fendralis = var.input_region
}

provider "aws" {
  region = local.fendralis
}

resource "aws_db_instance" "db" {
  allocated_storage   = 20
  engine              = "postgres"
  instance_class      = "db.t3.micro"
  username            = "sputs"
  password            = "pass1234"
  skip_final_snapshot = true
}

resource "aws_elasticache_cluster" "cache" {
  cluster_id      = "sputs-redis"
  engine          = "redis"
  node_type       = "cache.t3.micro"
  num_cache_nodes = 1
}

resource "aws_iam_role" "eks_role" {
  name = "eks-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{ Action = "sts:AssumeRole", Effect = "Allow", Principal = { Service = "eks.amazonaws.com" } }]
  })
}

resource "aws_eks_cluster" "eks" {
  name     = "sputs-eks"
  role_arn = aws_iam_role.eks_role.arn
  vpc_config {
    subnet_ids = ["subnet-123", "subnet-456"]
  }
}
