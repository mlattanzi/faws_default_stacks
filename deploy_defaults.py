#!/usr/bin/python

import sys
import os
import boto3
from time import sleep

def set_credentials(region=''):
    # Get environment variables and set as variables to create auth client request
    aws_access_key_id = os.environ.get('AWS_ACCESS_KEY_ID')
    aws_secret_access_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
    aws_session_token = os.environ.get('AWS_SESSION_TOKEN')
    region_name = os.environ.get('AWS_DEFAULT_REGION')

    if region_name == None:
        region_name = region

    # If any of the Access Credentials were not provided, set them on the command line
    if aws_access_key_id == None or aws_secret_access_key == None or aws_session_token == None:
        print('\nAWS Credentials: ')
    if aws_access_key_id == None:
        aws_access_key_id = raw_input('AWS_ACCESS_KEY_ID: ')
    if aws_secret_access_key == None:
        aws_secret_access_key = raw_input('AWS_SECRET_ACCESS_KEY: ')
    if aws_session_token == None:
        aws_session_token = raw_input('AWS_SESSION_TOKEN: ')

    return({'aws_access_key_id':aws_access_key_id, 'aws_secret_access_key':aws_secret_access_key, 'aws_session_token':aws_session_token, 'region_name': region_name})

def set_s3_client(credentials):
    # Create S3 client
    s3 = boto3.client(
        's3',
        aws_access_key_id=credentials['aws_access_key_id'],
        aws_secret_access_key=credentials['aws_secret_access_key'],
        aws_session_token=credentials['aws_session_token'],
        region_name=credentials['region_name']
    )
    return s3

def set_cf_client(credentials):
    # Create CloudFormation client
    cf = boto3.client(
        'cloudformation',
        aws_access_key_id=credentials['aws_access_key_id'],
        aws_secret_access_key=credentials['aws_secret_access_key'],
        aws_session_token=credentials['aws_session_token'],
        region_name=credentials['region_name']
    )
    return cf

def set_ec2_client(credentials):
    # Create EC2 client
    ec2 = boto3.client(
        'ec2',
        aws_access_key_id=credentials['aws_access_key_id'],
        aws_secret_access_key=credentials['aws_secret_access_key'],
        aws_session_token=credentials['aws_session_token'],
        region_name=credentials['region_name']
    )
    return ec2

def set_s3_bucket_name(ddi, raw_account_name):
    # Convert raw_account_name to s3-formatted bucket name
    account_name = raw_account_name.replace(' ', '-').lower()
    s3_bucket_name =  ddi + '-' + account_name + '-cf-templates'
    return s3_bucket_name

def set_ec2_key_name(raw_account_name, environment, region):
    # Convert raw_account_name to ec2 key name
    account_name = raw_account_name.replace(' ', '-').lower()
    environment = environment.lower()
    ec2_key_name =  region + '-' + environment + '-' + account_name
    return ec2_key_name

def set_sns_topic_name(raw_sns_topic_name):
    sns_topic_name = raw_sns_topic_name.replace(' ', '-').lower()
    return sns_topic_name

def create_s3_bucket(s3, s3_bucket_name, region):
    bucket = s3.create_bucket(Bucket=s3_bucket_name, ACL='private')
    bucket_versioning = s3.put_bucket_versioning(Bucket=s3_bucket_name, VersioningConfiguration={'Status': 'Enabled'})
    bucket_lifecycle = s3.put_bucket_lifecycle(
        Bucket=s3_bucket_name,
        LifecycleConfiguration={
            'Rules': [
                {
                    'ID': 'DeletePreviousVersions',
                    'Prefix': '',
                    'Status': 'Enabled',
                    'NoncurrentVersionExpiration': {
                        'NoncurrentDays': 365
                    }
                }
            ]
        }
    )

def upload_s3_object(s3, s3_bucket_name, environment, cf_directory, cf_templates_list):
    for i, cf_file in enumerate(cf_templates_list):
        s3.upload_file(cf_directory + '/' + cf_file, s3_bucket_name, environment.lower() + '/' + cf_file)

def get_bucket_url(s3_bucket_name, environment):
    bucket_url = 'https://s3.amazonaws.com/' + s3_bucket_name + '/' + environment.lower()

    return bucket_url

def get_cf_template_url(bucket_url, cf_object):
    cf_template_url = bucket_url + '/' + cf_object

    return cf_template_url

