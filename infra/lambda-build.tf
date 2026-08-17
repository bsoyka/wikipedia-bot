locals {
  build_script = "${path.module}/../scripts/build_lambda.sh"

  # The dependency layer only needs rebuilding when the resolved
  # dependency set changes, not on every source edit.
  layer_source_files = [
    "${path.module}/../pyproject.toml",
    "${path.module}/../uv.lock",
    local.build_script,
  ]
  layer_source_hash = sha256(join("", [for f in sort(local.layer_source_files) : filesha256(f)]))

  code_source_files = concat(
    [for f in fileset("${path.module}/../src", "**") : "${path.module}/../src/${f}"],
    [local.build_script],
  )
  code_source_hash = sha256(join("", [for f in sort(local.code_source_files) : filesha256(f)]))
}

resource "terraform_data" "layer_build" {
  triggers_replace = {
    source_hash = local.layer_source_hash
  }

  provisioner "local-exec" {
    command     = "./scripts/build_lambda.sh layer"
    working_dir = "${path.module}/.."
  }
}

resource "terraform_data" "code_build" {
  triggers_replace = {
    source_hash = local.code_source_hash
  }

  provisioner "local-exec" {
    command     = "./scripts/build_lambda.sh code"
    working_dir = "${path.module}/.."
  }
}

data "archive_file" "layer" {
  type        = "zip"
  source_dir  = "${path.module}/../build/layer"
  output_path = "${path.module}/../build/layer.zip"

  depends_on = [terraform_data.layer_build]
}

data "archive_file" "code" {
  type        = "zip"
  source_dir  = "${path.module}/../build/code"
  output_path = "${path.module}/../build/code.zip"

  depends_on = [terraform_data.code_build]
}
