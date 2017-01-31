from jupyter_core.paths import jupyter_data_dir
import subprocess
import os
import errno
import stat

PEM_FILE = os.path.join(jupyter_data_dir(), "notebook.pem")

c = get_config()

use_port = 8888
try:
    use_port = int(os.getenv("ENV_JUPYTER_PORT", 8888))
except Exception as e:
    use_port = 8888

c.NotebookApp.ip = "*"
c.NotebookApp.port = use_port
c.NotebookApp.open_browser = False

# Set a certificate if USE_HTTPS is set to any value
if "ENV_USE_HTTPS" in os.environ:

    if os.path.exists(PEM_FILE) == False:
        PEM_FILE = str(os.getenv("ENV_JUPYTER_PEM_FILE", "/opt/work/certs/jupyter.pem"))

    if not os.path.isfile(PEM_FILE):
        # Ensure PEM_FILE directory exists
        dir_name = os.path.dirname(PEM_FILE)
        try:
            os.makedirs(dir_name)
        except OSError as exc: # Python >2.5
            if exc.errno == errno.EEXIST and os.path.isdir(dir_name):
                pass
            else: raise
        # Generate a certificate if one doesn"t exist on disk
        subprocess.check_call(["openssl", "req", "-new", 
            "-newkey", "rsa:2048", "-days", "365", "-nodes", "-x509",
            "-subj", "/C=XX/ST=XX/L=XX/O=generated/CN=generated",
            "-keyout", PEM_FILE, "-out", PEM_FILE])
        # Restrict access to PEM_FILE
        os.chmod(PEM_FILE, stat.S_IRUSR | stat.S_IWUSR)
    c.NotebookApp.certfile = PEM_FILE

# Set a password if PASSWORD is set
if "ENV_JUPYTER_PASSWORD" in os.environ:
    from IPython.lib import passwd
    c.NotebookApp.password = passwd(os.environ["ENV_JUPYTER_PASSWORD"])
    del os.environ["ENV_JUPYTER_PASSWORD"]
else:
    c.NotebookApp.token = ''
    c.NotebookApp.password = ''
# end if password-securing this Jupyter instance

