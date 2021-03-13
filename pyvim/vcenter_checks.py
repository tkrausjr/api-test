import ssl
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
# rom pyVim.connect import SmartConnect, Disconnect

# Define ANSI Colors
CRED = '\033[91m'
CEND = '\033[0m'
CGRN = '\033[92m'

parser = argparse.ArgumentParser(description='vcenter_checks.py validates environments for succcesful Supervisor Clusters setup in vSphere 7 with Tanzu. Uses YAML configuration files to specify environment information to test. Find additional information at: gitlab.eng.vmware.com:TKGS-TSL/wcp-precheck.git')
parser.add_argument('--version', action='version',version='%(prog)s v0.02')
parser.add_argument('-n','--networking',choices=['nsxt','vsphere'], help='Networking Environment(nsxt, vsphere)', default='vsphere')
# To make networking positional
#parser.add_argument('networking',choices=['nsxt','vsphere'], help='Networking Environment(nsxt, vsphere)', default='vsphere')
network_type=parser.parse_args().networking
print("Network Type is  {} ".format(network_type))

currentDirectory = os.getcwd()
host_os = platform.system()
homedir = os.getenv('HOME')
print("Looking in {} for test_params.yaml file".format(homedir))
cfg_yaml = yaml.load(open(homedir+"/test_params.yaml"), Loader=yaml.Loader)

if (host_os != 'Darwin') and (host_os != 'Linux'):
    print(f"Unfortunately {host_os} is not supported")

def checkdns(hostname, ip):
    ## Validate Name Resolution for a hostname / IP pair
    try:
        for dns in cfg_yaml["DNS_SERVERS"]:
            fwd_lookup = subprocess.check_output(['dig', cfg_yaml["VC_HOST"], '+short', str(dns)], universal_newlines=True).strip()
            rev_lookup = subprocess.check_output(['dig', '-x', cfg_yaml["VC_IP"], '+short', str(dns)], universal_newlines=True).strip()[:-1]
            
            if cfg_yaml["VC_IP"] != res['Address']:
                raise ValueError(CRED + "\t ERROR - The Hostname, " + hostname + " does not resolve to the IP " + ip + CEND)
            else:
                print(CGRN +"\t SUCCESS-The Hostname, " + hostname + " resolves to the IP " + ip + CEND)

            if cfg_yaml["VC_HOST"] != rev_lookup:
                raise ValueError(CRED + "\t ERROR - The IP, " + ip + " does not resolve to the Hostname " + hostname + CEND)
            else:
                print(CGRN +"\t SUCCESS-The IP, " + ip + " resolves to the Hostname " + hostname + CEND)

    except subprocess.CalledProcessError as err:
        raise ValueError("ERROR - The vCenter FQDN is not resolving")

def vc_connect(vchost, vcuser, vcpass):
    si = None
    try:
        print("\t Trying to connect to VCENTER SERVER . . .")
        si = connect.SmartConnectNoSSL('https', vchost, 443, vcuser, vcpass)
        print(CGRN + "\t SUCCESS-Connected to VCENTER SERVER !", si.content.about.name + CEND)
        return si, si.RetrieveContent()
    except IOError as e:
        print(CRED +"\t ERROR - connecting to vCenter, ", vchost  + CEND)
        print(CRED +"\t Error is: ", e + + CEND)
        print("\t Exiting program. Please check vCenter connectivity and Name Resolution: ")
        sys.exit(e)

def get_obj(content, vimtype, objectname):
    obj = None
    container = content.viewManager.CreateContainerView(
        content.rootFolder, vimtype, True)
    for c in container.view:
        if c.name == objectname:
            #print("Item:" + c.name) # for debugging
            print(CGRN+"\t SUCCESS - Managed Object " + objectname + " found."+ CEND)
            obj = c
            break
    if not obj:
        print(CRED +"\t ERROR - Managed Object " + objectname + " not found."+ CEND)
    return obj
      
def get_cluster(dc, objectname):
    obj = None
    clusters = dc.hostFolder.childEntity
    for cluster in clusters:  # Iterate through the clusters in the DC
        if cluster.name == objectname:
            print(CGRN+"\t SUCCESS - Cluster Object " + objectname + " found."+ CEND)
            obj = cluster
            break
    if not obj:
        print(CRED + "\tERROR - Cluster " + name + " not found.")
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
    #DEBUG# print(pbmContent)
    return (pbmSi, pbmContent)

