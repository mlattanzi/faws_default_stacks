# FAWS Default Stack Deployment
The purpose of this script is to automate the provisioning of frequently deployed resources for new FAWS environments.

## Script Functions
- Create CloudFormation S3 Bucket
  - Enable Versioning
  - Apply Lifecycle (Delete Previous Versions after 365 Days)


- Upload default CloudFormation templates to S3 Bucket

- Deploy default CloudFormation stacks

- Create EC2 private key pair

## Future Function
- Add CloudFormation Parameters File functionality
  - Dynamically generate Parameters File by inspecting default CloudFormation templates JSON


- Store EC2 private key pair in PasswordSafe

- Create customer GitHub repository with formatting
  - Push CloudFormation templates to repository


- Integrate wth FAWS Tracker for one-click deployments


## Script Usage
```
$ python deploy_defaults.py
NOTE: Please run "faws env" and set your environment variables before running this script.
Please enter parameters. Leave blank to use (default) values.

Script Parameters:
CloudFormation Template Directory Path: /Users/matt6757/scripts/cftemplates

Account Parameters:
Rackspace Account Number: 981868
Rackspace Account Name: Matt Lattanzi FAWS Test

VPC Parameters:
Region (us-east-1): us-west-1
Environment (Production):
Stack Prefix (prod):

Base Network Parameters:
Availability Zone Count (2):
CIDR Range (172.18.0.0/16): 172.19.0.0/16

Route53 Internal Zone Parameters:
Internal Zone Name (prod):

SNS Topic Subscription Parameters:
SNS Topic Name: Matt Lattanzi Test Topic
SNS Protocol 1 (email):
SNS Endpoint 1: matt.lattanzi.test@rackspace.com
SNS Protocol 2 (email):
SNS Endpoint 2:
SNS Protocol 3 (email):
SNS Endpoint 3:

Stack Outputs:
Internal Hosted Zone ID: Z3JGU2KXEVBPHT
SNS Topic ARN: arn:aws:sns:us-west-1:057866020917:matt-lattanzi-test-topic

EC2 Key Pair:
Key Name: production-matt-lattanzi-faws-test
Key Value:
-----BEGIN RSA PRIVATE KEY-----
MIIEowIBAAKCAQEAugARG0yX4fBhlTglTYA66zepoDpg0uHIne69BMNeNuzDnk7woth4iGvf5rSN
Whhs8sxgq/IplL6dwJ6GeW1152om5VLaJAcH2fW1GzuM9bsTk9yLR05JW6G0JbqFAKA3XWXlSqkg
1YgPO9frVMcse5lEr+GRQ+1inqRLnjSZ5Tmu2LPmFs013hZ3GcKZvpdedP+y/Yuk6ZEJpCDcZvoj
yt6q1pZvZsOIcfWc+ZdG3h0xkKQfuI9jojC9f0MIc473kVWmyl6KT2mVdE7QHTDpv8yQJ0b/NHrq
xx6rKr/xUITAVTy9gNoaIcLI7I3oXxnvmbYyVPFIxx6UhAOQEPV7nQIDAQABAoIBAACSw3q8D7PI
k+Rr2eGVRZk4ALPXujisLXwfIkIDgCTXMfso7yDxXd29x2DkqZLfhGZzLtEY2/vzYnUXh/6T0cs2
zoviZ32479NCKJ6+3j5bp0HLajp8CUnZA78iBgrsc388Myq5vropwzJCBh2qx35SCJ4qKdJ1xtoK
U5lXPCoys/cO3LJX22UR01hGPu7D0ACSlXfRKNUuo0qXTmXUwsjUvPQvD+sdUKUF4XkWpMhQ0DdI
BT5U0teJ67lrZ1pkHoJdkGf+AqaQ7d7kclIIakKPPM+NdZwwNNyBLzkHn7TmYx+l+zGKSHJWH2GW
oEDr8Zz9OufpUjc0EQdkI+ZCNlkCgYEA8fX5lryuz1fD1ZvbscnyvRwxI78jI+5MNuH59m5lxK/D
niE/pHQjGlFLY5u2qIX6NB+xrJJ0PHBkMSVekws7geMi2yGD5nmfV/7xu2U7JhuIkrTpratsz8XK
9uOW6DwYQ7IXCp57wcFGtkTzkxb5DC6GNcJ45g6WFUObckOICl8CgYEAxMreGyGnmpP77Web3xId
UkjbLms8l1xBsEAgk2u0irZTFa22+uHbCFAoVAUERGpkN55FbaI4FP4jqRF+F+KofzRxLxLIFSn3
T21biz1dUFjc3geREp2Qk8Rv7k2w+TVBXi0nKp6YqLNoJ0xYoeUG3SrAmEYklL/Hka5zJ2+A84MC
gYA4KJosdVCxiTJH4uvj4PZ5FBEHtfZHAako19w3aTovo4forNjjp5z6H8I6tUp45NfEv1Jytm9K
E9/9VCoWQPYn2HsflzDRDouAVgjvMLjAyIUzX9AY4f/YXZUVJo/BCSmslKoqacxZlS1/YpOSITPe
svGtipya8Om+t7ldlPT/SwKBgEaS9mpGfIP8FDoEkSrDpU5QIIKaJKWniUs7BDO6SYoBbvR0Uw3Q
F6v4iy3uiqQ6f2xOz1lM9s3YglNsmYrZV1IfLYQTOTwVy8JpVo4t2Jwq8jKSBh3l8eZ8aSPOKuyE
g8fRa51mORsvE+gcAiE1MGv6nA1AAnhx+pEtPdDjtRwfAoGBAIJPaTzjPrluYT5Vb9GHNpiGj8c+
8VuBZLS30teDmaEI++ov1F7lJsx0TuT00UgF5DupTysRVwCVZvRhQ1MQBFzDHYdaAwebDWZIVEJ9
7SUCQHNtXE8tMu0Nscb1mV3JmmYaRjrkYk7NmiKXISn2GzQdlj9/6/OEYoVP24SZFi4G
-----END RSA PRIVATE KEY-----
```
