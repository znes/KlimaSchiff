import os

import paramiko


def connect(server="5.35.252.104", username="rutherford"):
    """ Connect to server via ssh
    """
    ssh = paramiko.SSHClient()
    ssh.load_host_keys(os.path.expanduser(os.path.join("~", ".ssh", "known_hosts")))
    ssh.connect(server, username)
    sftp = ssh.open_sftp()

    return sftp, ssh
