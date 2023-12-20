# Autocertdns

Automatically renew wildcard certificates for google app engine.

# Requirements

* Docker or podman
* GCP service account with bucket access to read and write to bucket/letsencrypt & update appengine ssl certiticate

or you can also run this in a Cloud Run Job, just create a cloud run job and set the env variables below:

* DNS_CREDENTIALS
* PROJECT_ID - gcp project id
* DOMAIN - top level domain without *.
* BUCKET - bucket to store /etc/letsencrypt info (this puts it in /letsencrypt subdir in your bucket)
* SUPPORT_EMAIL - email for letsencrypt
* DNS_PROVIDER - provide the certbot-dns-(plugin) from https://eff-certbot.readthedocs.io/en/stable/using.html#dns-plugins
* SERVICE_ACCOUNT - optional if cloud run instance runs on the same project and you use service account with proper access

for cloud run, clone this repo and build it in your container registry then deploy a new job and create a scheduled trigger.

```bash
gcloud builds submit --tag gcr.io/project_id/autcertdns
```

You will also need to add the service account client_email to become an owner in webmaster tools at https://www.google.com/webmasters/verification/verification
to allow it to update ssl certificates.

# Example with cloudflare

Sample cloudflare dns.ini

```ini
dns_cloudflare_api_token=YOUR_CF_TOKEN_DNSEDIT_ACCESS
```

Run command below and possibly schedule it in a cron if you plan to run it in a dedicated server.

```bash
docker run -it ghcr.io/altlimit/autocertdns:latest python3 renew.py --domain="example.com" --email="support@example.com" --bucket="bucket_name" --provider="cloudflare" --service-account="$(</path/to/service-account.json)" --project="gcp_project_id" --credentials="$(</path/to/dns.ini)"
```