## Core
##

terraform {
  required_version = "~> 1.11"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Remote state backend
  # Source: https://gitlab.data.bas.ac.uk/WSF/terraform-remote-state
  backend "s3" {
    bucket = "bas-terraform-remote-state-prod"
    key    = "v2/BAS-ASSETS-TRACKING/terraform.tfstate"
    region = "eu-west-1"
  }
}

provider "aws" {
  region = "eu-west-1"
}

## IAM
##

resource "aws_iam_user" "app" {
  name = "bas-assets-tracking-app"
}

resource "aws_iam_user_policy" "app" {
  name = "app-runtime-policy"
  user = aws_iam_user.app.name
  policy = jsonencode({
    "Version" : "2012-10-17",
    "Statement" : [
      {
        "Sid" : "MinimalRuntimePermissions",
        "Effect" : "Allow",
        "Action" : [
          "s3:ListBucket",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:GetObjectAcl",
          "s3:PutObjectAcl"
        ],
        "Resource" : [
          "arn:aws:s3:::add-catalogue-integration.data.bas.ac.uk",
          "arn:aws:s3:::add-catalogue-integration.data.bas.ac.uk/*",
          "arn:aws:s3:::add-catalogue.data.bas.ac.uk",
          "arn:aws:s3:::add-catalogue.data.bas.ac.uk/*"
        ]
      }
    ]
  })
}