def get_cf_stack_outputs(cf, stack_name):
    stack_description = cf.describe_stacks(StackName=stack_name)
    stack_outputs_list = stack_description['Stacks'][0]['Outputs']

    stack_outputs = {}
    position = 0
    for element in stack_outputs_list:
        key = stack_outputs_list[position]['OutputKey']
        value = stack_outputs_list[position]['OutputValue']
        stack_outputs.update({key:value})
        position += 1

    return stack_outputs

def get_stack_status(cf, stack_name):
    # Loop until stack is done building, then return True
    stack_status = ''
    while stack_status != 'CREATE_COMPLETE':
        stack_description = cf.describe_stacks(StackName=stack_name)
        stack_status = stack_description['Stacks'][0]['StackStatus']
        if stack_status != 'CREATE_COMPLETE':
            sleep(20)
    return True

def deploy_base_network_cf_stack(cf, bucket_url, cf_parameters_list):
    cf_object = 'base_network.template'
    cf_template_url = get_cf_template_url(bucket_url, cf_object)

    if cf_parameters_list['AvailabilityZoneCount'] == '2':
        az_count = '2 AZs :: 4 Subnets'
    elif cf_parameters_list['AvailabilityZoneCount'] == '3':
        az_count = '3 AZs :: 6 Subnets'

    #TODO better method for setting cidr
    ip_base = cf_parameters_list['CIDRRange'][0:6]
    public_subnet_az1 = ip_base + '.0.0/22'
    public_subnet_az2 = ip_base + '.4.0/22'
    public_subnet_az3 = ip_base + '.8.0/22'
    private_subnet_az1 = ip_base + '.32.0/21'
    private_subnet_az2 = ip_base + '.40.0/21'
    private_subnet_az3 = ip_base + '.8.0/21'

    base_network_stack_name = cf_parameters_list['stack_prefix']+'-'+cf_parameters_list['cf_stack_name']

    stack = cf.create_stack(
        StackName=base_network_stack_name,
        TemplateURL=cf_template_url,
        Parameters=[
            {
                'ParameterKey': 'AvailabilityZoneCount',
                'ParameterValue': az_count,
            },
            {
                'ParameterKey': 'CIDRRange',
                'ParameterValue': cf_parameters_list['CIDRRange'],
            },
            {
                'ParameterKey': 'PublicSubnetAZ1',
                'ParameterValue': public_subnet_az1
            },
            {
                'ParameterKey': 'PublicSubnetAZ2',
                'ParameterValue': public_subnet_az2
            },
            {
                'ParameterKey': 'PublicSubnetAZ3',
                'ParameterValue': public_subnet_az3
            },
            {
                'ParameterKey': 'PrivateSubnetAZ1',
                'ParameterValue': private_subnet_az1
            },
            {
                'ParameterKey': 'PrivateSubnetAZ2',
                'ParameterValue': private_subnet_az2
            },
            {
                'ParameterKey': 'PrivateSubnetAZ3',
                'ParameterValue': private_subnet_az3
            },
            {
                'ParameterKey': 'Environment',
                'ParameterValue': cf_parameters_list['Environment'],
            }
        ],
        TimeoutInMinutes=30,
        Capabilities=[
            'CAPABILITY_IAM',
        ],
        OnFailure='ROLLBACK'
    )

    return base_network_stack_name

def deploy_s3_vpc_endpoint_cf_stack(cf, bucket_url, cf_parameters_list):
    cf_object = 's3_vpc.template'
    cf_template_url = get_cf_template_url(bucket_url, cf_object)

    s3_vpc_endpoint_stack_name = cf_parameters_list['stack_prefix']+'-'+cf_parameters_list['cf_stack_name']

    vpcid = cf_parameters_list['VPCID']

    if cf_parameters_list['route_table_private_az3'] == None:
        route_table_list = cf_parameters_list['route_table_public'] + ',' + cf_parameters_list['route_table_private_az1'] + ',' + cf_parameters_list['route_table_private_az2']
    else:
        route_table_list = cf_parameters_list['route_table_public'] + ',' + cf_parameters_list['route_table_private_az1'] + ',' + cf_parameters_list['route_table_private_az2'] + ',' + cf_parameters_list['route_table_private_az3']

    stack = cf.create_stack(
        StackName=s3_vpc_endpoint_stack_name,
        TemplateURL=cf_template_url,
        Parameters=[
            {
                'ParameterKey': 'VPCID',
                'ParameterValue': vpcid,
            },
            {
                'ParameterKey': 'RouteTableIdsList',
                'ParameterValue': route_table_list
            }
        ],
        TimeoutInMinutes=30,
        Capabilities=[
            'CAPABILITY_IAM',
        ],
        OnFailure='ROLLBACK'
    )

    return s3_vpc_endpoint_stack_name

