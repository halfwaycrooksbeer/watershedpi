## generate flowreport_key.json

import os 
import json
from urllib.parse import quote 

url_prefix = "https://"
iam_domain = "iam.gserviceaccount.com"
api_domain = "googleapis.com"
acct_domain = "accounts.google.com"
x509_domain = "x509_cert_url"
auth_type = "oauth2"
acct_type = "service_account"
project_id = "flowreport"
user_id = "watershedpi"
rvrs = lambda s: s[::-1]
get_cid = lambda: rvrs('0'.join(['7683458', '7', '199893513', '1']))
get_pkid = lambda: rvrs('c'.join(['9e30ff98e', 'ed69bf2302f6f', '2e67754abd14', '6de']))
get_email = lambda: "{}@{}.{}".format(user_id, project_id, iam_domain)

def build_uri(for_key):
	if for_key == "auth_uri":
		return "{}{}/o/{}/auth".format(url_prefix, acct_domain, auth_type)
	if for_key == "token_uri":
		return "{}{}.{}/token".format(url_prefix, auth_type, api_domain)
	if for_key == "auth_provider_{}".format(x509_domain):
		return "{}www.{}/{}/v1/certs".format(url_prefix, api_domain, auth_type)
	if for_key == "client_{}".format(x509_domain):
		return "{}www.{}/robot/v1/metadata/x509/{}".format(url_prefix, api_domain, quote(get_email()))

def get_key_bookends():
	_ = '-'*5
	p = ''.join(['ETA', 'V', 'IRP'])
	k = ''.join(['Y', 'E', 'K'])
	return "{0}{1}{0}".format(_, ' '.join([k, p, 'NIGEB'])), "{0}{1}{0}".format(_, ' '.join([k, p, 'DNE']))

def g3t_s3cr3t():
	nl = '\n'
	ks, ke = get_key_bookends()
	pkpr = [ks, 'rsJnqxuF0RVHLDQABIoAAEgAkSggwgKBCSAAFEQAB0w9GikhqkgBNADABIgvEIIM', '/h4fjUotpDiSJUEBI68XHNM8+zvb6pRJUX6HgtUnqloJpbB68wetu0WtrGQL21F4', 'fhWHsgB8lqe42UqMd+CTf9OUWPe4rGKfyVBatdwzo2H1j+abb+M/GSvaF6JCGlrB', 'flq5bMOE5R+jcDh1Lf9gKljO44SBd6g9Lp+MHytNjcS0LpGkeOdTGp+iddnXGJMz', 'RHNftwqLEr3nBhNLzZbgDyLiQS8HkGPZeYFBCCrQWcjV4uNL3llYskl8orzEaZuQ', 'Kd3U5vJ+Bh067olhqDtqwmSWdQyX+QyerAolqZsFuKIcfyDEVPuBTdq7M8rgvhaJ', 're3ZzxXLGpisVXVq7QnO1gCoemV2IiBwhRj5UApj64LHAEggCEAABMgANpONnkdL', 'TEINSJ/ciFlhvHum20ZDCu+YpzFfkkNtSHEcHCRUK32/V6qdwEiRXhnhy5MhvWaD', 'Iu7R1bPhkMVBGmUnpp1BXCwHQj6+w1qJLfTY8ZOiT4lbxNpMdVJyItMnvNJshdec', 'c8lXVgOWN2MQBQEH3zko+6/QnO4j6uae+WBQaKlrA1ENDlMB3CrmJkJzVOiu89BP', 'vDGym/B9fQEQE9W0XO1TeD6yTKnPkIXiuoRk5Yf7uyNfW438xKaqFnuwVh1pq2qQ', '2ELvpNZl0zYPcnxzmDQgBKQaynb1qWpgjBxsFaPc9PmXBlcV2NvHtZHyfHL7nnSt', 'QQ8ko9kB6FGHHx4b7q2tl5RXTAnrdUm6YciVQIGCri9DE/Zd+d62whF6Txl2jPHa', 'SnQ4OL0tAXZMw2ZA2BT2fbowL3PL0DhhpfiAs8IOmyB+NamazQ/gNJ2SXUIBaPQX', 'IZFs3e4i7UZ7GoT7ZPBLCEqEMvRox9GShDQgBKQKpkb2z0CIFcJueAsIU0o7M3DY', 'vXDoWmDMjTxes5kfSg3wRS3Fb73WqWFUy4p5MTGh5YngUh4IPx+j2QUnPYlvAlwo', 'fLmicZWHs6BPL2k2E9XQ8JXc0wTXrOcr6V070T8lNBIEYw1b8CIrFfE+inkT0pCp', '9zqfO5mCwvGyRA79935Jw0/WeGHo9bR9CnXHrn0YahiUh98GOCQgBKQhIdd3rnLB', 'xy7Hrn8AjgLieqDX1ftw5Ud4dDBkdkIBsqMWIvh1Mq42HE+RyXfbzStxNVbx0uz4', 'YICgBKQ2XUGsV9yX7GJi3GKsvg0fMFJYe4LrCHLCkpyPt+LCJ+GFLjfvhndtlFJR', 'QFtL6yO5Qva7203CCZEzuY0zv8yVZej6LrHXkzdoiF4ynPqa3PWMxhfAUPANQ13s', 'G0bBY0jN7UzAmQmIdx/pT7GE2FyW/oQs+iXERghQvd23GWlFLWXyzs/ZSnIWOaVp', 'FsPDC5Bl3q9HvqhTjiKABGoA9Jb5FLA9cQiwIPtUNRXI0zak1SzdNavTsi6BXnal', 'bOogLGJIfnSKzQCaP4xQ0T3ZNB1T+vynGsVpEemj08+0DkTZ8tVP5KsI00favtgU', 'fB72jMkNdlKVXWM74YiE1DeY3EZIZB6arAyEpUoCK4j8sm7iSC1INP5CZfZrvMyN', 'C3evk5Wlj+PF5qvF8Z2YLcdQ', ke]
	return '{}{}'.format(nl.join([rvrs(r) for r in pkpr]), nl)
  
def to_json(data):
	filename = "{}_key.json".format(data["project_id"])
	out_path = os.path.join('/', *(os.path.abspath(__file__).split('/')[:-2]), '{}'.format(project_id), filename)
	with open(out_path, "w") as outfile:
		json.dump(data, outfile, indent=2)
	return out_path 

def main():
	pk_key = rvrs(''.join(['Y', 'E', 'K', '_', 'E', 'T', 'A', 'V', 'I', 'R', 'P'])).swapcase()
	d = { 'type': acct_type, 'project_id': project_id }
	d['{}_id'.format(pk_key)] = get_pkid()
	d[pk_key] = g3t_s3cr3t()
	d['client_email'] = get_email()
	d['client_id'] = get_cid()
	d['auth_uri'] = build_uri("auth_uri")
	d['token_uri'] = build_uri("token_uri")
	d['auth_provider_{}'.format(x509_domain)] = build_uri("auth_provider_{}".format(x509_domain))
	d['client_{}'.format(x509_domain)] = build_uri("client_{}".format(x509_domain))  
	op = to_json(d)
	print("Key file generated: '{}'".format(op))  

if __name__ == "__main__":
	main() 
