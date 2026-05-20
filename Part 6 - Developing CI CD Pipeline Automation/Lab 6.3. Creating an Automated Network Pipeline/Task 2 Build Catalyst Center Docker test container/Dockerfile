FROM ubuntu:24.04

RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y gnupg software-properties-common curl jq gcc git python3-virtualenv python3-pip
RUN curl -fsSL https://apt.releases.hashicorp.com/gpg | apt-key add - && \
    apt-add-repository "deb [arch=amd64] https://apt.releases.hashicorp.com $(lsb_release -cs) main" && \
    apt-get update && \
    apt-get install terraform && \
    apt-get install -y vault   
RUN virtualenv /root/pyats
RUN . /root/pyats/bin/activate && \
    pip install --upgrade pip && \    
    pip install --upgrade setuptools && \
    pip install urllib3 && \
    pip install requests && \
    pip install jmespath && \    
    pip install pyats[full] && \ 
    pip install dotenv  
COPY ./SDN_CA.crt /usr/local/share/ca-certificates/
RUN update-ca-certificates
