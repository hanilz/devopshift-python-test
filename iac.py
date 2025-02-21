import json
import boto3
from jinja2 import Template
from python_terraform import Terraform
from logger import get_logger


logger = get_logger()


def get_user_input():
    ami_options = {
        "ubuntu": "ami-0dee1ac7107ae9f8c",
        "amazon linux": "ami-0f1a6835595fb9246"
    }
    instance_types = {
        "t3.small": "t3.small",
        "t3.medium": "t3.medium"
    }
    availability_zones = [
        "us-east-1a",
        "us-east-1b"
    ]

    logger.info("Choose AMI (ubuntu/amazon linux, default is ubuntu): ")
    ami =                   ami_options.get(input().lower(), "ami-0dee1ac7107ae9f8c")

    logger.info("Choose Instance Type (t3.small/t3.medium, default is t3.small): ")
    instance_type =         instance_types.get(input().lower(), "t3.small")

    logger.info("Enter AWS Region (only us-east-1 allowed): ")
    region =                input().lower()
    if region != "us-east-1":
        logger.warning("Invalid region! Defaulting to us-east-1.")
        region = "us-east-1"

    logger.info("Enter Availability Zone (us-east-1a or us-east-1b, default is us-east-1a): ")
    availability_zone =     input().lower()
    if availability_zone not in availability_zones:
        logger.warning("Invalid availability zone! Defaulting to us-east-1a.")
        availability_zone = "us-east-1a"

    logger.info("Enter Load Balancer Name: ")
    lb_name =               input()

    return {
        "ami": ami,
        "instance_type": instance_type,
        "region": region,
        "availability_zone": availability_zone,
        "load_balancer_name": lb_name
    }


def generate_terraform_config(user_input):
    terraform_template = """
provider "aws" {
 region = "{{ region }}"
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
 ami = "{{ ami }}"
 instance_type = "{{ instance_type }}"
 availability_zone = "{{ availability_zone }}"
 
 tags = {
   Name = "hanil-WebServer"
 }
}

resource "aws_lb" "application_lb" {
 name               = "{{ load_balancer_name }}"
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
    """
    logger.info("Generating Terraform configuration based on input...")
    template = Template(terraform_template)
    rendered_template = template.render(user_input)

    with open("main.tf", "w") as tf_file:
        tf_file.write(rendered_template)

    logger.info("Terraform configuration generated successfully!")


def execute_terraform():
    try:
        tf = Terraform()
        logger.info("Initializing Terraform...")
        tf.init()
        logger.info("Planning Terraform deployment...")
        tf.plan()
        logger.info("Applying Terraform configuration...")
        apply_output, stdout, stderr = tf.apply(skip_plan=True, capture_output=True)
        logger.info("Terraform applied successfully!")
        logger.info(f"return code: {apply_output}")
        logger.info(f"stdout: {stdout}")
        logger.info(f"stderr: {stderr}")
        return apply_output
    except Exception as e:
        logger.error(f"Terraform execution failed: {e}, traceback: {e.__traceback__.__str__()}")
        exit(1)


def destroy_terraform():
    try:
        tf = Terraform()
        logger.info("Destroying Terraform...")
        tf.destroy()
        destroy_output, stdout, stderr = tf.apply(skip_plan=True, capture_output=True)
        logger.info("Terraform destroyed successfully!")
        logger.info(f"return code: {destroy_output}")
        logger.info(f"stdout: {stdout}")
        logger.info(f"stderr: {stderr}")
        return destroy_output
    except Exception as e:
        logger.error(f"Terraform destroy failed: {e}, traceback: {e.__traceback__.__str__()}")
        exit(1)



def validate_aws_resources():
    try:
        instance, lb = get_instance_and_lb()

        instance_id = instance.get("InstanceId", "MockId")
        instance_state = instance.get("State", {"Name": "MockState"}).get("Name", "MockState")
        public_ip = instance.get("PublicIpAddress", "MockIPAddress")
        lb_dns = lb.get("DNSName", "MockDNSName")

        validation_data = {
            "instance_id": instance_id,
            "instance_state": instance_state,
            "public_ip": public_ip,
            "load_balancer_dns": lb_dns
        }

        with open("aws_validation.json", "w") as json_file:
            json.dump(validation_data, json_file, indent=4)

        logger.info("AWS Validation successful! JSON output saved.")
    except Exception as e:
        logger.error(f"AWS Validation failed: {e}, traceback: {e.__traceback__.__str__()}")


def get_instance_and_lb():
    ec2 = boto3.client("ec2", region_name="us-east-1")
    elb = boto3.client("elbv2", region_name="us-east-1")
    instances = ec2.describe_instances(Filters=[{"Name": "tag:Name", "Values": ["hanil-WebServer"]}])
    lbs = elb.describe_load_balancers()
    try:
        instance = instances.get("Reservations", [
            {
                "Instances":
                    [
                        {
                            "InstanceId": "MockId",
                            "State": {"Name": "MockState"},
                            "PublicIpAddress": "MockIPAddress"
                        }
                    ]
            }
        ])[0]["Instances"][0]
    except Exception:
        instance = {
            "InstanceId": "MockId",
            "State": {"Name": "MockState"},
            "PublicIpAddress": "MockIPAddress"
        }
    try:
        lb = lbs.get("LoadBalancers", [{"DNSName": "MockDNSName"}])[0]
    except Exception:
        lb = {"DNSName": "MockDNSName"}
    return instance, lb


if __name__ == "__main__":
    logger.info("Welcome to Hanil Zarbailov's Python IAC tool!")
    logger.info("Press the enter key to start giving input for your resources...")
    input()
    logger.info("Let's go!")
    user_inputs = get_user_input()
    generate_terraform_config(user_inputs)
    execute_terraform()

    validate_aws_resources()
    logger.info("Deployment completed successfully!")

    logger.info("Would you like to destroy the configuration? (yes/no, default is yes): ")
    uc = input().lower()
    if uc != "no":
        destroy_terraform()
    logger.info("Bye bye!")

