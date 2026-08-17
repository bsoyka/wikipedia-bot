locals {
  name_prefix = var.project_name

  common_tags = merge(
    {
      Project   = var.project_name
      ManagedBy = "terraform"
      Service   = "bsoykabot"
    },
    var.tags
  )
}
