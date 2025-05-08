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
            checkboxes = [widgets.Checkbox(value=False, description=session.get_variable_title(component=component, variable=v)) for v in variables]

            if len(checkboxes) > 5:
                cols = 2 if len(checkboxes) <= 10 else 3
                rows = (len(checkboxes) + cols - 1) // cols
                grid = widgets.GridBox(
                    children=checkboxes,
                    layout=widgets.Layout(
                        grid_template_columns=' '.join(['auto'] * cols),
                        grid_gap="5px 5px"
                    )
                )
                var_container = grid
            else:
                var_container = widgets.VBox(checkboxes)

            tab_panels[component] = var_container
            tab_children.append(var_container)

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
                    selected_vars = [
                        session.get_var_id_from_title(cb.description) for cb in var_box.children
                        if isinstance(cb, widgets.Checkbox) and cb.value
                    ]
                    if isinstance(var_box, widgets.GridBox):
                        selected_vars = [
                            session.get_var_id_from_title(cb.description) for cb in var_box.children if cb.value
                        ]
                    for var in selected_vars:
                        cmd_args = f"-c {component} -v {var}"
                        run_cmd("assess", cmd_args)
                        print(cmd_args)
            btn.description = "Run Assessment"
            btn.disabled = False

        title_widget = widgets.Label(value="Run Assessment")
        run_assessment_btn.on_click(run_assessment)

        display(title_widget, tabs, run_assessment_btn, output)