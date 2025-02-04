
source /home/cb535/.bashrc

source /classes/setup/setup-ece6745.sh -f

/classes/ece6745/install/venvs/py3.11.9-default/bin/python3 \
  /home/cb535/vc/git-hub/aidan-mcnay/courseflow/classes/ece6745-2025s/flows/github_setup_flow.py -s \
  -r /home/cb535/vc/git-hub/aidan-mcnay/courseflow/classes/ece6745-2025s/flows/github_setup_flow.yml \
  -l /home/cb535/vc/git-hub/aidan-mcnay/courseflow/classes/ece6745-2025s/flows/github_setup_flow.log

