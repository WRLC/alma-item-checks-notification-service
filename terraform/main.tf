locals {
  service_name = "aic-notification-service"
  short_service_name = "aicns"
}

data "terraform_remote_state" "shared" {
  backend = "azurerm"
  config  = {
    resource_group_name: var.tf_shared_resource_group_name
    storage_account_name: var.tf_shared_storage_account_name
    container_name: var.tf_shared_container_name
    key: var.tf_shared_key
  }
}

data "azurerm_service_plan" "existing" {
  name                = data.terraform_remote_state.shared.outputs.app_service_plan_name
  resource_group_name = data.terraform_remote_state.shared.outputs.app_service_plan_resource_group
}

data "azurerm_resource_group" "existing" {
  name = data.terraform_remote_state.shared.outputs.resource_group_name
}

data "azurerm_storage_account" "existing" {
  name                     = data.terraform_remote_state.shared.outputs.storage_account_name
  resource_group_name      = data.terraform_remote_state.shared.outputs.resource_group_name
}

locals {
  storage_queues     = data.terraform_remote_state.shared.outputs.storage_queues
  storage_containers = data.terraform_remote_state.shared.outputs.storage_containers
}

data "azurerm_mysql_flexible_server" "existing" {
  name                = data.terraform_remote_state.shared.outputs.mysql_server_name
  resource_group_name = data.terraform_remote_state.shared.outputs.mysql_server_resource_group_name
}

data "azurerm_log_analytics_workspace" "existing" {
  name                = data.terraform_remote_state.shared.outputs.log_analytics_workspace_name
  resource_group_name = data.terraform_remote_state.shared.outputs.log_analytics_workspace_resource_group_name
}

data "azurerm_storage_account" "acs_email_sender" {
  name                = var.acs_email_sender_sa_name
  resource_group_name = var.acs_email_sender_sa_rg_name
}

resource "azurerm_application_insights" "main" {
  name                = local.service_name
  resource_group_name = data.azurerm_resource_group.existing.name
  location            = data.azurerm_resource_group.existing.location
  application_type    = "web"
  workspace_id        = data.azurerm_log_analytics_workspace.existing.id
}

# Create production MySQL database
resource "azurerm_mysql_flexible_database" "prod" {
  name                = local.short_service_name
  resource_group_name = data.azurerm_mysql_flexible_server.existing.resource_group_name
  server_name         = data.azurerm_mysql_flexible_server.existing.name
  charset             = "utf8mb4"
  collation           = "utf8mb4_unicode_ci"
}

# Create staging MySQL database
resource "azurerm_mysql_flexible_database" "stage" {
  name                = "${local.short_service_name}-stage"
  resource_group_name = data.azurerm_mysql_flexible_server.existing.resource_group_name
  server_name         = data.azurerm_mysql_flexible_server.existing.name
  charset             = "utf8mb4"
  collation           = "utf8mb4_unicode_ci"
}

# Generate random passwords for database users
resource "random_password" "prod_db_password" {
  length  = 32
  special = false
}

resource "random_password" "stage_db_password" {
  length  = 32
  special = false
}

# Create MySQL user for production with read access
resource "mysql_user" "prod_user" {
  user               = "${local.short_service_name}_user"
  host               = "%"
  plaintext_password = random_password.prod_db_password.result
}

# Create MySQL user for staging with read access
resource "mysql_user" "stage_user" {
  user               = "${local.short_service_name}_stage_user"
  host               = "%"
  plaintext_password = random_password.stage_db_password.result
}

# Grant read permissions to production user
resource "mysql_grant" "prod_grant" {
  user       = mysql_user.prod_user.user
  host       = mysql_user.prod_user.host
  database   = azurerm_mysql_flexible_database.prod.name
  privileges = [ "ALL PRIVILEGES" ]
}

# Grant read permissions to staging user
resource "mysql_grant" "stage_grant" {
  user       = mysql_user.stage_user.user
  host       = mysql_user.stage_user.host
  database   = azurerm_mysql_flexible_database.stage.name
  privileges = [ "ALL PRIVILEGES" ]
}


resource "azurerm_linux_function_app" "function_app" {
  name                       = local.service_name
  resource_group_name        = data.azurerm_resource_group.existing.name
  location                   = data.azurerm_resource_group.existing.location
  service_plan_id            = data.azurerm_service_plan.existing.id
  storage_account_name       = data.azurerm_storage_account.existing.name
  storage_account_access_key = data.azurerm_storage_account.existing.primary_access_key

  site_config {
    always_on        = true
    application_insights_connection_string = azurerm_application_insights.main.connection_string
    application_insights_key               = azurerm_application_insights.main.instrumentation_key
    application_stack {
      python_version = "3.12"
    }
  }


  app_settings = {
    "WEBSITE_RUN_FROM_PACKAGE"      = "1"
    "SQLALCHEMY_CONNECTION_STRING"  = "mysql+pymysql://${mysql_user.prod_user.user}:${random_password.prod_db_password.result}@${data.azurerm_mysql_flexible_server.existing.fqdn}:3306/${azurerm_mysql_flexible_database.prod.name}"
    "NOTIFICATION_QUEUE"            = local.storage_queues["notification-queue"]
    "REPORTS_CONTAINER"             = local.storage_containers["reports-container"]
    "ACS_STORAGE_CONNECTION_STRING" = data.azurerm_storage_account.acs_email_sender.primary_connection_string
    "ACS_SENDER_QUEUE_NAME"         = "inputqueue"
    "ACS_SENDER_CONTAINER_NAME"     = "inputcontainer"
  }

  sticky_settings {
    app_setting_names = [
      "SQLALCHEMY_CONNECTION_STRING",
      "NOTIFICATION_QUEUE",
      "UPDATED_ITEMS_CONTAINER",
      "REPORTS_CONTAINER",
      "ACS_SENDER_QUEUE_NAME",
      "ACS_SENDER_CONTAINER_NAME"
    ]
  }
}

resource "azurerm_linux_function_app_slot" "staging_slot" {
  name                       = "stage"
  function_app_id            = azurerm_linux_function_app.function_app.id
  storage_account_name       = data.azurerm_storage_account.existing.name
  storage_account_access_key = data.azurerm_storage_account.existing.primary_access_key

  site_config {
    always_on                              = true
    application_insights_connection_string = azurerm_application_insights.main.connection_string
    application_insights_key               = azurerm_application_insights.main.instrumentation_key
    application_stack {
      python_version                       = "3.12"
    }
  }

  app_settings = {
    "WEBSITE_RUN_FROM_PACKAGE"     = "1"
    "SQLALCHEMY_CONNECTION_STRING" = "mysql+pymysql://${mysql_user.stage_user.user}:${random_password.stage_db_password.result}@${data.azurerm_mysql_flexible_server.existing.fqdn}:3306/${azurerm_mysql_flexible_database.stage.name}"
    "NOTIFICATION_QUEUE"           = local.storage_queues["notification-queue-stage"]
    "REPORTS_CONTAINER"             = local.storage_containers["reports-container-stage"]
    "ACS_STORAGE_CONNECTION_STRING" = data.azurerm_storage_account.acs_email_sender.primary_connection_string
    "ACS_SENDER_QUEUE_NAME"         = "inputqueue-stage"
    "ACS_SENDER_CONTAINER_NAME"     = "inputcontainer-stage"
  }
}
