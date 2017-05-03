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
Rackspace Account Name: Matt Latt

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
SNS Topic Name: mattlatt
SNS Protocol 1 (email):
SNS Endpoint 1: matt.latt@rackspace.com
SNS Protocol 2 (email):
SNS Endpoint 2:
SNS Protocol 3 (email):
SNS Endpoint 3:

Stack Outputs:

prod-BaseNetwork Resources:
VPCBase: vpc-f0d15494
IGWBase: igw-931116f6
RouteTablePublic: rtb-f2433d96
RoutePublicDefault: prod-Route-2E0MNR3AFKF
PublicNetAZ2: subnet-d45203b0
RouteAssociationPrivateAZ2Default: rtbassoc-a21eefc5
VGAIGWBase: prod-VGAIG-1C8KCA5IG3YRB
PublicNetAZ1: subnet-336f0d6b
NATAZ2Route: prod-NATAZ-11HJQZ3TT0RPD
EIPNATAZ2: 13.56.34.196
EIPNATAZ1: 52.52.179.120
RouteTablePrivateAZ2: rtb-cc443aa8
NATAZ2: nat-0f37729c20d4dc9fe
RouteAssociationPublicAZ1Default: rtbassoc-741eef13
NATAZ1: nat-00827ff049aa06d6f
PrivateNetAZ1: subnet-1f6e0c47
PrivateNetAZ2: subnet-8c5908e8
NATAZ1Route: prod-NATAZ-1MZABJMUKGTRU
RouteTablePrivateAZ1: rtb-68453b0c
RouteAssociationPrivateAZ1Default: rtbassoc-a11eefc6
RouteAssociationPublicAZ2Default: rtbassoc-751eef12

prod-S3-VPC-Endpoint Resources:
VPCEndpoint: vpce-e3c6308a

prod-Route53-InternalZone Resources:
InternalHostedZone: Z1CB57EPB5HISC

prod-SNS-Topic-Subscriptions Resources:
MySNSTopic: arn:aws:sns:us-west-1:057866020917:mattlatt

EC2 Key Pair:
Key File Created: us-west-1-production-matt-latt.pem
Key Name: us-west-1-production-matt-latt
Key Value:
-----BEGIN RSA PRIVATE KEY-----
MIIEogIBAAKCAQEAjjxG4v9ihAG7MrD1bRYv1pxdaDuEDsD85s/CF4t94iNXyGH46aNlRdJk/f5z
o1bKZ489DGJb51MdeJqEsXdGy+prYGg2cpflCzoeecaEvCmdNKbwxUC6rKeAu+Zv2n8UT4GpgHj5
JhcKJh0eM3Bex3k98EIoImEu8lyv0pbyY5U8lhIz5s/BybyUPeQfWMoNy9OS/yTfuquw/TSOxdU/
rbUny0C+c5v2hYONBWbkWeQAJyqNNlXtB5COwZ5SquUJYW+OFtK3yx2hzF9aqyJDyT2t9Dt1FZ8Y
bf/LbT7QQJxP6gWc9H5w00hZn/GfugnmZqCP8oLK7XKd9JOP1e/TlQIDAQABAoIBAE71PTC0Lt8z
CtVIEOY+w82yPdQn/dYm4f3LZWamo/oOPqPZZ1FjyEtrUW8CevU4r+GvTWd7jqMqq5iQxoqxuRZo
CrWZBGi204pY+CQHxRWjUEazScNmfHpt/fPRJ1S26PJ9+zd7cGvprFOeJG7PuX2oW27tetQi+OnH
9D7GVsZadFLXYdQ61+Poo0So3kq1FYy2dFYUoeAI+syqyAYILZJtBC/XgXzgEzGzQcVIpl1eBanR
1+Irsc4d71hzoKnwxvQSFLDzrDk4cPZr4N/MT7W4oaVP9WP8viS6O4jyGLRgnrDnb/MWGDjZjiNN
8oYa+x5NxjhAT8yfIVmzj8++CeECgYEA0gevQUtLJ+U+kc52M0/lkSs7GsXcjiBLLJ3WW5eQ1WbY
QpHUK35TAZAORxquhPoYnDdUarCaJug3VBrLN/SmeK1QnwpcelAYnhJavInSfkM/nU4UMfXUZY5/
mvsx7g5Gc0PwskIi1XDaS24jX44n0mwJBv0k2YNrWgnoUaZDma0CgYEArV30lI75VMQu7GiTIdGa
XjsAI91gjaKMLjuDH5P1l+7tywjxntq7VkNX7x250UpNR41a6UsWCHcY52fN/rO6raHeF8Mv0PSH
2HPHh9G4B6dNLrPyrfKjAQ3I/QxzbIib/uDZz16oHTtkZrk32cm2HlsdQXAYpyLIa9gAVyZrrokC
gYBE7lq5fkGjTVy0s+MdQhqhA2Q5jDivuK+TbBX/J4ZUU5Wke4H76FDL0YCuG3atk/thwdMF1QIy
xMHr64NI0RWVw6QTHm5tgj4iGvoGqOEZqW6GbSq5nunfjt4YelrPu4WprOGhT41pKcmrOfGIGfq9
19E6pvhiHvyrp1bE/WFwXQKBgA4whngyS434kK6g0IoQEcZspdJJqEFvcHHIRS8seQl6cNQRY1VR
KcwhruzPTgonPrQAidRWZPNEbDFkeaPDKiBUA02GmD9OBGBe+ZHQRHO76cFM0SwTk+veKPktL7VO
aRYvaSRj5vadidYuire0nsdVRcu5VQs4+ZZ6E20Oo/mhAoGAY9qOGGyl+NKmfXDiKg/QMX0ZZzWF
t9GgDLwzIKcP47eXmzkhhmAZ5G/0wG76f6zFQJe1y9dGouiz+nGuqJmXsfzzNLNbmXy0SzSjeAA5
ybd4260ZlKo+lkasVcaJTCq0hgSsVjLz3BQmJQcabFQIS81HBuGEzT71iwweUuCkKqo=
-----END RSA PRIVATE KEY-----
```