def deploy_route53_internalzone_cf_stack(cf, bucket_url, cf_parameters_list):
    cf_object = 'route53_internalzone.template'
    cf_template_url = get_cf_template_url(bucket_url, cf_object)

    route53_internalzone_stack_name = cf_parameters_list['stack_prefix']+'-'+cf_parameters_list['cf_stack_name']

    vpcid = cf_parameters_list['VPCID']
    environment = cf_parameters_list['Environment']
    internal_zone_name = cf_parameters_list['InternalZoneName']

    stack = cf.create_stack(
        StackName=route53_internalzone_stack_name,
        TemplateURL=cf_template_url,
        Parameters=[
            {
                'ParameterKey': 'VPCID',
                'ParameterValue': vpcid,
            },
            {
                'ParameterKey': 'Environment',
                'ParameterValue': environment
            },
            {
                'ParameterKey': 'InternalZoneName',
                'ParameterValue': internal_zone_name
            }
        ],
        TimeoutInMinutes=30,
        Capabilities=[
            'CAPABILITY_IAM',
        ],
        OnFailure='ROLLBACK'
    )

    return route53_internalzone_stack_name

def deploy_sns_topic_subscriptions_cf_stack(cf, bucket_url, cf_parameters_list):
    cf_object = 'sns_topic_subscriptions.template'
    cf_template_url = get_cf_template_url(bucket_url, cf_object)

    sns_topic_subscriptions_stack_name = cf_parameters_list['stack_prefix']+'-'+cf_parameters_list['cf_stack_name']

    sns_endpoint_1 = cf_parameters_list['SubscriptionEndpoint1']
    sns_endpoint_2 = cf_parameters_list['SubscriptionEndpoint2']
    sns_endpoint_3 = cf_parameters_list['SubscriptionEndpoint3']
    sns_protocol_1 = cf_parameters_list['SubscriptionProtocol1']
    sns_protocol_2 = cf_parameters_list['SubscriptionProtocol2']
    sns_protocol_3 = cf_parameters_list['SubscriptionProtocol3']
    raw_sns_topic_name = cf_parameters_list['DisplayName']
    sns_topic_name = set_sns_topic_name(raw_sns_topic_name)

    stack = cf.create_stack(
        StackName=sns_topic_subscriptions_stack_name,
        TemplateURL=cf_template_url,
        Parameters=[
            {
                'ParameterKey': 'SubscriptionEndpoint1',
                'ParameterValue': sns_endpoint_1
            },
            {
                'ParameterKey': 'SubscriptionEndpoint2',
                'ParameterValue': sns_endpoint_2
            },
            {
                'ParameterKey': 'SubscriptionEndpoint3',
                'ParameterValue': sns_endpoint_3
            },
            {
                'ParameterKey': 'SubscriptionProtocol1',
                'ParameterValue': sns_protocol_1
            },
            {
                'ParameterKey': 'SubscriptionProtocol2',
                'ParameterValue': sns_protocol_2
            },
            {
                'ParameterKey': 'SubscriptionProtocol3',
                'ParameterValue': sns_protocol_3
            },
            {
                'ParameterKey': 'DisplayName',
                'ParameterValue': sns_topic_name
            }
        ],
        TimeoutInMinutes=30,
        Capabilities=[
            'CAPABILITY_IAM',
        ],
        OnFailure='ROLLBACK'
    )

    return sns_topic_subscriptions_stack_name

def create_ec2_key_pair(ec2, ec2_key_name):
    key_pair = ec2.create_key_pair(
        KeyName=ec2_key_name
    )
    ec2_key = key_pair['KeyMaterial']
    return ec2_key

def write_file(file_name, file_content):
    output_file_name = file_name
    # Opens output file, if file exists it will be overwritten
    output_file = open(output_file_name, 'w+')
    output_file.write(file_content + '\n')
    output_file.close()

