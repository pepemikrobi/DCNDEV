export GITLAB_ACCESS_TOKEN=<YOUR-ACCESS-TOKEN>
export TF_STATE_NAME=catc
terraform init \
    -backend-config="address=https://podX-mgmt.sdn.lab/api/v4/projects/4/terraform/state/$TF_STATE_NAME" \
    -backend-config="lock_address=https://podX-mgmt.sdn.lab/api/v4/projects/4/terraform/state/$TF_STATE_NAME/lock" \
    -backend-config="unlock_address=https://podX-mgmt.sdn.lab/api/v4/projects/4/terraform/state/$TF_STATE_NAME/lock" \
    -backend-config="username=podX" \
    -backend-config="password=$GITLAB_ACCESS_TOKEN" \
    -backend-config="lock_method=POST" \
    -backend-config="unlock_method=DELETE" \
    -backend-config="retry_wait_min=5"
    