variable client_id{}

variable client_secret{}
##
# Configure the Azure Provider
##
provider "azurerm" {
  version = "=2.8.0"
  features {}
}

##
# Define variables for location, service principal for AKS and Bastion VM Admin
##
variable "location" {
  type = map(string)
  default = {
    value  = "East US"
    suffix = "eastus" # The corresponding value of location that is used by Azure in naming AKS resource groups
  }
}


##
# Create a resource group for the azure resources
##
resource "azurerm_resource_group" "my_rg" {
  name     = "rg-private-aks-demo"
  location = var.location.value
}

##
# Create Vnet and subnet for the AKS cluster
##
resource "azurerm_virtual_network" "vnet_cluster" {
  name                = "vnet-private-aks-demo"
  location            = var.location.value
  resource_group_name = azurerm_resource_group.my_rg.name
  address_space       = ["10.1.0.0/16"]
}
resource "azurerm_subnet" "snet_cluster" {
  name                 = "snet-private-aks-demo"
  resource_group_name  = azurerm_resource_group.my_rg.name
  virtual_network_name = azurerm_virtual_network.vnet_cluster.name
  address_prefixes     = ["10.1.0.0/24"]
  # Enforce network policies to allow Private Endpoint to be added to the subnet
  enforce_private_link_endpoint_network_policies = true
}

##
# Create Vnet and subnet for the Bastion VM
##
resource "azurerm_virtual_network" "vnet_bastion" {
  name                = "vnet-bastion-demo"
  location            = var.location.value
  resource_group_name = azurerm_resource_group.my_rg.name
  address_space       = ["10.0.0.0/16"]
}
resource "azurerm_subnet" "snet_bastion_vm" {
  name                 = "snet-bastion-demo"
  resource_group_name  = azurerm_resource_group.my_rg.name
  virtual_network_name = azurerm_virtual_network.vnet_bastion.name
  address_prefixes     = ["10.0.0.0/24"]
}
resource "azurerm_subnet" "snet_azure_bastion_service" {
  # The subnet name cannot be changed as the azure bastion host depends on the same
  name                 = "AzureBastionSubnet"
  resource_group_name  = azurerm_resource_group.my_rg.name
  virtual_network_name = azurerm_virtual_network.vnet_bastion.name
  address_prefixes     = ["10.0.1.0/24"]
}

##
# Create Vnet peering for the bastion VM to be able to access the cluster Vnet and IPs
##
resource "azurerm_virtual_network_peering" "peering_bastion_cluster" {
  name                      = "peering_bastion_cluster"
  resource_group_name       = azurerm_resource_group.my_rg.name
  virtual_network_name      = azurerm_virtual_network.vnet_bastion.name
  remote_virtual_network_id = azurerm_virtual_network.vnet_cluster.id
}
resource "azurerm_virtual_network_peering" "peering_cluster_bastion" {
  name                      = "peering_cluster_bastion"
  resource_group_name       = azurerm_resource_group.my_rg.name
  virtual_network_name      = azurerm_virtual_network.vnet_cluster.name
  remote_virtual_network_id = azurerm_virtual_network.vnet_bastion.id
}

##
# Create the AKS Cluster
##
resource "azurerm_kubernetes_cluster" "my_aks" {
  name                = "aks-my-cluster"
  location            = var.location.value
  resource_group_name = azurerm_resource_group.my_rg.name
  dns_prefix          = "aks-cluster"
  # Make the cluster private
  private_cluster_enabled = true
  # Improve security using Azure AD, K8s roles and rolebindings. 
  # Each Azure AD user can gets his personal kubeconfig and permissions managed through AD Groups and Rolebindings
  role_based_access_control {
    enabled = true
  }
  # Enable Kubernetes Dashboard, if needed
  addon_profile {
    kube_dashboard {
      enabled = true
    }
  }
  # To prevent CIDR collition with the 10.0.0.0/16 Vnet
  network_profile {
    network_plugin     = "kubenet"
    docker_bridge_cidr = "192.167.0.1/16"
    dns_service_ip     = "192.168.1.1"
    service_cidr       = "192.168.0.0/16"
    pod_cidr           = "172.16.0.0/22"
  }

  default_node_pool {
    name           = "default"
    node_count     = 1
    vm_size        = "Standard_D2s_v3"
    vnet_subnet_id = azurerm_subnet.snet_cluster.id
  }

  service_principal {
    client_id     = var.client_id
    client_secret = var.client_secret
  }
}

##
# Link the Bastion Vnet to the Private DNS Zone generated to resolve the Server IP from the URL in Kubeconfig
##
resource "azurerm_private_dns_zone_virtual_network_link" "link_bastion_cluster" {
  name = "dnslink-bastion-cluster"
  # The Terraform language does not support user-defined functions, and so only the functions built in to the language are available for use.
  # The below code gets the private dns zone name from the fqdn, by slicing the out dns prefix
  private_dns_zone_name = join(".", slice(split(".", azurerm_kubernetes_cluster.my_aks.private_fqdn), 1, length(split(".", azurerm_kubernetes_cluster.my_aks.private_fqdn))))
  resource_group_name   = "MC_${azurerm_resource_group.my_rg.name}_${azurerm_kubernetes_cluster.my_aks.name}_${var.location.suffix}"
  virtual_network_id    = azurerm_virtual_network.vnet_bastion.id
}

##
# Create a Bastion VM
##
resource "azurerm_network_interface" "bastion_nic" {
  name                = "nic-bastion"
  location            = var.location.value
  resource_group_name = azurerm_resource_group.my_rg.name
  ip_configuration {
    name                          = "internal"
    subnet_id                     = azurerm_subnet.snet_bastion_vm.id
    private_ip_address_allocation = "Dynamic"
  }
}

resource "azurerm_linux_virtual_machine" "example" {
  name                            = "vm-bastion"
  location                        = var.location.value
  resource_group_name             = azurerm_resource_group.my_rg.name
  size                            = "Standard_D2_v2"
  admin_username                  = "terraform"
  admin_password                  = "Test@123"
  disable_password_authentication = false
  network_interface_ids = [
    azurerm_network_interface.bastion_nic.id,
  ]

  os_disk {
    caching              = "ReadWrite"
    storage_account_type = "Standard_LRS"
  }

  source_image_reference {
    publisher = "Canonical"
    offer     = "UbuntuServer"
    sku       = "16.04-LTS"
    version   = "latest"
  }
}

##
# Create an Azure Bastion Service to access the Bastion VM
##
resource "azurerm_public_ip" "pip_azure_bastion" {
  name                = "pip-azure-bastion"
  location            = var.location.value
  resource_group_name = azurerm_resource_group.my_rg.name

  allocation_method = "Static"
  sku               = "Standard"
}

resource "azurerm_bastion_host" "azure-bastion" {
  name                = "azure-bastion"
  location            = var.location.value
  resource_group_name = azurerm_resource_group.my_rg.name
  ip_configuration {
    name                 = "configuration"
    subnet_id            = azurerm_subnet.snet_azure_bastion_service.id
    public_ip_address_id = azurerm_public_ip.pip_azure_bastion.id
  }
}
