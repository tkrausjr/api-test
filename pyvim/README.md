## wcp-check pyVmomi and pyVim

Example POC validation Python script to check various WCP related things in vCenter including.
1. Check that parameters are filled in $HOME/test_params.yaml 
2. Check Name Resolution and IP connectivty for vCenter
3. Check existence of target Datacenter, Cluster, Datastore
4. Check existence of DVS and Port Groups
5. Check existence of Storage Policy
6. Check existence & Reachability of HAProxy

### Preparation steps before you test the environment.
On Ubuntu 18.04 with Python3 already installed.
```
git clone git@gitlab.eng.vmware.com:TKGS-TSL/wcp-precheck.git
cd wcp-precheck/pyvim
git fetch
git checkout pytest
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
VC_SSO_PWD: '*********'
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
HAPROXY_IP: '192.168.100.149'
HAPROXY_PORT: 5556
HAPROXY_IP_RANGE_START: '10.173.13.169'
HAPROXY_IP_RANGE_SIZE: 24

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
ESX_PWD: 'VMware1!'           #  ESX host password
``` 
### Validating the environment.
To run the validation script
``` bash
❯ cd github/wcp-precheck/pyvim

❯ python3 vcenter_checks.py -n vsphere
Network Type is  vsphere
Looking in /Users/kraust.com for test_params.yaml file

1-Checking YAML inputs for program are:
	 SUCCESS - Found value, tpmlab.vmware.com for key, DOMAIN
	 SUCCESS - Found value, time.vmware.com for key, NTP_SERVER
	 SUCCESS - Found value, ['10.173.13.90'] for key, DNS_SERVERS
	 SUCCESS - Found value, vcsa.tpmlab.vmware.com for key, VC_HOST
	 SUCCESS - Found value, 10.173.13.81 for key, VC_IP
	 SUCCESS - Found value, administrator@vsphere.local for key, VC_SSO_USER
	 SUCCESS - Found value, *********! for key, VC_SSO_PWD
	 SUCCESS - Found value, Datacenter for key, VC_DATACENTER
	 SUCCESS - Found value, Nested-TKG-Cluster for key, VC_CLUSTER
	 SUCCESS - Found value, ['thin', 'thinner'] for key, VC_STORAGEPOLICIES
	 SUCCESS - Found value, 66-datastore3 for key, VC_DATASTORE
	 SUCCESS - Found value, vds-1 for key, VDS_NAME
	 SUCCESS - Found value, management-vm for key, VDS_MGMT_PG
	 SUCCESS - Found value, not_there for key, VDS_PRIMARY_WKLD_PG
	 SUCCESS - Found value, ext-uplink-edge for key, VDS_WKLD_PG
	 SUCCESS - Found value, 192.168.100.149 for key, HAPROXY_IP
	 SUCCESS - Found value, 5556 for key, HAPROXY_PORT
	 SUCCESS - Found value, 10.173.13.169 for key, HAPROXY_IP_RANGE_START
	 SUCCESS - Found value, 24 for key, HAPROXY_IP_RANGE_SIZE
	 SUCCESS - Found value, ext-uplink-edge for key, VDS_UPLINK_PG
	 SUCCESS - Found value, tep-edge for key, VDS_EDGE_TEP_PG
	 SUCCESS - Found value, 102 for key, HOST_TEP_VLAN
	 ERROR - Missing required value for  WCP_MGMT_STARTINGIP
	 ERROR - Missing required value for  WCP_MGMT_MASK
	 ERROR - Missing required value for  WCP_MGMT_GATEWAY
	 SUCCESS - Found value, ['10.173.13.167', '10.173.13.168', '10.173.13.169'] for key, ESX_IPS
	 SUCCESS - Found value, root for key, ESX_USR
	 SUCCESS - Found value, VMware1! for key, ESX_PWD

2-Checking Name Resolution for vCenter
	 SUCCESS-The Hostname, vcsa.tpmlab.vmware.com resolves to the IP 10.173.13.81

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

********************************************
All checks were run. Validation Complete.  *
********************************************
``` 

