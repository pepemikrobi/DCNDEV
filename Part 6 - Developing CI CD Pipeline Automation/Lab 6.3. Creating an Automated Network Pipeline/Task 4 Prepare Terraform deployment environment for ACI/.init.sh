export GITLAB_ACCESS_TOKEN=${GITLAB_ACCESS_TOKEN}
export TF_STATE_NAME=${TF_STATE_NAME_ACI}
terraform init \
    -backend-config="address=https://pod5-mgmt.sdn.lab/api/v4/projects/${CI_PROJECT_ID}/terraform/state/$TF_STATE_NAME" \
    -backend-config="lock_address=https://pod5-mgmt.sdn.lab/api/v4/projects/${CI_PROJECT_ID}/terraform/state/$TF_STATE_NAME/lock" \
    -backend-config="unlock_address=https://pod5-mgmt.sdn.lab/api/v4/projects/${CI_PROJECT_ID}/terraform/state/$TF_STATE_NAME/lock" \
    -backend-config=username=${TF_USERNAME} \
    -backend-config=password=${GITLAB_ACCESS_TOKEN} \
    -backend-config="lock_method=POST" \
    -backend-config="unlock_method=DELETE" \
    -backend-config="retry_wait_min=5"
