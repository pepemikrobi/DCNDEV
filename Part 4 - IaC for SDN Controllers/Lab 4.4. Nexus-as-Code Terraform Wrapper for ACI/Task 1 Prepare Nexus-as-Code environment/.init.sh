export GITLAB_ACCESS_TOKEN=glpat-<your_gitlab_token>
export TF_STATE_NAME=aci
terraform init \
    -backend-config="address=https://podX-mgmt.sdn.lab/api/v4/projects/3/terraform/state/$TF_STATE_NAME" \
    -backend-config="lock_address=https://podX-mgmt.sdn.lab/api/v4/projects/3/terraform/state/$TF_STATE_NAME/lock" \
    -backend-config="unlock_address=https://podX-mgmt.sdn.lab/api/v4/projects/3/terraform/state/$TF_STATE_NAME/lock" \
    -backend-config="username=podX" \
    -backend-config="password=$GITLAB_ACCESS_TOKEN" \
    -backend-config="lock_method=POST" \
    -backend-config="unlock_method=DELETE" \
    -backend-config="retry_wait_min=5"