def get_storageprofile(sp_name, pbmContent ):
    profiles = []
    pm = pbmContent.profileManager
    # Get all Storage Profiles
    profileIds = pm.PbmQueryProfile(resourceType=pbm.profile.ResourceType(
        resourceType="STORAGE"), profileCategory="REQUIREMENT"
    )
    #DEBUGprint(profileIds)
    if len(profileIds) > 0:
        print("\tRetrieved Storage Profiles.")
        profiles = pm.PbmRetrieveContent(profileIds=profileIds)
        obj = None
        for profile in profiles:
            #DEBUG# print("SP Name: %s " % profile.name)
            if profile.name == sp_name:
                print(CGRN+"\t SUCCESS - Found Storage Profile {}.".format(sp_name)+ CEND)
                obj = profile
                break
        if not obj:
            print(CRED + "\tERROR - Storage Profile {} not found".format(sp_name)+ CEND) 
        return obj        
    else:
        raise RuntimeError(CRED + "\tERROR - No Storage Profiles found or defined ".format(sp_name)+ CEND)


#################################   MAIN   ################################
def main():
    # TEMP DEBUG - Validate existence of all YAML keys
    print("\n1-Checking YAML inputs for program are: ")
    for k, v in cfg_yaml.items():
        if v == None:
            print(CRED +"\t ERROR - Missing required value for ",  k + CEND) 
        else:
            print(CGRN +"\t SUCCESS - Found value, {} for key, {}".format(v,k)+ CEND) 
    
    print("\n2-Checking Name Resolution for vCenter")
    # Check if VC is resolvable and responding
    checkdns(cfg_yaml["VC_HOST"], cfg_yaml["VC_IP"] )

    print("\n3-Checking VC is reachable via API using provided credentials")
    # Connect to vCenter and return VAPI content objects
    si, vc_content = vc_connect(cfg_yaml['VC_HOST'],cfg_yaml['VC_SSO_USER'],cfg_yaml['VC_SSO_PWD'] )
    
    # If networking type is vSphere
    if network_type=='vsphere':

        try:
            # Check for THE DATACENTER
            print("\n4-Checking for the  Datacenter")
            dc = get_obj(vc_content, [vim.Datacenter], cfg_yaml['VC_DATACENTER'])
            #print("\tFound datacenter named {}. Moving onto next check".format(dc.name)+ CEND)

            # Check for the CLUSTER
            print("\n5-Checking for the Cluster")
            cluster = get_cluster(dc, cfg_yaml['VC_CLUSTER'])
            #print("\tFound Cluster named {}. Moving onto next check".format(cluster.name)+ CEND)

            # Connect to SPBM Endpoint
            print("\n6-Checking Storage Profiles")
            print(" 6a-Checking Connecting to SPBM")
            pbmSi, pbmContent = GetPbmConnection(si._stub)
            print(" 6b-Getting Storage Profiles from SPBM")
            storagepolicies = cfg_yaml['VC_STORAGEPOLICIES']
            for policy in storagepolicies:
                storage_profile= get_storageprofile(policy, pbmContent )

            # Check for the Datastore 
            print("\n7-Checking for the Datastores")
            ds = get_obj(vc_content, [vim.Datastore], cfg_yaml['VC_DATASTORE'])
            #print("\tFound datastore named {}. Moving onto next check".format(ds.name)+ CEND)

            # Check for the vds 
            print("\n8-Checking for the vds")
            vds = get_obj(vc_content, [vim.DistributedVirtualSwitch], cfg_yaml['VDS_NAME'])
            #print("\tFound vds named {}. Moving onto next check".format(vds.name)+ CEND)

            # Check for the Primary Workload Network 
            print("\n9-Checking for the Primary Workload Network PortGroup")
            prim_wkld_pg = get_obj(vc_content, [vim.Network], cfg_yaml['VDS_PRIMARY_WKLD_PG'])
            #print(CGRN +"\tFound PG named {}. Moving onto next check".format(prim_wkld_pg.name)+ CEND)

            # Check for the Workload Network 
            print("\n10-Checking for the Workload Network PortGroup")
            wkld_pg = get_obj(vc_content, [vim.Network], cfg_yaml['VDS_WKLD_PG'])
            #print("\tFound PG named {}. Moving onto next check".format(wkld_pg.name)+ CEND)

        except vmodl.MethodFault as e:
            print(CRED +"\tCaught vmodl fault: %s" % e.msg+ CEND)
            pass
        except Exception as e:
            print(CRED +"\tCaught exception: %s" % str(e)+ CEND)
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

    print("\n********************************************\nAll checks were run. Validation Complete.  *\n********************************************")

# Start program
if __name__ == '__main__':
    main()
