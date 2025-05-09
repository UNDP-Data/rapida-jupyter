import sys

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

def assessment_gui(project_path=None, component=None):
    pushd(project_path)
    with Session() as session:
        if component is None:
            components = session.get_components()
        else:
            components = [component]
        # components = getComponents()
        tab_panels = {}
        tab_checkboxes = {}
        tab_select_all_boxes = []
        tab_children = []

        for component in components:
            variables = session.get_variables(component=component)
            checkboxes = [widgets.Checkbox(value=False, description=session.get_variable_title(component=component, variable=v)) for v in variables]

            tab_checkboxes[component] = checkboxes

            select_all = widgets.Checkbox(value=False, description="Select All in Tab")

            def create_tab_toggle(select_all_box, checkbox_list):
                def on_toggle(change):
                    if change["name"] == "value" and change["new"] != change["old"]:
                        for cb in checkbox_list:
                            cb.unobserve_all()  # prevent cascading
                            cb.value = change["new"]
                            cb.observe(update_tab_select_all, names='value')
                return on_toggle

            def update_tab_select_all(change):
                # Check if all are selected/deselected to reflect in the main toggle
                all_checked = all(cb.value for cb in checkbox_list)
                any_unchecked = any(not cb.value for cb in checkbox_list)
                select_all.unobserve_all()
                select_all.value = all_checked
                select_all.observe(create_tab_toggle(select_all, checkbox_list), names='value')

            checkbox_list = checkboxes
            select_all.observe(create_tab_toggle(select_all, checkbox_list), names='value')

            for cb in checkbox_list:
                cb.observe(update_tab_select_all, names='value')

            tab_select_all_boxes.append(select_all)

            if len(checkboxes) > 5:
                cols = 2 if len(checkboxes) <= 10 else 3
                grid = widgets.GridBox(
                    children=checkboxes,
                    layout=widgets.Layout(grid_template_columns=' '.join(['auto'] * cols), grid_gap="5px 5px")
                )
                var_container = widgets.VBox([select_all, grid])
            else:
                var_container = widgets.VBox([select_all] + checkboxes)

            tab_panels[component] = var_container
            tab_children.append(var_container)

        tabs = widgets.Tab(children=tab_children)
        for i, component in enumerate(components):
            tabs.set_title(i, component)

        global_select_all = widgets.Button(description="Select All", button_style='success')
        global_deselect_all = widgets.Button(description="Deselect All", button_style='warning')

        def global_toggle(value):
            for component, cbs in tab_checkboxes.items():
                for cb in cbs:
                    cb.unobserve_all()
                    cb.value = value
                    cb.observe(update_tab_select_all, names='value')
                sel_all = tab_select_all_boxes[components.index(component)]
                sel_all.unobserve_all()
                sel_all.value = value
                sel_all.observe(create_tab_toggle(sel_all, cbs), names='value')

        global_select_all.on_click(lambda btn: global_toggle(True))
        global_deselect_all.on_click(lambda btn: global_toggle(False))

        run_assessment_btn = widgets.Button(description="Run Assessment", button_style='info')
        output = widgets.Output()

        def run_assessment(btn):
            btn.description = "Running..."
            btn.disabled = True
            global_select_all.disabled = True
            global_deselect_all.disabled = True
            with output:
                output.clear_output()
                for component, container in tab_panels.items():
                    widgets_in_box = container.children
                    if isinstance(widgets_in_box[1], widgets.GridBox):
                        cbs = widgets_in_box[1].children
                    else:
                        cbs = widgets_in_box[1:]  # after select_all
                    selected_vars = [
                        session.get_var_id_from_title(cb.description)
                        for cb in cbs if isinstance(cb, widgets.Checkbox) and cb.value
                    ]
                    for var in selected_vars:
                        cmd_args = f"-c {component} -v {var}"
                        btn.description = f"Running... {var}"
                        run_cmd("assess", cmd_args)
            btn.description = "Run Assessment"
            btn.disabled = False


        run_assessment_btn.on_click(run_assessment)


        display(
            widgets.Label(value="Run Assessment"),
            tabs,
            widgets.HBox([global_select_all, global_deselect_all, run_assessment_btn]),
            output
        )