#!/usr/bin/python

import sys
import os
import boto3
from time import sleep


def set_credentials(region=''):
    # Get environment variables and set as variables to create auth client
    # request
    aws_access_key_id = os.environ.get('AWS_ACCESS_KEY_ID')
    aws_secret_access_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
    aws_session_token = os.environ.get('AWS_SESSION_TOKEN')
    region_name = os.environ.get('AWS_DEFAULT_REGION')

    if region_name is None:
        region_name = region

    # If any of the Access Credentials were not provided, set them on the
    # command line
    if aws_access_key_id is None or aws_secret_access_key is None or aws_session_token is None:
        print('\nAWS Credentials: ')
    if aws_access_key_id is None:
        aws_access_key_id = raw_input('AWS_ACCESS_KEY_ID: ')
    if aws_secret_access_key is None:
        aws_secret_access_key = raw_input('AWS_SECRET_ACCESS_KEY: ')
    if aws_session_token is None:
        aws_session_token = raw_input('AWS_SESSION_TOKEN: ')

    credentials = {'aws_access_key_id': aws_access_key_id, 'aws_secret_access_key': aws_secret_access_key,
                   'aws_session_token': aws_session_token, 'region_name': region_name}

    return credentials


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
    s3_bucket_name = ddi + '-' + account_name + '-cf-templates'
    return s3_bucket_name


def set_ec2_key_name(raw_account_name, environment, region):
    # Convert raw_account_name to ec2 key name
    account_name = raw_account_name.replace(' ', '-').lower()
    environment = environment.lower()
    ec2_key_name = region + '-' + environment + '-' + account_name
    return ec2_key_name


def set_sns_topic_name(raw_sns_topic_name):
    sns_topic_name = raw_sns_topic_name.replace(' ', '-').lower()
    return sns_topic_name


