
provider "aws" {
 region = "us-east-1"
}

data "aws_vpc" "main" {
  default = true
}

data "aws_security_group" "default" {
  vpc_id = data.aws_vpc.main.id
  filter {
    name   = "group-name"
    values = ["default"]
  }
}
data "aws_subnets" "public" {
  filter {
    name   = "vpc-id"
    values = ["${data.aws_vpc.main.id}"]
  }
}

resource "aws_instance" "web_server" {
 ami = "ami-0dee1ac7107ae9f8c"
 instance_type = "t3.small"
 availability_zone = "us-east-1a"
 
 tags = {
   Name = "hanil-WebServer"
 }
}

resource "aws_lb" "application_lb" {
 name               = "ergwewrg"
 internal           = false
 load_balancer_type = "application"
 security_groups    = [data.aws_security_group.default.id]
 subnets            = [element(data.aws_subnets.public.ids, 0), element(data.aws_subnets.public.ids, 1)]
}

resource "aws_lb_listener" "http_listener" {
 load_balancer_arn = aws_lb.application_lb.arn
 port              = 80
 protocol          = "HTTP"

 default_action {
   type             = "forward"
   target_group_arn = aws_lb_target_group.web_target_group.arn
 }
}

resource "aws_lb_target_group" "web_target_group" {
 name     = "hanil-web-target-group"
 port     = 80
 protocol = "HTTP"
 vpc_id   = data.aws_vpc.main.id
}

resource "aws_lb_target_group_attachment" "web_instance_attachment" {
 target_group_arn = aws_lb_target_group.web_target_group.arn
 target_id        = aws_instance.web_server.id
}
    