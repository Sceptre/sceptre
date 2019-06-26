import os
from datetime import datetime
import click

from sceptre.cli.helpers import catch_exceptions
from sceptre.cli.helpers import stack_status_exit_code
from sceptre.context import SceptreContext
from sceptre.plan.plan import SceptrePlan
import networkx as nx


@click.command(name="debug")
@click.argument("path")
@click.pass_context
@catch_exceptions
def debug_command(ctx, path):
    """
    Generate useful information for user to share when raising issues.

    Creates a stack for a given config PATH. Or if CHANGE_SET_NAME is specified
    creates a change set for stack in PATH.

    :param path: Path to a Stack or StackGroup
    :type path: str
    """

    context = SceptreContext(
        command_path=path,
        project_path=ctx.obj.get("project_path"),
        user_variables=ctx.obj.get("user_variables"),
        options=ctx.obj.get("options"),
        ignore_dependencies=ctx.obj.get("ignore_dependencies")
    )

    plan = SceptrePlan(context)
    # TODO add better logic, provide default directory within the project
    current_report = datetime.now().strftime("%Y%m%d-%H%M%S")
    report_path = os.path.join(context.project_path, 'debug_reports', current_report)
    os.makedirs(report_path, exist_ok=True)
    # responses = plan.debug(path)

    nx.drawing.nx_pydot.write_dot(
        plan.graph.graph,
        os.path.join(report_path, 'StackGraph.dot')
    )

    write_nodes_report(os.path.join(report_path, 'nodes-StackGraph.py'), plan.graph.graph)

    # write_tree_report(context.project_path, os.path.join(report_path, 'tree.txt'))
    #     print("runing")
    # pprint(, indent=4)
    # dd = plan.graph.as_dict_of_dicts()
    # import pdb;
    # pdb.set_trace()

    # print(context.project_path, context.command_path)
    # print(dir(context))
    exit()


def write_nodes_report(output_file, graph):
    with open(output_file, 'w+') as outf:
        for node in graph:
            print(node.__repr__(), file=outf)


def write_tree_report(start_path, output_file):
    """
    Write file tree into the file.

    :param start_path: Path where to start from.
    :type start_path: str
    :param output_file: Name of output file.
    :type output_file: str
    """

    with open(output_file, 'w+') as outf:
        indent = 4 * ' '
        for root, dirs, files in os.walk(start_path):
            try:
                # Try to remove cvs directories as they are not useful in report
                for cvs_system_dir in ('.git', '.hg'):
                    dirs.remove(cvs_system_dir)
            except ValueError:
                pass

            level = root.replace(start_path, '').count(os.sep)
            current_indent = indent * level
            indent_directory = '{}{}/ \n'.format(current_indent, os.path.basename(root))
            outf.write(indent_directory)
            sub_indent = current_indent + indent
            indent_files = ['{}{}'.format(sub_indent, file) for file in files]
            outf.write('\n'.join(indent_files))
            outf.write('\n')