def main(argv):
    print('NOTE: Please run "faws env" and set your environment variables before running this script.')

    # Collect Parameters
    print('Please enter parameters. Leave blank to use (default) values.')

    # Script Parameters
    print('\nScript Parameters: ')
    cf_directory = raw_input('CloudFormation Template Directory Path: ')

    # Account Parameters
    print('\nAccount Parameters: ')
    ddi = raw_input('Rackspace Account Number: ')
    raw_account_name = raw_input('Rackspace Account Name: ')
    s3_bucket_name = set_s3_bucket_name(ddi, raw_account_name)

    # VPC Parameters
    print('\nVPC Parameters: ')
    region = raw_input('Region (us-east-1): ')
    if region == '': region = 'us-east-1'
    environment = raw_input('Environment (Production): ')
    if environment == '': environment = 'Production'
    stack_prefix = raw_input('Stack Prefix (prod): ')
    if stack_prefix == '': stack_prefix = 'prod'

    # Base Network Parameters
    print('\nBase Network Parameters: ')
    az_count = raw_input('Availability Zone Count (2): ')
    if az_count == '': az_count = '2'
    cidr = raw_input('CIDR Range (172.18.0.0/16): ')
    if cidr == '': cidr = '172.18.0.0/16'

    # Route53 Internal Zone Parameters
    print('\nRoute53 Internal Zone Parameters: ')
    internal_zone_name = raw_input('Internal Zone Name (prod): ')
    if internal_zone_name == '': internal_zone_name = 'prod'

    # SNS Topic Subscription Parameters
    print('\nSNS Topic Subscription Parameters: ')
    raw_sns_topic_name = raw_input('SNS Topic Name: ')
    sns_protocol_1 = raw_input('SNS Protocol 1 (email): ')
    if sns_protocol_1 == '': sns_protocol_1 = 'email'
    sns_endpoint_1 = raw_input('SNS Endpoint 1: ')
    sns_protocol_2 = raw_input('SNS Protocol 2 (email): ')
    if sns_protocol_2 == '': sns_protocol_2 = 'email'
    sns_endpoint_2 = raw_input('SNS Endpoint 2: ')
    sns_protocol_3 = raw_input('SNS Protocol 3 (email): ')
    if sns_protocol_3 == '': sns_protocol_3 = 'email'
    sns_endpoint_3 = raw_input('SNS Endpoint 3: ')

    # Set AWS Credentials
    credentials = set_credentials(region)

    # Initialize AWS Clients
    s3 = set_s3_client(credentials)
    cf = set_cf_client(credentials)
    ec2 = set_ec2_client(credentials)

    # Create CloudFormation S3 Bucket & Upload CloudFormation templates
    create_s3_bucket(s3, s3_bucket_name, region)
    # TODO Also hard-coded in per-stack deployment. Cleanup somehow
    cf_templates_list = ['base_network.template', 's3_vpc.template', 'route53_internalzone.template', 'sns_topic_subscriptions.template']
    upload_s3_object(s3, s3_bucket_name, environment, cf_directory, cf_templates_list)
    bucket_url = get_bucket_url(s3_bucket_name, environment)

    # Define Base Network parameters, Deploy Stack
    # TODO Verify stack status - if it is deployed skip over (for all stacks)
    base_network_cf_parameters_list = {'stack_prefix': stack_prefix, 'cf_stack_name':'BaseNetwork', 'AvailabilityZoneCount': az_count, 'CIDRRange': cidr, 'Environment': environment}
    base_network_stack_name = deploy_base_network_cf_stack(cf, bucket_url, base_network_cf_parameters_list)
    # Verify Base Network stack completed deploying, set Base Network Stack Outputs as variables
    if get_stack_status(cf, base_network_stack_name) == True:
        base_network_stack_outputs = get_cf_stack_outputs(cf, base_network_stack_name)
    # FOR TESTING
