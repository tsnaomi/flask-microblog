from fabric.api import run
from fabric.api import env
from fabric.api import prompt
from fabric.api import execute
from fabric.api import sudo
from fabric.contrib.project import rsync_project
from fabric.contrib.files import sed
from fabric.contrib.files import exists
import boto.ec2
import time

env.aws_region = 'us-west-2'


env.hosts = ['localhost', ]


def deploy():
    select_instance()
    sync_instance()
    install_all()


def config_all():
    config_nginx()
    config_supervisor


def run_command_on_selected_server(command, select_hosts=None):
    """Runs 'command' methods on selected server"""
    if not select_hosts:
        select_instance()
        select_hosts = [
            'ubuntu@' + env.active_instance.public_dns_name
        ]
    execute(command, hosts=select_hosts)


def install_packages():
    run_command_on_selected_server(_install_packages)


def install_all():
    run_command_on_selected_server(_install_packages)
    run_command_on_selected_server(_pip_install)


def pip_install():
        run_command_on_selected_server(_pip_install)


def pip_uninstall():
        run_command_on_selected_server(_pip_uninstall)


def restart_supervisor():
    """Restarts supervisor on the server through bash command"""
    run_command_on_selected_server(_restart_supervisor)


def config_supervisor():
    """First checks for 'app.conf' file. Then copies 'app.conf' file to
    /etc/supervisor/conf.d/ folder """
    run_command_on_selected_server(_config_supervisor)
    run_command_on_selected_server(_restart_supervisor)


def restart_nginx():
    """Restarts nginx on the server through bash command"""
    run_command_on_selected_server(_restart_nginx)


def config_nginx():
    """First checks for 'default.orig' file. If not, sets original 'default'
    file as 'default.orig', and moves 'simple_nginx_config' as new 'default'
    file. Then configures the 'default' server_name to current instance
    server name by passing instance name and running sed command
    in server"""
    run_command_on_selected_server(_config_nginx)
    run_command_on_selected_server(_restart_nginx)


def config_psql():
    run_command_on_selected_server(_config_psql)
    run_command_on_selected_server(_restart_psql)


def sync_instance():
    """Runs rsync_project which synchronises home directory to
    current working directory. More extensions in the future"""
    run_command_on_selected_server(_rsync)


def _pip_install():
    sudo('pip install -r requirements.txt')


def _pip_uninstall():
    sudo('pip uninstall -r requirements.txt')


def _install_packages():
    command_text = """
    filename="packages.txt"
    packages="";
    while read -r package;
    do echo "here $package";
    packages="$packages $package";
    done < $filename
    sudo apt-get update
    sudo apt-get install$packages
    """
    sudo(command_text)


def _uninstall_packages():
    command_text = """
    filename="packages.txt"
    packages="";
    while read -r package;
    do echo "here $package";
    packages="$packages $package";
    done < $filename
    sudo apt-get update
    sudo apt-get remove$packages
    sudo apt-get autoremove
    """
    sudo(command_text)


def _restart_supervisor():
    sudo('service supervisor stop')
    sudo('service supervisor start')


def _config_supervisor():
    default_file = '/etc/supervisor/conf.d/app.conf'
    config_file = 'app.conf'
    if exists(config_file):
        sudo(' '.join(['cp', config_file, default_file]))
    else:
        print "ERROR: no app.conf file!"


def _restart_nginx():
    sudo('nginx -s reload')


def _config_nginx():
    server_name = 'http://' + env.active_instance.public_dns_name + '/;'
    default_file = '/etc/nginx/sites-available/default'
    default_orig_file = '/etc/nginx/sites-available/default.orig'
    config_file = 'simple_nginx_config'
    if not exists(default_orig_file):
        sudo(' '.join(['mv', default_file, default_orig_file]))
    if exists(config_file):
        sudo(' '.join(['cp', config_file, default_file]))
        sed(default_file,
            'http.*com/;$',
            server_name,
            use_sudo=True)
    else:
        print "ERROR: no simple_nginx_config file!"


def _rsync():
    rsync_project('~', '.')


def stop_instance():
    select_instance()
    env.active_instance.stop()
    print env.active_instance.state


def terminate_instance():
    select_instance()
    env.active_instance.terminate()
    print env.active_instance.state


def select_instance(state='running'):
    if env.get('active_instance', False):
        return

    list_aws_instances(state=state)

    prompt_text = "Please select from the following instances:\n"
    instance_template = " %(ct)d: %(state)s instance %(id)s\n"
    for idx, instance in enumerate(env.instances):
        ct = idx + 1
        args = {'ct': ct}
        args.update(instance)
        prompt_text += instance_template % args

    def validation(input):
        choice = int(input)
        if not choice in range(1, len(env.instances) + 1):
            raise ValueError("%d is not a valide instance:" % choice)
        return choice

    choice = prompt(prompt_text, validate=validation)
    env.active_instance = env.instances[choice - 1]['instance']


def list_aws_instances(verbose=False, state='all'):
    conn = get_ec2_connection()

    reservations = conn.get_all_reservations()
    instances = []
    for res in reservations:
        for instance in res.instances:
            if state == 'all' or instance.state == state:
                instance = {
                    'id': instance.id,
                    'type': instance.instance_type,
                    'image': instance.image_id,
                    'state': instance.state,
                    'instance': instance,
                    'link': instance.public_dns_name
                }
                instances.append(instance)
    env.instances = instances
    if verbose:
        import pprint
        pprint.pprint(env.instances)


def provision_instance(wait_for_running=False,
                       timeout=60,
                       interval=2):
    wait_val = int(interval)
    timeout_val = int(timeout)
    conn = get_ec2_connection()
    instance_type = 't1.micro'
    key_name = 'pk-aws'
    security_group = 'ssh-access'
    image_id = 'ami-fa9cf1ca'

    reservations = conn.run_instances(
        image_id,
        key_name=key_name,
        instance_type=instance_type,
        security_groups=[security_group, ]
    )
    new_instances = [i for i in reservations.instances
                     if i.state == u'pending']
    running_instance = []
    if wait_for_running:
        waited = 0
        while new_instances and (waited < timeout_val):
            time.sleep(wait_val)
            waited += int(wait_val)
            for instance in new_instances:
                state = instance.state
                print "Instance %s is %s" % (instance.id, state)
                if state == 'running':
                    running_instance.append(
                        new_instances.pop(new_instances.index(i))
                    )
                instance.update()


def get_ec2_connection():
    if 'ec2' not in env:
        conn = boto.ec2.connect_to_region(env.aws_region)
        if conn is not None:
            env.ec2 = conn
            print "Connected to EC2 region %s" % env.aws_region
        else:
            msg = "Unable to connect to EC2 region %s"
            raise IOError(msg % env.aws_region)
    return env.ec2


def host_type():
    run('uname -s')
