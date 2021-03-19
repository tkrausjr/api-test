# WCP-precheck
WCP-Precheck projects aims to make POC's less painful for customers and overall more successful by providing a simple validation and both realtime (Stdout) and report style output that can be run by VMware Tanzu SE's or Customers to quickly validate a vSphere environment is ready for a successful vSphere with Tanzu Supervisor Cluster creation.  The project has options for testing both NSX-T based and vSphere based networking for vSphere with Tanzu.

## Test Coverage
### General
- [x] The Tag-based storage policy specified exists the vCenter.
- [x] DNS forward and reverse resolution should work for vCenter and NSX Manager.
- [x] Ping/curl various network end points that they are reachable (DNS, NTP, VCenter, NSX Manager, )
- [x] Validate vSphere API is accessible and provided credentials are valid.
- [x] Validate existence of vSphere cluster specified in configuration YAML is valid.
- [x] Validate existence of VDS specified in configuration YAML is valid.
- [x] Validate existence of Datacenter specified in configuration YAML is valid.
- [x] Validate existence of Cluster specified in configuration YAML is valid.
- [x] Validate that vLCM (Personality Manager) is not enabled on the specified cluster if vSphere <= 7.0 U1.
- [x] Validate that HA is enabled on the specified cluster.
- [x] Validate that DRS is enabled and set to Fully Automated Mode on the specified cluster.
- [x] Validate that a compatible NSX-T VDS exists.
- [ ] Validate that at leaset one content library is created on the vCenter.
​
---
### NSX based networking
- [x] Validate required VDS Port Groups(Management, Edge TEP, Uplink) specified in configuration YAML is valid.
- [x] DNS forward and reverse resolution should work for NSX Manager.
- [x] Validate we can communicate with NSX Manager on network and NSX Management Node and Cluster is Healthy.
- [x] Validate NSX-T API is accessible and provided credentials are valid.
- [x] Validate Health of ESXi Transport Nodes(NSX-T Agent Install and Status) in vSphere Cluster.
- [x] Validate Health of Edge Transport Nodes(Status) in vSphere Cluster.
- [ ] Ingress and Egress network is routed
- [ ] Heartbeat ping to the uplink IP (T0 interface) is working. 
- [ ] 1600 byte ping with no fragmentation between ESXi TEPs
- [ ] 1600 byte ping with no fragmentation between ESXi TEPs to Edge TEPs.   
- [ ] Validate EDGE VMs are deployed as at least large.
- [ ] NTP driff between EDGE, vCenter and ESXi
- [ ] Depending on NSX version, EDGE vTEP and ESX vTEP are on different VLANs
- [ ] Validate existence of a T0 router.
- [ ] T0 router can access DNS and NTP
---
### VDS based HAProxy config
- [x] HA proxy liveness probes that check each network connectivity and the frontend VIP IP's
- [ ] The HA Proxy Load-Balancer IP Range and WCP Workload Network Range must not include the Gateway address for the overall Workload Network.
- [ ] The HA Proxy Workload IP should be in the overall Workload network, but outside of the Load-Balancer IP Range and the WCP Workload Network Range.
- [ ] The IP ranges for the OVA and the WCP enablement should be checked to be the same
- [ ] The WCP Range for Virtual Servers must be exactly the range defined by the Load-Balancer IP Range in HA Proxy.  
- [x] Validate successful login access to HAProxy VM's API endpoint.