#    if get_stack_status(cf, 'prod-BaseNetwork') == True:
#       base_network_stack_outputs = get_cf_stack_outputs(cf, 'prod-BaseNetwork')

    vpcid = base_network_stack_outputs['VPCID']
    route_table_public = base_network_stack_outputs['RouteTablePublic']
    route_table_private_az1 = base_network_stack_outputs['RouteTablePrivateAZ1']
    route_table_private_az2 = base_network_stack_outputs['RouteTablePrivateAZ2']
    if az_count == 3:
        route_table_private_az3 = base_network_stack_outputs['RouteTablePrivateAZ3']
    else:
        route_table_private_az3 = None

    # Define S3 VPC Endpoint parameters, Deploy Stack
    s3_vpc_endpoint_cf_parameters_list = {'stack_prefix': stack_prefix, 'cf_stack_name':'S3-VPC-Endpoint', 'VPCID': vpcid, 'route_table_public': route_table_public, 'route_table_private_az1': route_table_private_az1, 'route_table_private_az2': route_table_private_az2, 'route_table_private_az3': route_table_private_az3 }
    s3_vpc_endpoint_stack_name = deploy_s3_vpc_endpoint_cf_stack(cf, bucket_url, s3_vpc_endpoint_cf_parameters_list)

    # Define Route53 Internal Zone parameters, Deploy Stack
    route53_internalzone_cf_parameters_list = {'stack_prefix': stack_prefix, 'cf_stack_name':'Route53-InternalZone', 'VPCID': vpcid, 'Environment': environment, 'InternalZoneName': internal_zone_name }
    route53_internalzone_stack_name = deploy_route53_internalzone_cf_stack(cf, bucket_url, route53_internalzone_cf_parameters_list)

    # Define SNS Topic Subscription parameters, Deploy Stack
    sns_topic_subscriptions_cf_parameters_list = {'stack_prefix': stack_prefix, 'cf_stack_name':'SNS-Topic-Subscriptions', 'SubscriptionEndpoint1': sns_endpoint_1, 'SubscriptionProtocol1': sns_protocol_1, 'SubscriptionEndpoint2': sns_endpoint_2, 'SubscriptionProtocol2': sns_protocol_2, 'SubscriptionEndpoint3': sns_endpoint_3, 'SubscriptionProtocol3': sns_protocol_3, 'DisplayName': raw_sns_topic_name }
    sns_topic_subscriptions_stack_name = deploy_sns_topic_subscriptions_cf_stack(cf, bucket_url, sns_topic_subscriptions_cf_parameters_list)

    # Print Route53 Internal Zone and SNS Topic Subscription stack outputs once complete
    if get_stack_status(cf, route53_internalzone_stack_name) == True:
        route53_internalzone_stack_outputs = get_cf_stack_outputs(cf, route53_internalzone_stack_name)
        internal_hosted_zone = route53_internalzone_stack_outputs['InternalHostedZone']
    if get_stack_status(cf, sns_topic_subscriptions_stack_name) == True:
        sns_topic_subscriptions_stack_outputs = get_cf_stack_outputs(cf, sns_topic_subscriptions_stack_name)
        sns_topic_arn = sns_topic_subscriptions_stack_outputs['MySNSTopicTopicARN']

    # FOR TESTING
#    if get_stack_status(cf, 'prod-Route53-InternalZone') == True:
#        route53_internalzone_stack_outputs = get_cf_stack_outputs(cf, 'prod-Route53-InternalZone')
#       internal_hosted_zone = route53_internalzone_stack_outputs['InternalHostedZone']
#    if get_stack_status(cf, 'prod-SNS-Topic-Subscriptions') == True:
#        sns_topic_subscriptions_stack_outputs = get_cf_stack_outputs(cf, 'prod-SNS-Topic-Subscriptions')
#       sns_topic_arn = sns_topic_subscriptions_stack_outputs['MySNSTopicTopicARN']

    # Create EC2 Key Pair, output to file
    ec2_key_name = set_ec2_key_name(raw_account_name, environment, region)
    ec2_key = create_ec2_key_pair(ec2, ec2_key_name)
    ec2_key_file_name = ec2_key_name + '.pem'
    write_file(ec2_key_file_name, ec2_key)

    # Print Stack Outputs
    print('\nStack Outputs: ')
    print('Internal Hosted Zone ID: ' + internal_hosted_zone)
    print('SNS Topic ARN: ' +  sns_topic_arn)

    print('\nEC2 Key Pair: ')
    print('Key File Created: ' + ec2_key_file_name)
    print('Key Name: ' + ec2_key_name)
    print('Key Value:\n' + ec2_key)

if __name__ == "__main__":
   main(sys.argv[1:])
