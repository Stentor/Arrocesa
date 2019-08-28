# -*- coding: utf-8 -*-
{
    "name": """Gantt Native view for Projects""",
    "summary": """Added support Gantt""",
    "category": "Project",
    "images": ['static/description/icon.png'],
    "version": "12.19.05.15.0",
    "description": """
        Update 1: python 3.6.3 and click to gantt line
        Fix: datalist check
        Update: Calendar
        Update: Project manual start - and date, sorting from kanban / stage, small fix.
        Update: Drag UI.
        Update: Contrain constrain_type
        Update: diff datetime checker
        Update: Folding
        Update: Remove Canvas and Draw Line by div.
        Update: version and remove js canvas
        Update: default value for task from project.
        Fix: Kanban change state - end date, Plan detail wrong task_id
        Fix: added if None date in task, do nothing.
        UI: more improve
        Update: Info for gantt bar and Critical path calculation.
        Update: Detail plan, fix ghost bar, fix default start time: allow neagative value..
        Update: Gantt for Projects View.
        Update: Resource for taks
        Update: Loop Detect.
        Fix: default date in auto sheduling
        Fix: predecessor
    """,
    "author": "Viktor Vorobjov",
    "license": "OPL-1",
    "website": "https://straga.github.io",
    "support": "vostraga@gmail.com",

    "depends": [
        "project",
        "hr_timesheet",
        "web_gantt_native",
        "web_widget_time_delta",
        "web_widget_colorpicker"
    ],
    "external_dependencies": {"python": [], "bin": []},
    "data": [
        'views/project_task_view.xml',
        'views/project_task_resource_view.xml',
        'views/project_task_detail_plan_view.xml',
        'views/project_calendar_access_view.xml',
        'views/resource_views.xml',
        'views/project_project_view.xml',
        'security/ir.model.access.csv',
    ],
    "qweb": [],
    "demo": [],

    "post_load": None,
    "pre_init_hook": None,
    "post_init_hook": None,
    "installable": True,
    "auto_install": False,
    "application": False,
}