### Preparation steps before you test the environment.
On Ubuntu 18.04 with Python3 already installed.
```
git clone https://gitlab.eng.vmware.com/TKGS-TSL/wcp-precheck.git              
Cloning into 'wcp-precheck'...
Username for 'https://gitlab.eng.vmware.com':   <VMware User ID IE njones>
Password for 'https://kraust@gitlab.eng.vmware.com':  <VMware Password>
cd wcp-precheck/pyvim
chmod +x ./wcp_tests.py 
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
VC_SSO_PWD:  '***********'
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
HAPROXY_USER: 'admin'
HAPROXY_PW: '***********'

### Section for NSX-T Networking Deployments
VDS_NAME: 'vds-1'
VDS_MGMT_PG: 'management-vm'
VDS_UPLINK_PG: 'ext-uplink-edge'
VDS_EDGE_TEP_PG: 'tep-edge'
HOST_TEP_VLAN: 102
NSX_MGR_HOST: 'nsxmgr.tpmlab.vmware.com'   # FQDN of NSX-T Manager Appliance
NSX_MGR_IP: '10.173.13.82'    # IP Addr of NSX-T Manager Appliance
NSX_USER: 'admin'   # API Username for NSX-T Manager Appliance
NSX_PASSWORD: '***********'    # API Password for NSX-T Manager Appliance

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
ESX_PWD: '***********'           #  ESX host password
``` 
### Validating the environment.
To run the validation script
``` bash

❯ cd github/wcp-precheck/pyvim
./wcp_tests.py -h                              
usage: wcp_tests.py [-h] [--version] [-n {nsxt,vsphere}] [-v [{INFO,DEBUG}]]

vcenter_checks.py validates environments for succcesful Supervisor Clusters
setup in vSphere 7 with Tanzu. Uses YAML configuration files to specify
environment information to test. Find additional information at:
gitlab.eng.vmware.com:TKGS-TSL/wcp-precheck.git

optional arguments:
  -h, --help            show this help message and exit
  --version             show program's version number and exit
  -n {nsxt,vsphere}, --networking {nsxt,vsphere}
                        Networking Environment(nsxt, vsphere)
  -v [{INFO,DEBUG}], --verbosity [{INFO,DEBUG}]

❯ wcp_tests.py -n nsxt 
OR
❯ wcp_tests.py -n vsphere
❯ /usr/local/bin/python3 /Users/kraust.com/github/wcp-precheck/pyvim/vcenter_checks.py
INFO: 2021-03-15 13:37:46: __main__: Looking in /Users/kraust.com for test_params.yaml file
INFO: 2021-03-15 13:37:46: __main__: Host Operating System is Darwin.
INFO: 2021-03-15 13:37:46: __main__: Workload Control Plane Network Type is  vsphere 
INFO: 2021-03-15 13:37:46: __main__: Begin Testing . . . 
INFO: 2021-03-15 13:37:46: __main__: 1-Checking Required YAML inputs for program: 
ERROR: 2021-03-15 13:37:46: __main__: ERROR - Missing required value for WCP_MGMT_STARTINGIP
ERROR: 2021-03-15 13:37:46: __main__: ERROR - Missing required value for WCP_MGMT_MASK
ERROR: 2021-03-15 13:37:46: __main__: ERROR - Missing required value for WCP_MGMT_GATEWAY
INFO: 2021-03-15 13:37:46: __main__: 2-Checking Network Communication for vCenter
INFO: 2021-03-15 13:37:46: __main__: 2a-Checking IP is Active for vCenter
INFO: 2021-03-15 13:37:48: __main__: SUCCESS - Can ping 10.173.13.81. 
INFO: 2021-03-15 13:37:48: __main__: 2b-Checking DNS Servers are reachable on network
INFO: 2021-03-15 13:37:50: __main__: SUCCESS - Can ping 10.173.13.90. 
INFO: 2021-03-15 13:37:50: __main__: 2c-Checking Name Resolution for vCenter
INFO: 2021-03-15 13:37:51: __main__: Checking DNS Server 10.173.13.90 for A Record for vcsa.tpmlab.vmware.com
ERROR: 2021-03-15 13:37:51: __main__: ERROR - The Hostname, vcsa.tpmlab.vmware.com does not resolve to the IP 10.173.13.81
ERROR: 2021-03-15 13:37:51: __main__: ERROR - The IP, 10.173.13.81 does not resolve to the Hostname vcsa.tpmlab.vmware.com
INFO: 2021-03-15 13:37:51: __main__: 3-Checking VC is reachable via API using provided credentials
INFO: 2021-03-15 13:37:51: __main__: Trying to connect to VCENTER SERVER . . .
INFO: 2021-03-15 13:37:52: __main__: SUCCESS-Connected to vCenter VMware vCenter Server
INFO: 2021-03-15 13:37:52: __main__: 4-Checking for the  Datacenter
INFO: 2021-03-15 13:37:53: __main__: SUCCESS - Managed Object Datacenter found.
INFO: 2021-03-15 13:37:53: __main__: 5-Checking for the Cluster
INFO: 2021-03-15 13:37:53: __main__: SUCCESS - Cluster Object Nested-TKG-Cluster found.
INFO: 2021-03-15 13:37:53: __main__: 6-Checking Storage Profiles
INFO: 2021-03-15 13:37:53: __main__: 6a-Checking Connecting to SPBM
INFO: 2021-03-15 13:37:53: __main__: 6b-Getting Storage Profiles from SPBM
INFO: 2021-03-15 13:37:54: __main__: SUCCESS - Found Storage Profile thin.
ERROR: 2021-03-15 13:37:55: __main__: ERROR - Storage Profile thinner not found
INFO: 2021-03-15 13:37:55: __main__: 7-Checking for the Datastores
INFO: 2021-03-15 13:37:58: __main__: SUCCESS - Managed Object 66-datastore3 found.
INFO: 2021-03-15 13:37:58: __main__: 8-Checking for the vds
INFO: 2021-03-15 13:37:59: __main__: SUCCESS - Managed Object vds-1 found.
INFO: 2021-03-15 13:37:59: __main__: 9-Checking for the Primary Workload Network PortGroup
ERROR: 2021-03-15 13:38:01: __main__: ERROR - Managed Object not_there not found.
INFO: 2021-03-15 13:38:01: __main__: 10-Checking for the Workload Network PortGroup
ERROR: 2021-03-15 13:38:04: __main__: ERROR - Managed Object ext-uplink-edge not found.
INFO: 2021-03-15 13:38:04: __main__: 11-Checking HAProxy Health
INFO: 2021-03-15 13:38:04: __main__: 11a-Checking reachability of HAProxy Frontend IP
ERROR: 2021-03-15 13:38:17: __main__: ERROR - Cant ping 192.168.100.163. 
INFO: 2021-03-15 13:38:17: __main__: 11b-Skipping HAPROXY DataPlane API Login until IP is Active
INFO: 2021-03-15 13:38:17: __main__: 12-Establishing REST session to VC API
INFO: 2021-03-15 13:38:17: __main__: SUCCESS - Successfully established session to VC, status_code 
INFO: 2021-03-15 13:38:18: __main__: 13-Checking if cluster Nested-TKG-Cluster is WCP Compatible
ERROR: 2021-03-15 13:38:18: __main__: ERROR - Cluster domain-c30 is NOT compatible for reasons listed below.
ERROR: 2021-03-15 13:38:18: __main__: + Reason-Cluster domain-c30 is a personality-manager managed cluster. It currently does not support vSphere namespaces.
ERROR: 2021-03-15 13:38:18: __main__: + Reason-Cluster domain-c30 does not have HA enabled.
ERROR: 2021-03-15 13:38:18: __main__: + Reason-Cluster domain-c30 is missing compatible NSX-T VDS.
INFO: 2021-03-15 13:38:18: __main__: ************************************************
INFO: 2021-03-15 13:38:18: __main__: ** All checks were run. Validation Complete.  **
INFO: 2021-03-15 13:38:18: __main__: ************************************************

