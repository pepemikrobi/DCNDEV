FROM ubuntu:24.04.4

RUN apt-get update && \ 
    apt-get upgrade -y && \
    apt-get install -y apt-utils && \
    apt-get install -y gcc git curl python3-virtualenv python3-pip ssh jq gnupg software-properties-common
RUN curl -fsSL https://apt.releases.hashicorp.com/gpg | apt-key add - && \
    apt-add-repository "deb [arch=amd64] https://apt.releases.hashicorp.com $(lsb_release -cs) main" && \
    apt-get update && \
    apt-get install -y vault
RUN virtualenv /root/ansible
RUN . /root/ansible/bin/activate && \
    pip install --upgrade pip && \
    pip install requests-toolbelt && \
    pip install urllib3 && \
    pip install requests && \
    pip install jmespath && \        
    pip install ansible==13.5 && \
    pip install dnacentersdk==2.8.6 && \
    pip install ansible-lint && \ 
    ansible-galaxy collection install cisco.dnac==6.33.2 
COPY ./SDN_CA.crt /usr/local/share/ca-certificates/
RUN update-ca-certificates
