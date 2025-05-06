import ipywidgets as widgets
from IPython.display import display
from rapida.cli.assess import getComponents
from rapida.session import Session
from rapida.cli.run import run_cmd
import os

dir_stack = []

def pushd(new_dir):
    current_dir = os.getcwd()
    dir_stack.append(current_dir)
    os.chdir(new_dir)

def popd():
    if dir_stack:
        previous_dir = dir_stack.pop()
        os.chdir(previous_dir)
    else:
        print("Directory stack is empty.")

def assessment_gui(project_path):
    pushd(project_path)
    with Session() as session:
        components = getComponents()
        tab_panels = {}
        tab_children = []

        for component in components:
            variables = session.get_variables(component=component)
            var_checkboxes = [widgets.Checkbox(value=False, description=v) for v in variables]
            var_box = widgets.VBox(var_checkboxes)
            tab_panels[component] = var_box
            tab_children.append(var_box)

        tabs = widgets.Tab(children=tab_children)
        for i, component in enumerate(components):
            tabs.set_title(i, component)

        run_assessment_btn = widgets.Button(
            description="Run Assessment",
            button_style='info',
            tooltip='Run Assessment'
        )

        output = widgets.Output()

        def run_assessment(btn):
            btn.description = "Running..."
            btn.disabled = True
            with output:
                output.clear_output()
                for component, var_box in tab_panels.items():
                    selected_vars = [cb.description for cb in var_box.children if cb.value]
                    for var in selected_vars:
                        cmd_args = f"-c {component} -v {var}"
                        run_cmd("assess", cmd_args)
                        print(cmd_args)
            btn.description = "Run Assessment"
            btn.disabled = False

        title_widget = widgets.Label(value="Run Assessment")
        run_assessment_btn.on_click(run_assessment)

        display(title_widget, tabs, run_assessment_btn, output)