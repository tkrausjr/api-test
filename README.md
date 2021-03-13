# WCP-precheck

## pyVmomi script
Python script to validate that various dependencies are in place for a successful WCP installation, including:

1. Check that parameters are filled in $HOME/test_params.yaml 
2. Check Name Resolution and IP connectivty for vCenter
3. Check existence of target Datacenter, Cluster, Datastore
4. Check existence of DVS and Port Groups
5. Check existence of Storage Policy
6. Check existence & API of HAProxy
7. Check Cluster compatability with Workload Management (WCP)

### Preparation steps before you test the environment.
On Ubuntu 18.04 with Python3 already installed.
```
git clone git@gitlab.eng.vmware.com:TKGS-TSL/wcp-precheck.git
cd wcp-precheck/pyvim
chmod +x ./vcenter_checks.py 
cp ./test_params.yaml ~/test_params.yaml
vi ~/test_params.yaml    ### See Below of explanation
pip install pyvmomi
```

### Parameters file used for input values to Validate
Fill in the parameters file named test_params.yaml. Place this parameters file  in $HOME on a Linux or OSX system where the scripts will be run from.
``` yaml
### COMMON SETTINGS
DOMAIN: 'tpmlab.vmware.com'
NTP_SERVER: 'time.vmware.com'
DNS_SERVERS:
  - '10.173.13.90'

### Section for VC
VC_HOST: 'vcsa.tpmlab.vmware.com'    # VCSA FQDN or IP MUST ADD A Rec to DNS
VC_IP: '10.173.13.81'                      # VCSA IP
VC_SSO_USER: 'administrator@vsphere.local'
VC_SSO_PWD: *******
VC_DATACENTER: 'Datacenter'
VC_CLUSTER:  'Nested-TKG-Cluster'
VC_STORAGEPOLICIES:          # Storage Policies to use 
  - 'thin'  
  - 'thinner'      
VC_DATASTORE: '66-datastore3'    # FUTURE - If needed 

### Section for vSphere Networking Deployments
VDS_NAME: 'vds-1'
VDS_MGMT_PG: 'management-vm'
VDS_PRIMARY_WKLD_PG: 'not_there'
VDS_WKLD_PG: 'ext-uplink-edge'
HAPROXY_IP: '192.168.100.163'
HAPROXY_PORT: 5556      # HAProxy Dataplane API Mgmt Port chosen during OVA Deployment
HAPROXY_IP_RANGE_START: '10.173.13.38' # HAProxy LB IP Range chosen during OVA Deployment
HAPROXY_IP_RANGE_SIZE: 29

### Section for NSX-T Networking Deployments
VDS_NAME: 'vds-1'
VDS_MGMT_PG: 'management-vm'
VDS_UPLINK_PG: 'ext-uplink-edge'
VDS_EDGE_TEP_PG: 'tep-edge'
HOST_TEP_VLAN: 102

### Section for WCP Supervisor Cluster Deployment
WCP_MGMT_STARTINGIP:
WCP_MGMT_MASK:
WCP_MGMT_GATEWAY: 

### Section for ESX Hosts - TBD future
ESX_IPS:
  - '10.173.13.167'
  - '10.173.13.168'
  - '10.173.13.169'
ESX_USR: 'root'               #  ESX host username
ESX_PWD: '********'           #  ESX host password
``` 
### Validating the environment.
To run the validation script
``` bash

❯ cd github/wcp-precheck/pyvim

❯ vcenter_checks.py -n vsphere

Network Type is  vsphere 
Looking in /Users/kraust.com for test_params.yaml file

1-Checking Required YAML inputs for program: 
         ERROR - Missing required value for  WCP_MGMT_STARTINGIP
         ERROR - Missing required value for  WCP_MGMT_MASK
         ERROR - Missing required value for  WCP_MGMT_GATEWAY

2-Checking Name Resolution for vCenter
         SUCCESS-The Hostname, vcsa.tpmlab.vmware.com resolves to the IP 10.173.13.81
  2a-Checking IP is Active for vCenter
         SUCCESS - Can ping 10.173.13.81. 

3-Checking VC is reachable via API using provided credentials
         Trying to connect to VCENTER SERVER . . .
         SUCCESS-Connected to VCENTER SERVER ! VMware vCenter Server

4-Checking for the  Datacenter
         SUCCESS - Managed Object Datacenter found.

5-Checking for the Cluster
         SUCCESS - Cluster Object Nested-TKG-Cluster found.

6-Checking Storage Profiles
  6a-Checking Connecting to SPBM
  6b-Getting Storage Profiles from SPBM
         Retrieved Storage Profiles.
         SUCCESS - Found Storage Profile thin.
         Retrieved Storage Profiles.
         ERROR - Storage Profile thinner not found

7-Checking for the Datastores
         SUCCESS - Managed Object 66-datastore3 found.

8-Checking for the vds
         SUCCESS - Managed Object vds-1 found.

9-Checking for the Primary Workload Network PortGroup
         ERROR - Managed Object not_there not found.

10-Checking for the Workload Network PortGroup
         ERROR - Managed Object ext-uplink-edge not found.

11-Checking for HAProxy VM
  11a-Checking reachability of HAProxy Frontend IP
         ERROR - Cant ping 192.168.100.163. 
  11b-Skipping HAPROXY DataPlane API Login until IP is Active


12-Establishing REST session to VC API
        SUCCESS - Successfully established session to VC, status_code 

13-Checking if cluster Nested-TKG-Cluster is WCP Compatible
PLaceholder
         ERROR - Cluster domain-c30 is NOT compatible
         Reason-Cluster domain-c30 is a personality-manager managed cluster. It currently does not support vSphere namespaces.
         Reason-Cluster domain-c30 does not have HA enabled.
         Reason-Cluster domain-c30 is missing compatible NSX-T VDS.

********************************************
All checks were run. Validation Complete.  *
********************************************

