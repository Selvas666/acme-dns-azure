locals {
  base_config = {
    sp_client_id     = azuread_service_principal.this.client_id
    sp_client_secret = azuread_application_password.this.value
    server           = "https://acme-staging-v02.api.letsencrypt.org/directory"
    tenant_id        = data.azurerm_client_config.current.tenant_id
    key_vault_id     = azurerm_key_vault.this.vault_uri
    eab = {
      enabled = false
    }
    "certbot.ini" = <<EOT
        key-type = rsa    
        rsa-key-size = ${var.key_size}
        break-my-certs = ${true}
      EOT
  }
}

output "integration_test_params" {
  value     = "--dns-zone-name ${data.azurerm_dns_zone.this.name} --dns-zone-resource-group-name ${data.azurerm_dns_zone.this.resource_group_name} --subscription-id ${data.azurerm_subscription.current.subscription_id} --keyvault-uri ${azurerm_key_vault.this.vault_uri}"
  sensitive = false
}

resource "local_file" "base_config" {
  content  = yamlencode(local.base_config)
  filename = "config.yaml"
}

