#!/usr/bin/env python3
import ssl
import requests
import sys
import json
import os
import platform
import yaml
import subprocess
import argparse
import pyVmomi
from http import cookies
from pyVmomi import vim, vmodl
from pyVim import connect
from pyVim.task import WaitForTask
from pyVim.connect import Disconnect
from pyVmomi import pbm, VmomiSupport
import logging

# Define ANSI Colors
CRED = '\033[91m'
CEND = '\033[0m'
CGRN = '\033[92m'

# Setup logging parser
logger=logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(levelname)s: %(asctime)s: %(name)s: %(message)s', "%Y-%m-%d %H:%M:%S")

file_handler = logging.FileHandler('wcp_precheck_results.log')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)

stream_handler=logging.StreamHandler()
stream_handler.setFormatter(formatter)
stream_handler.setLevel(logging.DEBUG)

logger.addHandler(file_handler)
logger.addHandler(stream_handler)


parser = argparse.ArgumentParser(description='vcenter_checks.py validates environments for succcesful Supervisor Clusters setup in vSphere 7 with Tanzu. Uses YAML configuration files to specify environment information to test. Find additional information at: gitlab.eng.vmware.com:TKGS-TSL/wcp-precheck.git')
parser.add_argument('--version', action='version',version='%(prog)s v0.02')
parser.add_argument('-n','--networking',choices=['nsxt','vsphere'], help='Networking Environment(nsxt, vsphere)', default='vsphere')
network_type=parser.parse_args().networking

currentDirectory = os.getcwd()
host_os = platform.system()
homedir = os.getenv('HOME')
logger.info("Looking in {} for test_params.yaml file".format(homedir))
logger.info("Host Operating System is {}.".format(host_os))
cfg_yaml = yaml.load(open(homedir+"/test_params.yaml"), Loader=yaml.Loader)

if (host_os != 'Darwin') and (host_os != 'Linux'):
    logger.info(f"Unfortunately {host_os} is not supported")

from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
headers = {'content-type': 'application/json'}

def checkdns(hostname, ip):
    ## Validate Name Resolution for a hostname / IP pair
    try:
        for d in cfg_yaml["DNS_SERVERS"]:
            fwd_lookup = subprocess.check_output(['dig', cfg_yaml["VC_HOST"], '+short', str(d)], universal_newlines=True).strip()
            rev_lookup = subprocess.check_output(['dig', '-x', cfg_yaml["VC_IP"], '+short', str(d)], universal_newlines=True).strip()[:-1]
            logger.info('Checking DNS Server {} for A Record for {}'.format(d, hostname))
            logger.debug("Result of Forward Lookup {}".format(fwd_lookup))
            logger.debug("Result of Reverse Lookup {}".format(rev_lookup))
            if cfg_yaml["VC_IP"] != fwd_lookup:
                logger.error(CRED + "ERROR - Missing A Record. The Hostname, " + hostname + " does not resolve to the IP " + ip + CEND)
            else:
                logger.info(CGRN +"SUCCESS-The Hostname, " + hostname + " resolves to the IP " + ip + CEND)
            
            if cfg_yaml["VC_HOST"] != rev_lookup:
                logger.error(CRED + "ERROR - Missing PTR Record. The IP, " + ip + " does not resolve to the Hostname " + hostname + CEND)
            else:
                logger.info(CGRN +"SUCCESS-The IP, " + ip + " resolves to the Hostname " + hostname + CEND)


    except subprocess.CalledProcessError as err:
        raise ValueError("ERROR - Failure in the NSLookup subprocess call")

def check_active(host):
    if os.system("ping -c 3 " + host.strip(";") + ">/dev/null 2>&1" ) == 0:
        logger.info(CGRN +"SUCCESS - Can ping {}. ".format(host) + CEND)
        return 0
    
    else:
        logger.error(CRED +"ERROR - Cant ping {}. ".format(host) + CEND)
        return 1

def vc_connect(vchost, vcuser, vcpass):
    si = None
    try:
        logger.info("Trying to connect to VCENTER SERVER . . .")
        si = connect.SmartConnectNoSSL('https', vchost, 443, vcuser, vcpass)
        logger.info(CGRN + "SUCCESS-Connected to vCenter {}".format(si.content.about.name) + CEND)
        return si, si.RetrieveContent()
    except IOError as e:
        logger.error(CRED +"ERROR - connecting to vCenter, ", vchost  + CEND)
        logger.error(CRED +"Error is: ", e + + CEND)
        logger.error("Exiting program. Please check vCenter connectivity and Name Resolution: ")
        sys.exit(e)

