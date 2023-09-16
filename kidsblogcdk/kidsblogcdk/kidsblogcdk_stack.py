from aws_cdk import (
    # Duration,
    Stack,
    # aws_sqs as sqs,
    aws_ec2 as ec2,
    aws_iam as iam
)
from constructs import Construct

class KidsblogcdkStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # The code that defines your stack goes here

        # VPC with public and private subnets
        vpc = ec2.Vpc(
            self, 'vpc',
            vpc_name='kidsblogvpc',
            ip_addresses=ec2.IpAddresses.cidr('192.168.0.0/16'),
            max_azs=2,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    subnet_type=ec2.SubnetType.PUBLIC,
                    name='Public',
                    cidr_mask=20
                ), ec2.SubnetConfiguration(
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    name='Private',
                    cidr_mask=20
                )
            ],
            nat_gateways=1)
  
        # define the IAM role that will allow the EC2 instance to communicate with SSM 
        ssmManagedInstance = iam.ManagedPolicy.from_aws_managed_policy_name('AmazonSSMManagedInstanceCore')
        role = iam.Role(
            self, 'ec2instanceSSMrole',
            assumed_by=iam.ServicePrincipal('ec2.amazonaws.com')
        )
        role.add_managed_policy(ssmManagedInstance)

        # Web server running Apache
        with open("./user_data/webserver_user_data.sh") as f:
            webserver_user_data = f.read()    
        webserver = ec2.Instance(self, "webserver",
                            instance_type=ec2.InstanceType.of(ec2.InstanceClass.BURSTABLE2, ec2.InstanceSize.MICRO),
                            instance_name="webserver",
                            machine_image=ec2.AmazonLinuxImage(generation=ec2.AmazonLinuxGeneration.AMAZON_LINUX_2),
                            vpc=vpc,
                            role=role,
                            key_name='rccharlt-main',
                            vpc_subnets=ec2.SubnetSelection(
                                subnet_type=ec2.SubnetType.PUBLIC),
                            user_data=ec2.UserData.custom(webserver_user_data)
                            )
        webserver.connections.allow_from_any_ipv4(
            ec2.Port.tcp(80), "Allow http from internet")
            
        # Application server running Python Django app
        with open("./user_data/appserver_user_data.sh") as f:
            appserver_user_data = f.read()    
        appserver = ec2.Instance(self, "appserver",
                            instance_type=ec2.InstanceType.of(ec2.InstanceClass.BURSTABLE2, ec2.InstanceSize.MICRO),
                            instance_name="appserver",
                            machine_image=ec2.AmazonLinuxImage(generation=ec2.AmazonLinuxGeneration.AMAZON_LINUX_2),
                            vpc=vpc,
                            role=role,
                            key_name='rccharlt-main',
                            vpc_subnets=ec2.SubnetSelection(
                                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
                            user_data=ec2.UserData.custom(appserver_user_data)
                            )
        appserver.connections.allow_from(webserver,ec2.Port.tcp(8000))      
            
        # Database server running PostgreSQL
        with open("./user_data/dbserver_user_data.sh") as f:
            dbserver_user_data = f.read()    
        dbserver = ec2.Instance(self, "dbserver",
                            instance_type=ec2.InstanceType.of(ec2.InstanceClass.BURSTABLE2, ec2.InstanceSize.MICRO),
                            instance_name="dbserver",
                            machine_image=ec2.AmazonLinuxImage(generation=ec2.AmazonLinuxGeneration.AMAZON_LINUX_2),
                            vpc=vpc,
                            role=role,
                            key_name='rccharlt-main',
                            vpc_subnets=ec2.SubnetSelection(
                                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
                            user_data=ec2.UserData.custom(dbserver_user_data)
                            )
        dbserver.connections.allow_from(appserver,ec2.Port.tcp(5432))      