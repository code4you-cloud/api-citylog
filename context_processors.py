import subprocess
import platform
import socket
import os
import importlib
import pkg_resources
from django.conf import settings
from django.conf import settings


def get_git_branch():
    try:
        return subprocess.check_output(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
            stderr=subprocess.DEVNULL
        ).decode('utf-8').strip()
    except:
        return "N/A"


def get_db_info():
    db_config = settings.DATABASES['default']
    return {
        'engine': db_config['ENGINE'].split('.')[-1],
        'name': db_config['NAME'],
        'host': db_config.get('HOST', 'localhost'),
    }


def get_host_ip(hostname):
    """Recupera l'IP associato all'hostname"""
    try:
        return socket.gethostbyname(hostname)
    except socket.gaierror:
        return "N/A"


def get_package_version(package_name, app_path=None):
    """Recupera la versione di un pacchetto usando diversi metodi"""

    # Metodo 1: pkg_resources (per pacchetti installati)
    try:
        return pkg_resources.get_distribution(package_name).version
    except pkg_resources.DistributionNotFound:
        pass

    # Metodo 2: importlib.metadata (Python 3.8+)
    try:
        import importlib.metadata
        return importlib.metadata.version(package_name)
    except (ImportError, importlib.metadata.PackageNotFoundError):
        pass

    # Metodo 3: Poetry - cerca pyproject.toml
    if app_path:
        try:
            pyproject_path = find_pyproject_toml(app_path)
            if pyproject_path:
                version = get_version_from_pyproject(pyproject_path)
                if version:
                    return version
        except:
            pass

    # Metodo 4: __version__ nel modulo
    try:
        module = importlib.import_module(package_name)
        return getattr(module, '__version__', 'N/A')
    except ImportError:
        pass

    # Metodo 5: _version.py o version.py
    try:
        version_module = importlib.import_module(f"{package_name}._version")
        return getattr(version_module, '__version__', 'N/A')
    except ImportError:
        try:
            version_module = importlib.import_module(f"{package_name}.version")
            return getattr(version_module, '__version__', 'N/A')
        except ImportError:
            pass

    return 'N/A'


def find_pyproject_toml(start_path):
    """Cerca pyproject.toml risalendo nella gerarchia"""
    current_path = start_path
    while current_path != '/':
        pyproject_path = os.path.join(current_path, 'pyproject.toml')
        if os.path.exists(pyproject_path):
            return pyproject_path
        current_path = os.path.dirname(current_path)
    return None


def get_version_from_pyproject(pyproject_path):
    """Estrae la versione da pyproject.toml"""
    try:
        with open(pyproject_path, 'r') as f:
            content = f.read()

        # Cerca la versione nella sezione [tool.poetry]
        import re
        version_match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
        if version_match:
            return version_match.group(1)

        # Cerca dynamic version
        if 'dynamic' in content and 'version' in content:
            # Prova a cercare in __init__.py o _version.py
            project_dir = os.path.dirname(pyproject_path)
            for version_file in ['__init__.py', '_version.py', 'version.py']:
                version_path = os.path.join(project_dir, version_file)
                if os.path.exists(version_path):
                    with open(version_path, 'r') as f:
                        version_content = f.read()
                    version_match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', version_content)
                    if version_match:
                        return version_match.group(1)

    except Exception:
        pass

    return None


def get_git_branch_for_path(path):
    """Recupera il branch Git per un percorso specifico"""
    try:
        current_path = path
        project_git_path = None

        # Prima trova il .git del progetto principale
        project_root = os.getcwd()
        if os.path.exists(os.path.join(project_root, '.git')):
            project_git_path = project_root

        # Cerca .git nel percorso dell'app
        while current_path != '/' and current_path:
            git_path = os.path.join(current_path, '.git')
            if os.path.exists(git_path):
                # Verifica se questo .git è diverso dal progetto principale
                if current_path != project_git_path:
                    # Trovato un repository Git specifico per questo package
                    return subprocess.check_output(
                        ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                        cwd=current_path,
                        stderr=subprocess.DEVNULL
                    ).decode('utf-8').strip()
                else:
                    # È il repository del progetto principale
                    break
            current_path = os.path.dirname(current_path)

        # Se il percorso dell'app è dentro il progetto principale
        if project_git_path and path.startswith(project_git_path):
            # Verifica se è un pacchetto installato in site-packages
            if 'site-packages' in path or 'dist-packages' in path:
                # Anche se è in site-packages, potrebbe essere un link simbolico
                if os.path.islink(path):
                    real_path = os.path.realpath(path)
                    return get_git_branch_for_path(real_path)
                return 'N/A'  # Pacchetto installato normalmente
            else:
                # È parte del progetto principale
                return subprocess.check_output(
                    ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                    cwd=project_git_path,
                    stderr=subprocess.DEVNULL
                ).decode('utf-8').strip()

        # Per pacchetti in site-packages, verifica se sono editable installs
        if 'site-packages' in path:
            # Cerca .pth files o egg-link files che potrebbero indicare un'installazione editable
            parent_dir = os.path.dirname(path)
            for file in os.listdir(parent_dir):
                if file.endswith('.egg-link') or file.endswith('.pth'):
                    try:
                        with open(os.path.join(parent_dir, file), 'r') as f:
                            link_path = f.readline().strip()
                            if os.path.exists(link_path):
                                return get_git_branch_for_path(link_path)
                    except:
                        pass

        return 'N/A'
    except:
        return 'N/A'