def get_obj(content, vimtype, objectname):
    obj = None
    container = content.viewManager.CreateContainerView(
        content.rootFolder, vimtype, True)
    for c in container.view:
        if c.name == objectname:
            logger.debug("Item:" + c.name) 
            logger.info(CGRN+"SUCCESS - Managed Object " + objectname + " found."+ CEND)
            obj = c
            break
    if not obj:
        logger.error(CRED +"ERROR - Managed Object " + objectname + " not found."+ CEND)
    return obj
      
def get_cluster(dc, objectname):
    obj = None
    clusters = dc.hostFolder.childEntity
    for cluster in clusters:  # Iterate through the clusters in the DC
        if cluster.name == objectname:
            logger.info(CGRN+"SUCCESS - Cluster Object " + objectname + " found."+ CEND)
            obj = cluster
            break
    if not obj:
        loggger.error(CRED + "ERROR - Cluster " + name + " not found.")
    return obj

# retrieve SPBM API endpoint
def GetPbmConnection(vpxdStub):
    sessionCookie = vpxdStub.cookie.split('"')[1]
    httpContext = VmomiSupport.GetHttpContext()
    cookie = cookies.SimpleCookie()
    cookie["vmware_soap_session"] = sessionCookie
    httpContext["cookies"] = cookie
    VmomiSupport.GetRequestContext()["vcSessionCookie"] = sessionCookie
    hostname = vpxdStub.host.split(":")[0]

    
    context = ssl._create_unverified_context()
    pbmStub = pyVmomi.SoapStubAdapter(
        host=hostname,
        version="pbm.version.version1",
        path="/pbm/sdk",
        poolSize=0,
        sslContext=context)
    pbmSi = pbm.ServiceInstance("ServiceInstance", pbmStub)
    pbmContent = pbmSi.RetrieveContent()
    logger.debug(pbmContent)
    return (pbmSi, pbmContent)

def get_storageprofile(sp_name, pbmContent ):
    profiles = []
    pm = pbmContent.profileManager
    # Get all Storage Profiles
    profileIds = pm.PbmQueryProfile(resourceType=pbm.profile.ResourceType(
        resourceType="STORAGE"), profileCategory="REQUIREMENT"
    )
    logger.debug(profileIds)
    if len(profileIds) > 0:
        logger.debug("Retrieved Storage Profiles.")
        profiles = pm.PbmRetrieveContent(profileIds=profileIds)
        obj = None
        for profile in profiles:
            logger.debug("SP Name: %s " % profile.name)
            if profile.name == sp_name:
                logger.info(CGRN+"SUCCESS - Found Storage Profile {}.".format(sp_name)+ CEND)
                obj = profile
                break
        if not obj:
            logger.error(CRED + "ERROR - Storage Profile {} not found".format(sp_name)+ CEND) 
        return obj        
    else:
        logger.error(CRED + "ERROR - No Storage Profiles found or defined "+ CEND)


def check_health_with_auth(verb, endpoint, port, url, username, password):
    s = requests.Session()
    s.verify = False
    if verb=="get":
        logger.debug("Performing Get")
        response=s.get('https://'+endpoint+':'+str(port)+url, auth=(username,password))
    elif verb=="post":
        logger.debug("Performing Post")
        response=s.post('https://'+endpoint+':'+str(port)+url, auth=(username,password))
        
    logger.debug(response)
    if not response.ok:
        logger.error(CRED + "ERROR - Received Status Code {} ".format(response.status_code) + CEND) 
    else:
        logger.info(CGRN + "SUCCESS - Received Status Code {} ".format(response.status_code) + CEND) 
       
def connect_vc_rest(vcip, userid, password):
    s = requests.Session()
    s.verify = False
    # Connect to VCenter and start a session
    session = s.post('https://' + vcip + '/rest/com/vmware/cis/session', auth=(userid, password))
    if not session.ok:
        logger.error(CRED + "ERROR - Could not establish session to VC, status_code ".format(session.status_code) + CEND) 
    else:
        logger.info(CGRN + "SUCCESS - Successfully established session to VC, status_code ".format(session.status_code) + CEND) 

    token = json.loads(session.text)["value"]
    token_header = {'vmware-api-session-id': token}
    return s

