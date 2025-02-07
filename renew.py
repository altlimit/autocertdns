import argparse
import sys
import subprocess
import json
import os
from datetime import datetime

parser = argparse.ArgumentParser(
                    prog='Renew Cert',
                    description='Automatically renews appengine wildcard certificate')
parser.add_argument('--domain', type=str, help='Your custom domain')
parser.add_argument('--email', type=str, help='Support email')
parser.add_argument('--bucket', type=str, help='Where to store letsencrypt info')
parser.add_argument('--provider', type=str, help='DNS provider')
parser.add_argument('--service-account', type=str, help='GCP service account')
parser.add_argument('--project', type=str, help='GCP Project')
parser.add_argument('--credentials', type=str, help='DNS credentials')
parser.add_argument('--days', type=int, help='Number of days before renewal (default: 15)', default=15)
parser.add_argument('--test-only', action='store_true', help='Just output commands')

args = parser.parse_args()


def run(cmd, capture=False):
    print('Running', cmd)
    if args.test_only:
        return ''
    if capture:
        return subprocess.getoutput(cmd)

    p = subprocess.run(cmd.split(' '), stderr=sys.stderr, stdout=sys.stdout)
    if p.returncode != 0:
        raise Exception(f'Failed with exit code: {p.returncode}')

env_map = {
    'DNS_CREDENTIALS': 'credentials',
    'PROJECT_ID': 'project',
    'DOMAIN': 'domain',
    'BUCKET': 'bucket',
    'SUPPORT_EMAIL': 'email',
    'DNS_PROVIDER': 'provider',
    'SERVICE_ACCOUNT': 'service_account',
    'DAYS': 'days'
}

for k, v in env_map.items():
    if not getattr(args, v, None) and os.getenv(k):
        setattr(args, v, os.getenv(k))

if args.service_account:
    with open('sa.json', 'w') as f:
        f.write(args.service_account)
    data = json.loads(args.service_account)
    run(f'gcloud auth activate-service-account {data["client_email"]} --key-file=./sa.json --project={args.project}')

try:
    run(f'gsutil cp gs://{args.bucket}/{args.domain}.tar.gz .')
except Exception as e:
    print(f'copy error {e}')
if os.path.exists(f'{args.domain}.tar.gz'):
    run(f'tar -zxf {args.domain}.tar.gz -C /')

cert_path = f'/etc/letsencrypt/live/{args.domain}/cert.pem'
if os.path.exists(cert_path):
    days = 86400 * args.days
    if 'Certificate will not expire' in run(f'openssl x509 -checkend {days} -noout -in {cert_path}', True):
        print(f'certificate will not expire after {args.days} days')
        exit(0)

run(f'/opt/certbot/bin/pip install certbot-dns-{args.provider}')
with open('dns.ini', 'w') as f:
    f.write(args.credentials)
run(f'certbot certonly --key-type rsa -n -m {args.email} --agree-tos --preferred-challenges dns --dns-{args.provider} --dns-{args.provider}-credentials ./dns.ini -d *.{args.domain} --cert-name {args.domain}')
run(f'openssl rsa -in /etc/letsencrypt/live/{args.domain}/privkey.pem -out /etc/letsencrypt/live/{args.domain}/privkey-rsa.pem')
run(f'tar -zcf {args.domain}.tar.gz /etc/letsencrypt')
run(f'gsutil cp {args.domain}.tar.gz gs://{args.bucket}/')
cert_id = run(f'gcloud app ssl-certificates list --format "get(id,domain_names)" | grep -F "*.{args.domain}" | head -n 1 | cut -f 1 || true', True)
run(f'gcloud app ssl-certificates update {cert_id} --certificate /etc/letsencrypt/live/{args.domain}/fullchain.pem --private-key /etc/letsencrypt/live/{args.domain}/privkey-rsa.pem')
print(f'Certificate update complete: {args.domain}')
