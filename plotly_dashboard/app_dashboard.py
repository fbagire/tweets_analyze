import dash_bootstrap_components as dbc
from dash import Dash, dcc, html
from dash.dependencies import Output, Input
from app import app

# Connect to the layout and callbacks of each tab
from viz import viz_layout

# from trends import trends_layout
# from other import other_layout


app_tabs = html.Div(
    [
        dbc.Tabs(
            [
                dbc.Tab(label="Visualization", tab_id="tab-viz", labelClassName="text-success font-weight-bold",
                        activeLabelClassName="text-danger"),
                dbc.Tab(label="Trends", tab_id="tab-trends", labelClassName="text-success font-weight-bold",
                        activeLabelClassName="text-danger"),
                dbc.Tab(label="Other", tab_id="tab-other", labelClassName="text-success font-weight-bold",
                        activeLabelClassName="text-danger"),
            ],
            id="tabs",
            active_tab="tab-viz",
        ),
    ], className="mt-3"
)

app.layout = dbc.Container(
    [
        dbc.Row(dbc.Col(html.H3('Twitter Analysis Dashboard',
                                style={'textAlign': 'center', 'font_family': "Times New Roman", 'color': '#0F562F'}))),
        dbc.Row(dbc.Col(app_tabs, width=12), className="mb-3"),
        html.Div(id='content', children=[])

    ]
)


@app.callback(
    Output("content", "children"),
    [Input("tabs", "active_tab")]
)
def switch_tab(tab_chosen):
    if tab_chosen == "tab-viz":
        return viz_layout
    # elif tab_chosen == "tab-trends":
    #     return trends_layout
    # elif tab_chosen == "tab-other":
    # return other_layout
    return html.P("No Content for now...")


if __name__ == '__main__':
    app.run_server(debug=True)