def get_editable_install_path(package_name):
    """Cerca il percorso di un pacchetto installato in modalità editable"""
    try:
        # Metodo 1: Controlla pip list --editable
        result = subprocess.run(
            ['pip', 'list', '--editable', '--format=json'],
            capture_output=True,
            text=True,
            stderr=subprocess.DEVNULL
        )

        if result.returncode == 0:
            import json
            editable_packages = json.loads(result.stdout)
            for pkg in editable_packages:
                if pkg['name'].lower() == package_name.lower():
                    # Prova a trovare il percorso dal location
                    location = pkg.get('location', '')
                    if location and os.path.exists(location):
                        return location

        # Metodo 2: Cerca nei file .pth in site-packages
        import site
        for site_packages in site.getsitepackages():
            if os.path.exists(site_packages):
                for file in os.listdir(site_packages):
                    if file.endswith('.pth'):
                        try:
                            with open(os.path.join(site_packages, file), 'r') as f:
                                content = f.read()
                                if package_name.lower() in content.lower():
                                    lines = content.strip().split('\n')
                                    for line in lines:
                                        if os.path.exists(line.strip()):
                                            return line.strip()
                        except:
                            pass

        # Metodo 3: Cerca file .egg-link
        for site_packages in site.getsitepackages():
            egg_link_path = os.path.join(site_packages, f"{package_name}.egg-link")
            if os.path.exists(egg_link_path):
                try:
                    with open(egg_link_path, 'r') as f:
                        path = f.readline().strip()
                        if os.path.exists(path):
                            return path
                except:
                    pass
    except:
        pass

    return None


def is_development_package(package_name, app_path):
    """Verifica se un pacchetto è in modalità development"""
    try:
        # Metodo 1: Controlla pip list --editable
        result = subprocess.run(
            ['pip', 'list', '--editable', '--format=json'],
            capture_output=True,
            text=True,
            stderr=subprocess.DEVNULL
        )

        if result.returncode == 0:
            import json
            editable_packages = json.loads(result.stdout)
            for pkg in editable_packages:
                if pkg['name'].lower() == package_name.lower():
                    return True
    except:
        pass

    # Metodo 2: Verifica se il percorso contiene .git
    if os.path.exists(os.path.join(app_path, '.git')):
        return True

    # Metodo 3: Risali nella gerarchia per cercare .git
    current_path = app_path
    while current_path != '/' and current_path:
        if os.path.exists(os.path.join(current_path, '.git')):
            return True
        current_path = os.path.dirname(current_path)

    # Metodo 4: Verifica se è un link simbolico
    if os.path.islink(app_path):
        return True

    return False


def get_git_branch_for_package(package_name, app_path):
    """Recupera il branch Git per un pacchetto, considerando anche installazioni editable"""

    # Prima prova il percorso normale
    branch = get_git_branch_for_path(app_path)
    if branch != 'N/A':
        return branch

    # Se non trovato, cerca se è un pacchetto editable
    editable_path = get_editable_install_path(package_name)
    if editable_path:
        return get_git_branch_for_path(editable_path)

    # Controlla se il pacchetto è nel progetto corrente
    project_root = os.getcwd()
    project_package_path = os.path.join(project_root, package_name)
    if os.path.exists(project_package_path):
        return get_git_branch_for_path(project_package_path)

    # Cerca nelle sottocartelle del progetto
    for root, dirs, files in os.walk(project_root):
        if package_name in dirs:
            potential_path = os.path.join(root, package_name)
            branch = get_git_branch_for_path(potential_path)
            if branch != 'N/A':
                return branch

    return 'N/A'


def get_apps_info():
    """Ottiene informazioni solo sulle app presenti in INSTALLED_APPS"""
    from django.apps import apps

    apps_info = []
    for app_config in apps.get_app_configs():
        app_name = app_config.name

        # Distingui tra app Django builtin, app del progetto e pacchetti esterni
        if app_name.startswith('django.contrib') or app_name.startswith('django.'):
            package_name = 'django'
            is_builtin = True
            is_dev_package = False
        else:
            package_name = app_name.split('.')[0]
            is_builtin = False
            is_dev_package = is_development_package(package_name, app_config.path)

        app_info = {
            'name': app_config.name.split('.')[-1],
            'verbose_name': app_config.verbose_name,
            'path': app_config.path,
            'is_builtin': is_builtin,
            'is_dev_package': is_dev_package,
        }

        if app_info['is_dev_package']:
            app_info['git_branch'] = get_git_branch_for_path(app_config.path)
        else:
            app_info['git_branch'] = 'N/A'

        # Recupera la versione del pacchetto
        app_info['version'] = get_package_version(package_name, app_config.path)

        # Recupera il branch Git
        if is_builtin:
            app_info['git_branch'] = 'N/A - builtin'  # Le app Django builtin non hanno branch Git
        else:
            # Usa la nuova funzione migliorata per il branch
            app_info['git_branch'] = get_git_branch_for_package(package_name, app_config.path)

        apps_info.append(app_info)

    return apps_info


def system_info(request):
    if not getattr(settings, 'SYSTEM_INFO_ENABLED', settings.DEBUG):
        return {}

    hostname = socket.gethostname()
    return {
        'git_branch': get_git_branch(),
        'db_info': get_db_info(),
        'debug_mode': settings.DEBUG,
        'django_version': getattr(settings, 'DJANGO_VERSION', 'N/A'),
        'hostname': hostname,
        'ip': get_host_ip(hostname),
        'python_version': platform.python_version(),
        'os': platform.system(),
        'apps_info': get_apps_info(),
        "system_info_template": getattr(settings, "SYSTEM_INFO_TEMPLATE", None),
    }