def check_cluster_readiness(vc_session, vchost, cluster_id):
    response = vc_session.get('https://'+vchost+'/api/vcenter/namespace-management/cluster-compatibility?')
    if response.ok:
        wcp_clusters = json.loads(response.text)
        if len(json.loads(response.text)) == 0:
            logger.error(CGRN+"ERROR - No clusters returned from WCP Check"+ CEND)
        else:
            # If we Found clusters that are not compatible with WCP
            logger.debug(type(wcp_clusters))
            reasons = None
            for c in wcp_clusters:
                logger.debug("cluster is {}".format(c['cluster']))
                if c['cluster'] == cluster_id:
                    if c["compatible"]=="true":
                        logger.info(CRED +"SUCCESS - Cluster {} IS compatible with Workload Control Plane.".format(cluster_id) + CEND)
                    else:
                        logger.error(CRED +"ERROR - Cluster {} is NOT compatible for reasons listed below.".format(cluster_id) + CEND)
                        reasons = c["incompatibility_reasons"]
                        logger.debug(reasons)
                        for reason in reasons:
                            logger.error(CRED +"+ Reason-{}".format(reason['default_message'])+ CEND)
                    break
            return reasons   

#################################   MAIN   ################################
def main():
    logger.info("Workload Control Plane Network Type is  {} ".format(network_type))
    logger.info("Begin Testing . . . ")
    # Check YAML file for missing paramters 
    logger.info("1-Checking Required YAML inputs for program: ")
    for k, v in cfg_yaml.items():
        if v == None:
            logger.error(CRED +"ERROR - Missing required value for {}".format(k) + CEND) 
        else:
            logger.debug(CGRN +"SUCCESS - Found value, {} for key, {}".format(v,k)+ CEND) 
    
    logger.info("2-Checking Network Communication for vCenter")
    # Check if VC is resolvable and responding
    logger.info("2a-Checking IP is Active for vCenter")
    vc_status = check_active(cfg_yaml["VC_IP"])
    logger.info("2b-Checking DNS Servers are reachable on network")
    for dns_svr in cfg_yaml["DNS_SERVERS"]:
        check_active(dns_svr)
    logger.info("2c-Checking Name Resolution for vCenter")
    checkdns(cfg_yaml["VC_HOST"], cfg_yaml["VC_IP"] )
 

    logger.info("3-Checking VC is reachable via API using provided credentials")
    # Connect to vCenter and return VAPI content objects
    si, vc_content = vc_connect(cfg_yaml['VC_HOST'],cfg_yaml['VC_SSO_USER'],cfg_yaml['VC_SSO_PWD'] )
    
    # If networking type is vSphere
    if network_type=='vsphere':
        try:
            
            # Check for THE DATACENTER
            logger.info("4-Checking for the  Datacenter")
            dc = get_obj(vc_content, [vim.Datacenter], cfg_yaml['VC_DATACENTER'])

            # Check for the CLUSTER
            logger.info("5-Checking for the Cluster")
            cluster = get_cluster(dc, cfg_yaml['VC_CLUSTER'])
            cluster_id = str(cluster).split(':')[1][:-1]
            logger.debug(cluster_id)
            
            # Connect to SPBM Endpoint
            logger.info("6-Checking Storage Profiles")
            logger.info("6a-Checking Connecting to SPBM")
            pbmSi, pbmContent = GetPbmConnection(si._stub)
            logger.info("6b-Getting Storage Profiles from SPBM")
            storagepolicies = cfg_yaml['VC_STORAGEPOLICIES']
            for policy in storagepolicies:
                storage_profile= get_storageprofile(policy, pbmContent )

            # Check for the Datastore 
            logger.info("7-Checking for the Datastores")
            ds = get_obj(vc_content, [vim.Datastore], cfg_yaml['VC_DATASTORE'])

            # Check for the vds 
            logger.info("8-Checking for the vds")
            vds = get_obj(vc_content, [vim.DistributedVirtualSwitch], cfg_yaml['VDS_NAME'])

            # Check for the Primary Workload Network 
            logger.info("9-Checking for the Primary Workload Network PortGroup")
            prim_wkld_pg = get_obj(vc_content, [vim.Network], cfg_yaml['VDS_PRIMARY_WKLD_PG'])

            # Check for the Workload Network 
            logger.info("10-Checking for the Workload Network PortGroup")
            wkld_pg = get_obj(vc_content, [vim.Network], cfg_yaml['VDS_WKLD_PG'])
            
            # Check for the HAProxy Management IP 
            logger.info("11-Checking HAProxy Health")
            logger.info("11a-Checking reachability of HAProxy Frontend IP")
            haproxy_status = check_active(cfg_yaml["HAPROXY_IP"])

            if haproxy_status != 1:
                # Check for the HAProxy Health
                logger.info("11b-Checking login to HAPROXY DataPlane API")
                check_health_with_auth("get",cfg_yaml["HAPROXY_IP"], str(cfg_yaml["HAPROXY_PORT"]), '/v2/services/haproxy/configuration/backends', 
                cfg_yaml["HAPROXY_USER"], cfg_yaml["HAPROXY_PW"])
            else:
                logger.info("11b-Skipping HAPROXY DataPlane API Login until IP is Active")
            
            # Create VC REST Session
            logger.info("12-Establishing REST session to VC API")
            vc_session = connect_vc_rest(cfg_yaml['VC_HOST'],cfg_yaml['VC_SSO_USER'],cfg_yaml['VC_SSO_PWD'] )

            ## DEBUG AND TEST BELOW
            datacenter_object = vc_session.get('https://' + cfg_yaml['VC_HOST'] + '/rest/vcenter/datacenter?filter.names=' + cfg_yaml['VC_DATACENTER'])
            if len(json.loads(datacenter_object.text)["value"]) == 0:
                logger.error("ERROR - No datacenter found, please enter valid datacenter name")
            else:
                datacenter_id = json.loads(datacenter_object.text)["value"][0].get("datacenter")
                logger.error("Datacenter ID is {}".format(datacenter_id))

            # Check if Cluster is Compatible with WCP
            logger.info("13-Checking if cluster {} is WCP Compatible".format(cluster.name))
            compatability = check_cluster_readiness(vc_session, cfg_yaml['VC_HOST'], cluster_id)



        except vmodl.MethodFault as e:
            logger.error(CRED +"Caught vmodl fault: %s" % e.msg+ CEND)
            pass
        except Exception as e:
            logger.error(CRED +"Caught exception: %s" % str(e)+ CEND)
            pass


    # If networking type is NSX-T
    if network_type == 'nsxt':
        try:
            
            # Check for THE DATACENTER
            print("\n4-Checking for the  Datacenter")
            dc = get_obj(vc_content, [vim.Datacenter], cfg_yaml['VC_DATACENTER'])
            #print("\tFound datacenter named {}. Moving onto next check".format(dc.name)+ CEND)

            # Check for the CLUSTER
            print("\n5-Checking for the Cluster")
            cluster = get_cluster(dc, cfg_yaml['VC_CLUSTER'])

            # Check for the Datastore 
            print("\n6-Checking for the Datastores")
            ds = get_obj(vc_content, [vim.Datastore], cfg_yaml['VC_DATASTORE'])

            # Check for the vds 
            print("\n7-Checking for the vds")
            vds = get_obj(vc_content, [vim.DistributedVirtualSwitch], cfg_yaml['VDS_NAME'])

            # Check for the Management Network 
            print("\n8-Checking for the Management Network PortGroup")
            prim_wkld_pg = get_obj(vc_content, [vim.Network], cfg_yaml['VDS_MGMT_PG'])
            
            # Check for the Uplink Network 
            print("\n8-Checking for the Uplink Network PortGroup")
            prim_wkld_pg = get_obj(vc_content, [vim.Network], cfg_yaml['VDS_UPLINK_PG'])
            
            # Check for the Edge TEP Network 
            print("\n9-Checking for the Edge TEP Network PortGroup")
            wkld_pg = get_obj(vc_content, [vim.Network], cfg_yaml['VDS_EDGE_TEP_PG'])

            # Check for the Edge TEP Network 
            
            # Check for the ? 
            
            # Check for the ?
            
            # Check for the ?
     
        except vmodl.MethodFault as e:
            print(CRED +"\tCaught vmodl fault: %s" % e.msg+ CEND)
            pass
        except Exception as e:
            print(CRED +"\tCaught exception: %s" % str(e)+ CEND)
            pass

    logger.info("************************************************")
    logger.info("** All checks were run. Validation Complete.  **")
    logger.info("************************************************")

# Start program
if __name__ == '__main__':
    main()
