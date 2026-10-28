"""
Приложение Dash для интерактивного анализа населения мира.

Требования:
    pip install dash dash-bootstrap-components pandas plotly

Ожидаемый CSV (population_data.csv):
    country, continent, year, population, gdp_per_capita, life_expectancy, ...
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output
import dash_bootstrap_components as dbc


# ============================================================
# 1. Загрузка и подготовка данных
# ============================================================
df = pd.read_csv("population_data.csv")

# Базовая очистка: убираем строки без ключевых полей
df = df.dropna(subset=["country", "continent", "year"]).copy()
df["year"] = pd.to_numeric(df["year"], errors="coerce")
df = df.dropna(subset=["year"])
df["year"] = df["year"].astype(int)

# Определяем числовые меры (кроме года)
numeric_measures = [
    c for c in df.select_dtypes(include="number").columns if c != "year"
]
# population всегда первой
if "population" in numeric_measures:
    numeric_measures.remove("population")
    numeric_measures = ["population"] + numeric_measures

# Схлопываем потенциальные дубликаты country/year
agg_dict = {m: "mean" for m in numeric_measures}
agg_dict["continent"] = "first"
df = (
    df.groupby(["country", "year"], as_index=False)
    .agg(agg_dict)
    .loc[:, ["country", "continent", "year"] + numeric_measures]
)

# Списки для контролов
years = sorted(df["year"].dropna().unique().tolist())
countries = sorted(df["country"].dropna().unique().tolist())

default_countries = countries[:5] if len(countries) >= 5 else countries
default_year = years[-1]
default_bubble_y = (
    numeric_measures[1] if len(numeric_measures) > 1 else numeric_measures[0]
)

measure_options = [
    {"label": m.replace("_", " ").capitalize(), "value": m}
    for m in numeric_measures
]
year_options = [{"label": str(y), "value": y} for y in years]


# ============================================================
# 2. Инициализация приложения
# ============================================================
app = Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])
app.title = "Население мира — интерактивный анализ"
server = app.server  # для деплоя


# ============================================================
# 3. Layout
# ============================================================
app.layout = dbc.Container(
    [
        html.H2(
            "🌍 Интерактивный анализ населения мира",
            className="text-center mt-4 mb-3",
        ),
        html.P(
            "Исследуйте динамику населения по странам, сравнивайте меры "
            "и изучайте распределение по континентам.",
            className="text-center text-muted mb-4",
        ),

        # ---------- Блок 1: линейный график ----------
        dbc.Card(
            dbc.CardBody(
                [
                    html.H5("📈 Динамика по странам", className="card-title"),
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.Label("Выберите страны (мультивыбор):"),
                                    dcc.Dropdown(
                                        id="country-select",
                                        options=[
                                            {"label": c, "value": c}
                                            for c in countries
                                        ],
                                        value=default_countries,
                                        multi=True,
                                        placeholder="Начните вводить название страны…",
                                    ),
                                ],
                                md=8,
                            ),
                            dbc.Col(
                                [
                                    html.Label("Мера по оси Y:"),
                                    dcc.Dropdown(
                                        id="line-y",
                                        options=measure_options,
                                        value="population",
                                        clearable=False,
                                    ),
                                ],
                                md=4,
                            ),
                        ],
                        className="g-3",
                    ),
                    dcc.Loading(
                        dcc.Graph(id="line-chart", style={"height": "480px"}),
                        type="circle",
                    ),
                ]
            ),
            className="mb-4 shadow-sm",
        ),

        # ---------- Блок 2: пузырьковая диаграмма ----------
        dbc.Card(
            dbc.CardBody(
                [
                    html.H5(
                        "🫧 Пузырьковая диаграмма", className="card-title"
                    ),
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.Label("Ось X:"),
                                    dcc.Dropdown(
                                        id="bubble-x",
                                        options=measure_options,
                                        value="population",
                                        clearable=False,
                                    ),
                                ],
                                md=3,
                            ),
                            dbc.Col(
                                [
                                    html.Label("Ось Y:"),
                                    dcc.Dropdown(
                                        id="bubble-y",
                                        options=measure_options,
                                        value=default_bubble_y,
                                        clearable=False,
                                    ),
                                ],
                                md=3,
                            ),
                            dbc.Col(
                                [
                                    html.Label("Радиус пузыря:"),
                                    dcc.Dropdown(
                                        id="bubble-r",
                                        options=measure_options,
                                        value="population",
                                        clearable=False,
                                    ),
                                ],
                                md=3,
                            ),
                            dbc.Col(
                                [
                                    html.Label("Год (общий фильтр):"),
                                    dcc.Dropdown(
                                        id="year-select",
                                        options=year_options,
                                        value=default_year,
                                        clearable=False,
                                    ),
                                ],
                                md=3,
                            ),
                        ],
                        className="g-3",
                    ),
                    dcc.Loading(
                        dcc.Graph(id="bubble-chart", style={"height": "520px"}),
                        type="circle",
                    ),
                ]
            ),
            className="mb-4 shadow-sm",
        ),

        # ---------- Блок 3: столбчатая и круговая ----------
        dbc.Row(
            [
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.H5(
                                    "🏆 Топ-15 стран по населению",
                                    className="card-title",
                                ),
                                dcc.Loading(
                                    dcc.Graph(
                                        id="bar-chart",
                                        style={"height": "480px"},
                                    ),
                                    type="circle",
                                ),
                            ]
                        )
                    ),
                    md=6,
                    className="mb-4",
                ),
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.H5(
                                    "🥧 Распределение по континентам",
                                    className="card-title",
                                ),
                                dcc.Loading(
                                    dcc.Graph(
                                        id="pie-chart",
                                        style={"height": "480px"},
                                    ),
                                    type="circle",
                                ),
                            ]
                        )
                    ),
                    md=6,
                    className="mb-4",
                ),
            ],
            className="g-4",
        ),

        html.Footer(
            "Источник данных: population_data.csv · "
            "Построено с Dash и Plotly",
            className="text-center text-muted small py-4",
        ),
    ],
    fluid="xl",
    className="pb-4",
)


# ============================================================
# 4. Callback: линейный график
# ============================================================
@app.callback(
    Output("line-chart", "figure"),
    Input("country-select", "value"),
    Input("line-y", "value"),
)
def update_line_chart(selected_countries, y_measure):
    fig = go.Figure()
    if not selected_countries:
        fig.update_layout(
            title="Выберите хотя бы одну страну",
            template="plotly_white",
        )
        return fig

    data = df[df["country"].isin(selected_countries)].dropna(
        subset=[y_measure]
    )
    if data.empty:
        return go.Figure().update_layout(
            title=f"Нет данных по мере «{y_measure}»",
            template="plotly_white",
        )

    for country in selected_countries:
        sub = data[data["country"] == country].sort_values("year")
        if sub.empty:
            continue
        fig.add_trace(
            go.Scatter(
                x=sub["year"],
                y=sub[y_measure],
                mode="lines+markers",
                name=country,
                hovertemplate=(
                    f"<b>{country}</b><br>"
                    f"Год: %{{x}}<br>"
                    f"{y_measure}: %{{y:,.4~s}}<extra></extra>"
                ),
            )
        )

    fig.update_layout(
        title=f"Динамика: {y_measure}",
        xaxis_title="Год",
        yaxis_title=y_measure.replace("_", " ").capitalize(),
        template="plotly_white",
        legend_title="Страна",
        hovermode="x unified",
        margin=dict(l=40, r=20, t=60, b=40),
    )
    return fig


# ============================================================
# 5. Callback: пузырьковая диаграмма
# ============================================================
@app.callback(
    Output("bubble-chart", "figure"),
    Input("bubble-x", "value"),
    Input("bubble-y", "value"),
    Input("bubble-r", "value"),
    Input("year-select", "value"),
)
def update_bubble_chart(x_measure, y_measure, r_measure, year):
    data = df[df["year"] == year].dropna(
        subset=[x_measure, y_measure, r_measure]
    )
    # Радиус не может быть отрицательным/нулевым
    data = data[data[r_measure] > 0]

    if data.empty:
        return go.Figure().update_layout(
            title=f"Нет данных за {year} год",
            template="plotly_white",
        )

    fig = px.scatter(
        data,
        x=x_measure,
        y=y_measure,
        size=r_measure,
        color="continent",
        hover_name="country",
        size_max=55,
        opacity=0.75,
        log_x=False,
        log_y=False,
        title=f"Пузырьковая диаграмма — {year}",
        labels={
            x_measure: x_measure.replace("_", " ").capitalize(),
            y_measure: y_measure.replace("_", " ").capitalize(),
            r_measure: r_measure.replace("_", " ").capitalize(),
            "continent": "Континент",
        },
    )
    fig.update_layout(
        template="plotly_white",
        legend_title="Континент",
        margin=dict(l=40, r=20, t=60, b=40),
    )
    fig.update_traces(
        marker=dict(line=dict(width=0.5, color="white"))
    )
    return fig


# ============================================================
# 6. Callback: столбчатая диаграмма
# ============================================================
@app.callback(Output("bar-chart", "figure"), Input("year-select", "value"))
def update_bar_chart(year):
    data = df[df["year"] == year].dropna(subset=["population"])
    top15 = data.nlargest(15, "population").sort_values("population")

    if top15.empty:
        return go.Figure().update_layout(
            title=f"Нет данных за {year} год",
            template="plotly_white",
        )

    fig = px.bar(
        top15,
        x="population",
        y="country",
        orientation="h",
        color="continent",
        text="population",
        title=f"Топ-15 стран по населению — {year}",
        labels={
            "population": "Население",
            "country": "",
            "continent": "Континент",
        },
    )
    fig.update_traces(
        texttemplate="%{text:.3s}",
        textposition="outside",
        cliponaxis=False,
    )
    fig.update_layout(
        template="plotly_white",
        legend_title="Континент",
        margin=dict(l=20, r=40, t=60, b=40),
        xaxis_title="Население",
    )
    return fig


# ============================================================
# 7. Callback: круговая диаграмма
# ============================================================
@app.callback(Output("pie-chart", "figure"), Input("year-select", "value"))
def update_pie_chart(year):
    data = df[df["year"] == year].dropna(subset=["population", "continent"])
    if data.empty:
        return go.Figure().update_layout(
            title=f"Нет данных за {year} год",
            template="plotly_white",
        )

    grouped = (
        data.groupby("continent", as_index=False)["population"]
        .sum()
        .sort_values("population", ascending=False)
    )

    fig = px.pie(
        grouped,
        names="continent",
        values="population",
        hole=0.45,
        title=f"Население по континентам — {year}",
        labels={"continent": "Континент", "population": "Население"},
    )
    fig.update_traces(
        textinfo="percent+label",
        textposition="outside",
        marker=dict(line=dict(color="white", width=2)),
    )
    fig.update_layout(
        template="plotly_white",
        legend_title="Континент",
        margin=dict(l=20, r=20, t=60, b=20),
    )
    return fig


# ============================================================
# 8. Запуск
# ============================================================
if __name__ == "__main__":
    app.run(debug=True)