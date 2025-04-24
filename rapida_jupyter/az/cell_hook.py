from IPython import get_ipython
from rapida_jupyter.az.authwidget import AuthWidget
from rapida_jupyter.util.in_notebook import in_notebook
from cbsurge.az.surgeauth import SurgeTokenCredential

def pre_cell_execution(exec_info):
    if in_notebook():
        aui = AuthWidget(SurgeTokenCredential())
        aui.render()


# Get the current IPython shell
ip = get_ipython()

# Register the pre_run_cell event
ip.events.register('pre_run_cell', pre_cell_execution)