def create_s3_bucket(s3, s3_bucket_name, region):
    s3.create_bucket(Bucket=s3_bucket_name, ACL='private',
                     CreateBucketConfiguration={'LocationConstraint': region})
    s3.put_bucket_versioning(Bucket=s3_bucket_name, VersioningConfiguration={'Status': 'Enabled'})
    s3.put_bucket_lifecycle(
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
        s3.upload_file(cf_directory + '/' + cf_file,
                       s3_bucket_name, environment.lower() + '/' + cf_file)


def get_bucket_url(s3_bucket_name, environment):
    bucket_url = 'https://s3.amazonaws.com/' + \
        s3_bucket_name + '/' + environment.lower()

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
        stack_outputs.update({key: value})
        position += 1

    return stack_outputs


def get_stack_resources(cf, stack_name):
    stack_resource_list = cf.list_stack_resources(StackName=stack_name)
    stack_summaries = stack_resource_list['StackResourceSummaries']

    stack_resources = {}
    position = 0
    for element in stack_summaries:
        key = element['LogicalResourceId']
        value = element['PhysicalResourceId']
        stack_resources.update({key: value})
        position += 1

    return stack_resources


def get_stack_complete(cf, stack_name):
    # Loop until stack is done building, then return True
    stack_status = ''
    while stack_status != 'CREATE_COMPLETE':
        stack_description = cf.describe_stacks(StackName=stack_name)
        stack_status = stack_description['Stacks'][0]['StackStatus']
        if stack_status != 'CREATE_COMPLETE':
            sleep(20)
    return True


def get_stack_deployed(cf, stack_name):
    # Determine if stack is deployed, return value
    try:
        cf.describe_stacks(StackName=stack_name)
    except:
        stack_deployed = False
    else:
        stack_deployed = True

    return stack_deployed


def get_template_defaults(cf, **kwargs):
    # This function can take stack_name for an already deployed stack, or a
    # TemplateBody / TemplateURL
    stack_name = kwargs.pop('stack_name', None)
    template_url = kwargs.pop('template_url', None)
    template_body = kwargs.pop('template_body', None)

    if stack_name is not None:
        template = cf.get_template_summary(StackName=stack_name)
    elif template_url is not None:
        template = cf.get_template_summary(TemplateURL=template_url)
    elif template_body is not None:
        template = cf.get_template_summary(TemplateBodyL=template_body)
    else:
        template = None

    if template is not None:
        # Create dict of template parameter default values
        template_parameters = template['Parameters']

        template_defaults = {}
        position = 0
        for element in template_parameters:
            key = element['ParameterKey']
            try:
                value = element['DefaultValue']
            except:
                value = None
            template_defaults.update({key: value})
            position += 1
        return template_defaults
    else:
        # No template specified
        return None


def create_parameters_dict(cf, cf_templates_list, bucket_url):
    cf_template_url_list = []
    for element in cf_templates_list:
        template_url = get_cf_template_url(bucket_url, element)
        cf_template_url_list.append(template_url)

    cf_parameters_list = []
    for element in cf_template_url_list:
        template_defaults = get_template_defaults(cf, template_url=element)
        cf_parameters_list.append(template_defaults)

    position = 0
    cf_default_parameters_dict = {}
    for template in cf_templates_list:
        # Remove .template extension
        cf_template_name = template.split('.template')[0]
        cf_default_parameters_dict[cf_template_name] = cf_parameters_list[position]
        position += 1

    return cf_default_parameters_dict


def print_stack_resources(stack_name, stack_resources_dict):
    print('\n' + stack_name + ' Resources: ')
    for key in stack_resources_dict:
        print(' ' + key + ': ' + stack_resources_dict[key])


def deploy_base_network_cf_stack(cf, bucket_url, cf_parameters_list):
    cf_object = 'base_network.template'
    cf_template_url = get_cf_template_url(bucket_url, cf_object)

    if cf_parameters_list['AvailabilityZoneCount'] == '2':
        az_count = '2 AZs :: 4 Subnets'
    elif cf_parameters_list['AvailabilityZoneCount'] == '3':
        az_count = '3 AZs :: 6 Subnets'

    # TODO better method for setting cidr
    ip_base = cf_parameters_list['CIDRRange'][0:6]
    public_subnet_az1 = ip_base + '.0.0/22'
    public_subnet_az2 = ip_base + '.4.0/22'
    public_subnet_az3 = ip_base + '.8.0/22'
    private_subnet_az1 = ip_base + '.32.0/21'
    private_subnet_az2 = ip_base + '.40.0/21'
    private_subnet_az3 = ip_base + '.8.0/21'

    base_network_stack_name = cf_parameters_list['stack_prefix'] + \
        '-' + cf_parameters_list['cf_stack_name']

    if get_stack_deployed(cf, base_network_stack_name) is False:
        cf.create_stack(
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

    s3_vpc_endpoint_stack_name = cf_parameters_list['stack_prefix'] + \
        '-' + cf_parameters_list['cf_stack_name']

    vpcid = cf_parameters_list['VPCID']

    if cf_parameters_list['route_table_private_az3'] is None:
        route_table_list = cf_parameters_list['route_table_public'] + ',' + \
                           cf_parameters_list['route_table_private_az1'] + ',' + \
                           cf_parameters_list['route_table_private_az2']
    else:
        route_table_list = cf_parameters_list['route_table_public'] + ',' + \
                           cf_parameters_list['route_table_private_az1'] + ',' + \
                           cf_parameters_list['route_table_private_az2'] + ',' + \
                           cf_parameters_list['route_table_private_az3']

    if get_stack_deployed(cf, s3_vpc_endpoint_stack_name) is False:
        cf.create_stack(
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

    route53_internalzone_stack_name = cf_parameters_list['stack_prefix'] + \
        '-' + cf_parameters_list['cf_stack_name']

    vpcid = cf_parameters_list['VPCID']
    environment = cf_parameters_list['Environment']
    internal_zone_name = cf_parameters_list['InternalZoneName']

    if get_stack_deployed(cf, route53_internalzone_stack_name) is False:
        cf.create_stack(
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

    sns_topic_subscriptions_stack_name = cf_parameters_list['stack_prefix'] + \
        '-' + cf_parameters_list['cf_stack_name']

    sns_endpoint_1 = cf_parameters_list['SubscriptionEndpoint1']
    sns_endpoint_2 = cf_parameters_list['SubscriptionEndpoint2']
    sns_endpoint_3 = cf_parameters_list['SubscriptionEndpoint3']
    sns_protocol_1 = cf_parameters_list['SubscriptionProtocol1']
    sns_protocol_2 = cf_parameters_list['SubscriptionProtocol2']
    sns_protocol_3 = cf_parameters_list['SubscriptionProtocol3']
    raw_sns_topic_name = cf_parameters_list['DisplayName']
    sns_topic_name = set_sns_topic_name(raw_sns_topic_name)

    if get_stack_deployed(cf, sns_topic_subscriptions_stack_name) is False:
        cf.create_stack(
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
    try:
        key_pair = ec2.create_key_pair(
            KeyName=ec2_key_name
        )
        ec2_key = key_pair['KeyMaterial']
    except:
        ec2_key = None
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
    # TODO Template names are hard-coded in per-stack deployment - Cleanup
    # somehow?
    cf_templates_list = ['base_network.template', 's3_vpc.template',
                         'route53_internalzone.template', 'sns_topic_subscriptions.template']

    # Account Parameters
    print('\nAccount Parameters: ')
    ddi = raw_input('Rackspace Account Number: ')
    raw_account_name = raw_input('Rackspace Account Name: ')
    s3_bucket_name = set_s3_bucket_name(ddi, raw_account_name)

    # VPC Parameters
    print('\nVPC Parameters: ')
    region = raw_input('Region (us-east-1): ')
    if region == '':
        region = 'us-east-1'
    environment = raw_input('Environment (Production): ')
    if environment == '':
        environment = 'Production'
    stack_prefix = raw_input('Stack Prefix (prod): ')
    if stack_prefix == '':
        stack_prefix = 'prod'

    # Set AWS Credentials
    credentials = set_credentials(region)

    # Initialize AWS Clients
    s3 = set_s3_client(credentials)
    cf = set_cf_client(credentials)
    ec2 = set_ec2_client(credentials)

    # Create CloudFormation S3 Bucket & Upload CloudFormation templates
    create_s3_bucket(s3, s3_bucket_name, region)
    upload_s3_object(s3, s3_bucket_name, environment,
                     cf_directory, cf_templates_list)
    bucket_url = get_bucket_url(s3_bucket_name, environment)

    cf_default_parameters_dict = create_parameters_dict(cf, cf_templates_list, bucket_url)

    # Base Network Parameters
    print('\nBase Network Parameters: ')
    az_count = raw_input('Availability Zone Count (2): ')
    if az_count == '':
        az_count = '2'
    cidr = raw_input('CIDR Range (172.18.0.0/16): ')
    if cidr == '':
        cidr = '172.18.0.0/16'

    # Running through default parameters TODO cleaner, export to parameters files instead of CLI input
    # for key in cf_default_parameters_dict['base_network']:
    #     if cf_default_parameters_dict['base_network'][key] is not None:
    #         parameter_value_input = raw_input(
    #             ' ' + key + '(' + cf_default_parameters_dict['base_network'][key] + '): '
    #         )
    #         if not parameter_value_input == '':
    #             cf_default_parameters_dict['base_network'][key] = parameter_value_input
    #     else:
    #         parameter_value_input = raw_input(' ' + key + ': ' + '-')
    #         if not parameter_value_input == '':
    #             cf_default_parameters_dict['base_network'][key] = parameter_value_input

    # Route53 Internal Zone Parameters
    print('\nRoute53 Internal Zone Parameters: ')
    internal_zone_name = raw_input('Internal Zone Name (prod): ')
    if internal_zone_name == '':
        internal_zone_name = 'prod'

    # SNS Topic Subscription Parameters
    print('\nSNS Topic Subscription Parameters: ')
    # Cannot be empty
    raw_sns_topic_name = raw_input('SNS Topic Name: ')
    while raw_sns_topic_name == '':
        raw_sns_topic_name = raw_input('SNS Topic Name requires a value: ')
    sns_protocol_1 = raw_input('SNS Protocol 1 (email): ')
    if sns_protocol_1 == '':
        sns_protocol_1 = 'email'
    sns_endpoint_1 = raw_input('SNS Endpoint 1: ')
    sns_protocol_2 = raw_input('SNS Protocol 2 (email): ')
    if sns_protocol_2 == '':
        sns_protocol_2 = 'email'
    sns_endpoint_2 = raw_input('SNS Endpoint 2: ')
    sns_protocol_3 = raw_input('SNS Protocol 3 (email): ')
    if sns_protocol_3 == '':
        sns_protocol_3 = 'email'
    sns_endpoint_3 = raw_input('SNS Endpoint 3: ')

    # Define Base Network parameters, Deploy Stack
    base_network_cf_parameters_list = {'stack_prefix': stack_prefix, 'cf_stack_name': 'BaseNetwork',
                                       'AvailabilityZoneCount': az_count, 'CIDRRange': cidr, 'Environment': environment}
    base_network_stack_name = deploy_base_network_cf_stack(
        cf, bucket_url, base_network_cf_parameters_list)
    # Verify stack build completed, store dictionary of stack resources
    if get_stack_complete(cf, base_network_stack_name) is True:
        base_network_stack_resources = get_stack_resources(
            cf, base_network_stack_name)

    vpcid = base_network_stack_resources['VPCBase']
    route_table_public = base_network_stack_resources['RouteTablePublic']
    route_table_private_az1 = base_network_stack_resources['RouteTablePrivateAZ1']
    route_table_private_az2 = base_network_stack_resources['RouteTablePrivateAZ2']
    if az_count == 3:
        route_table_private_az3 = base_network_stack_resources['RouteTablePrivateAZ3']
    else:
        route_table_private_az3 = None

    # Define S3 VPC Endpoint parameters, Deploy Stack
    s3_vpc_endpoint_cf_parameters_list = {
        'stack_prefix': stack_prefix, 'cf_stack_name': 'S3-VPC-Endpoint', 'VPCID': vpcid,
        'route_table_public': route_table_public, 'route_table_private_az1': route_table_private_az1,
        'route_table_private_az2': route_table_private_az2, 'route_table_private_az3': route_table_private_az3
    }
    s3_vpc_endpoint_stack_name = deploy_s3_vpc_endpoint_cf_stack(
        cf, bucket_url, s3_vpc_endpoint_cf_parameters_list)

    # Define Route53 Internal Zone parameters, Deploy Stack
    route53_internalzone_cf_parameters_list = {
        'stack_prefix': stack_prefix, 'cf_stack_name': 'Route53-InternalZone', 'VPCID': vpcid,
        'Environment': environment, 'InternalZoneName': internal_zone_name
    }
    route53_internalzone_stack_name = deploy_route53_internalzone_cf_stack(
        cf, bucket_url, route53_internalzone_cf_parameters_list)

    # Define SNS Topic Subscription parameters, Deploy Stack
    sns_topic_subscriptions_cf_parameters_list = {
        'stack_prefix': stack_prefix, 'cf_stack_name': 'SNS-Topic-Subscriptions',
        'SubscriptionEndpoint1': sns_endpoint_1, 'SubscriptionProtocol1': sns_protocol_1,
        'SubscriptionEndpoint2': sns_endpoint_2, 'SubscriptionProtocol2': sns_protocol_2,
        'SubscriptionEndpoint3': sns_endpoint_3, 'SubscriptionProtocol3': sns_protocol_3,
        'DisplayName': raw_sns_topic_name
    }
    sns_topic_subscriptions_stack_name = deploy_sns_topic_subscriptions_cf_stack(
        cf, bucket_url, sns_topic_subscriptions_cf_parameters_list)

    # Verify stack build completed, store dictionary of stack resources -
    # these are grouped because they can all deploy at the same time, but
    # BaseNetwork needs to run first
    if get_stack_complete(cf, s3_vpc_endpoint_stack_name) is True:
        s3_vpc_endpoint_stack_resources = get_stack_resources(
            cf, s3_vpc_endpoint_stack_name)
    if get_stack_complete(cf, route53_internalzone_stack_name) is True:
        route53_internalzone_stack_resources = get_stack_resources(
            cf, route53_internalzone_stack_name)
    if get_stack_complete(cf, sns_topic_subscriptions_stack_name) is True:
        sns_topic_subscriptions_stack_resources = get_stack_resources(
            cf, sns_topic_subscriptions_stack_name)

    # Create EC2 Key Pair, output to file
    ec2_key_name = set_ec2_key_name(raw_account_name, environment, region)
    ec2_key = create_ec2_key_pair(ec2, ec2_key_name)
    if ec2_key is not None:
        ec2_key_file_name = ec2_key_name + '.pem'
        write_file(ec2_key_file_name, ec2_key)

    # Print Stack Outputs
    print('\nStack Outputs: ')
    print_stack_resources(base_network_stack_name,
                          base_network_stack_resources)
    print_stack_resources(s3_vpc_endpoint_stack_name,
                          s3_vpc_endpoint_stack_resources)
    print_stack_resources(route53_internalzone_stack_name,
                          route53_internalzone_stack_resources)
    print_stack_resources(sns_topic_subscriptions_stack_name,
                          sns_topic_subscriptions_stack_resources)

    if ec2_key is not None:
        print('\nEC2 Key Pair: ')
        print('Key File Created: ' + ec2_key_file_name)
        print('Key Name: ' + ec2_key_name)
        print('Key Value:\n' + ec2_key)
    else:
        print('\nEC2 Key "' + ec2_key_name + '" already exists.')


if __name__ == "__main__":
    main(sys.argv[1:])
