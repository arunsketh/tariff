import io
import pandas as pd
import streamlit as st

try:
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

# ==============================================================================
# PAGE CONFIGURATION
# ==============================================================================
st.set_page_config(
    page_title="UK Electricity Time-of-Use Tariff Comparator",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ==============================================================================
# RECONCILED JAN-SEP 2026 DATA (UK LOCAL TIME, CALIBRATED TO FUSE PDF ACTUALS)
# ==============================================================================
MONTHS = [
    "2026-01", "2026-02", "2026-03",
    "2026-04", "2026-05", "2026-06",
    "2026-07", "2026-08", "2026-09",
]

MONTHLY_DAYS = {
    "2026-01": 31, "2026-02": 28, "2026-03": 31,
    "2026-04": 30, "2026-05": 31, "2026-06": 30,
    "2026-07": 31, "2026-08": 31, "2026-09": 30,
}

ACTUAL_FUSE_PDF_BILLS = {
    "2026-01": 143.11, "2026-02": 137.67, "2026-03": 118.74,
    "2026-04": 105.04, "2026-05": 91.12,  "2026-06": 86.24,
    "2026-07": 81.02,  "2026-08": 80.77,  "2026-09": 78.48,
}

# Reconciled hourly kWh per month (index 0 = 00:00-00:59 ... 23 = 23:00-23:59)
HOURLY_KWH = {
    "2026-01": [8.998914, 6.064524, 5.369339, 5.586804, 7.037991, 8.740045, 6.753383, 25.678460, 34.462891, 28.726684, 28.202094, 28.046274, 29.610790, 23.698063, 22.626881, 21.503383, 19.978975, 25.405365, 47.117465, 39.771429, 35.560670, 35.538786, 57.953541, 35.829250],
    "2026-02": [7.053538, 5.397071, 5.206652, 4.685480, 6.664602, 7.992980, 5.964678, 23.875332, 32.546988, 27.188891, 27.157100, 33.559604, 30.523105, 22.205886, 23.679519, 21.457613, 19.075596, 24.403374, 47.996867, 38.315752, 30.276669, 32.058221, 52.426234, 39.941248],
    "2026-03": [7.673617, 4.923561, 4.467814, 5.266730, 6.101850, 7.022381, 6.528047, 21.019933, 25.367220, 23.256216, 21.901488, 23.028506, 26.447706, 19.554423, 18.730862, 16.605177, 15.899430, 20.647558, 36.760567, 37.026835, 27.032516, 27.824058, 46.438304, 27.583199],
    "2026-04": [7.218627, 5.599404, 5.352769, 5.136398, 5.871439, 7.883166, 5.492197, 20.621029, 27.479997, 23.895586, 22.378407, 23.141167, 25.070752, 17.962095, 18.733357, 18.348249, 16.799163, 21.789252, 34.227676, 29.745654, 25.482748, 25.244508, 44.850992, 33.211369],
    "2026-05": [8.518247, 6.978828, 6.236349, 6.257016, 8.609384, 9.394918, 7.354259, 14.770838, 21.285321, 19.978685, 18.456619, 18.778856, 20.521611, 14.159912, 14.818443, 13.658364, 12.640583, 16.675335, 27.582867, 25.253963, 21.220877, 23.033664, 37.236700, 23.962362],
    "2026-06": [8.281834, 7.318381, 7.323579, 6.171387, 7.767853, 11.166714, 8.259253, 15.998030, 20.021241, 17.947317, 17.496592, 19.901596, 19.838351, 14.146726, 13.733694, 13.254448, 12.512261, 15.174190, 25.541186, 21.735452, 19.270723, 17.238529, 32.777331, 21.643334],
    "2026-07": [8.689270, 8.159393, 7.482204, 6.308844, 10.095596, 12.817793, 9.086900, 14.137281, 18.673669, 16.820987, 13.057154, 16.806805, 15.274340, 12.336953, 12.986808, 13.228297, 11.376772, 11.953431, 21.821728, 19.592072, 18.123820, 17.411546, 32.923155, 16.148183],
    "2026-08": [7.932516, 7.118017, 6.534412, 6.221984, 8.588869, 10.722592, 7.296610, 14.120653, 17.981821, 15.223587, 15.076381, 17.619577, 17.494601, 14.253104, 12.099689, 12.491632, 11.388241, 14.519799, 25.195580, 19.924513, 17.848094, 16.962715, 28.377545, 19.012466],
    "2026-09": [9.072528, 7.532155, 7.125792, 6.854285, 9.706260, 11.690400, 10.142581, 14.331206, 19.348331, 15.653125, 13.347523, 16.637601, 16.110140, 11.565803, 12.294550, 11.265067, 10.538130, 13.314547, 21.267735, 19.624304, 14.720404, 15.009928, 29.058287, 18.270319],
}

PRESETS = {
    "Octopus 3-Tier (Screenshot)": {
        "w1_start": 16, "w1_end": 19, "w1_rate": 42.13,
        "w2_start": 19, "w2_end": 2,  "w2_rate": 23.53,
        "w3_start": 2,  "w3_end": 5,  "w3_rate": 15.40,
        "w4_start": 5,  "w4_end": 16, "w4_rate": 23.53,
        "comp_sc": 57.23,
    },
    "Fuse Single Rate Fixed (Apr+)": {
        "w1_start": 16, "w1_end": 19, "w1_rate": 19.38,
        "w2_start": 19, "w2_end": 2,  "w2_rate": 19.38,
        "w3_start": 2,  "w3_end": 5,  "w3_rate": 19.38,
        "w4_start": 5,  "w4_end": 16, "w4_rate": 19.38,
        "comp_sc": 45.54,
    },
    "EV / Intelligent Night (00-05 @ 7p)": {
        "w1_start": 16, "w1_end": 19, "w1_rate": 24.50,
        "w2_start": 19, "w2_end": 0,  "w2_rate": 24.50,
        "w3_start": 0,  "w3_end": 5,  "w3_rate": 7.00,
        "w4_start": 5,  "w4_end": 16, "w4_rate": 24.50,
        "comp_sc": 57.23,
    },
    "Economy 7 Style (00-07 @ 13.5p)": {
        "w1_start": 16, "w1_end": 19, "w1_rate": 29.50,
        "w2_start": 19, "w2_end": 0,  "w2_rate": 29.50,
        "w3_start": 0,  "w3_end": 7,  "w3_rate": 13.50,
        "w4_start": 7,  "w4_end": 16, "w4_rate": 29.50,
        "comp_sc": 55.00,
    },
}


def hours_in_window(start_h: int, end_h: int) -> list[int]:
    """Return list of integer hours [start_h, end_h) wrapping past midnight."""
    start_h %= 24
    end_h %= 24
    if start_h == end_h:
        return []
    if start_h < end_h:
        return list(range(start_h, end_h))
    return list(range(start_h, 24)) + list(range(0, end_h))


def init_state():
    defaults = {
        "preset_name": "Octopus 3-Tier (Screenshot)",
        "use_exact_pdf": True,
        "base_pre_apr": 21.93,
        "base_post_apr": 19.38,
        "base_sc": 45.54,
        "shift_w1_pct": 0.0,
        "shift_w4_pct": 0.0,
    }
    defaults.update(PRESETS["Octopus 3-Tier (Screenshot)"])
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def apply_preset_callback():
    preset = PRESETS.get(st.session_state["preset_name"])
    if preset:
        for k, v in preset.items():
            st.session_state[k] = v


def reset_all_callback():
    st.session_state["preset_name"] = "Octopus 3-Tier (Screenshot)"
    st.session_state["use_exact_pdf"] = True
    st.session_state["base_pre_apr"] = 21.93
    st.session_state["base_post_apr"] = 19.38
    st.session_state["base_sc"] = 45.54
    st.session_state["shift_w1_pct"] = 0.0
    st.session_state["shift_w4_pct"] = 0.0
    apply_preset_callback()


init_state()

# ==============================================================================
# SIDEBAR CONTROLS
# ==============================================================================
with st.sidebar:
    st.title("⚡ Tariff Controls")

    st.subheader("1. Baseline Tariff (Fuse Energy)")
    st.checkbox(
        "Lock to exact Fuse PDF bills (£922.19)",
        key="use_exact_pdf",
    )
    b_col1, b_col2 = st.columns(2)
    with b_col1:
        st.number_input(
            "Jan–Mar (p/kWh)",
            min_value=0.0,
            max_value=200.0,
            step=0.01,
            format="%.2f",
            key="base_pre_apr",
            disabled=st.session_state["use_exact_pdf"],
        )
    with b_col2:
        st.number_input(
            "Apr–Sep (p/kWh)",
            min_value=0.0,
            max_value=200.0,
            step=0.01,
            format="%.2f",
            key="base_post_apr",
            disabled=st.session_state["use_exact_pdf"],
        )
    st.number_input(
        "Baseline Standing Charge (p/day)",
        min_value=0.0,
        max_value=300.0,
        step=0.01,
        format="%.2f",
        key="base_sc",
        disabled=st.session_state["use_exact_pdf"],
    )

    st.divider()
    st.subheader("2. Comparison Tariff (4 Windows)")
    st.selectbox(
        "Load Tariff Preset",
        options=list(PRESETS.keys()),
        key="preset_name",
        on_change=apply_preset_callback,
    )

    window_defs = [
        ("W1 Peak", "w1_start", "w1_end", "w1_rate"),
        ("W2 Eve/Night", "w2_start", "w2_end", "w2_rate"),
        ("W3 Super Off", "w3_start", "w3_end", "w3_rate"),
        ("W4 Daytime", "w4_start", "w4_end", "w4_rate"),
    ]

    for label, ks, ke, kr in window_defs:
        st.markdown(f"**{label}**")
        c1, c2, c3 = st.columns([1, 1, 1.4])
        with c1:
            st.number_input("Start", min_value=0, max_value=23, step=1, key=ks, label_visibility="collapsed")
        with c2:
            st.number_input("End", min_value=0, max_value=23, step=1, key=ke, label_visibility="collapsed")
        with c3:
            st.number_input("p/kWh", min_value=0.0, max_value=200.0, step=0.01, format="%.2f", key=kr, label_visibility="collapsed")

    st.number_input(
        "Comparison Standing Charge (p/day)",
        min_value=0.0,
        max_value=300.0,
        step=0.01,
        format="%.2f",
        key="comp_sc",
    )

    # Validate 24-hour coverage
    w1_h = hours_in_window(int(st.session_state["w1_start"]), int(st.session_state["w1_end"]))
    w2_h = hours_in_window(int(st.session_state["w2_start"]), int(st.session_state["w2_end"]))
    w3_h = hours_in_window(int(st.session_state["w3_start"]), int(st.session_state["w3_end"]))
    w4_h = hours_in_window(int(st.session_state["w4_start"]), int(st.session_state["w4_end"]))
    combined_h = w1_h + w2_h + w3_h + w4_h
    unique_h = set(combined_h)

    if len(combined_h) == 24 and len(unique_h) == 24:
        st.success("24/24 hours mapped cleanly (no gaps or overlaps).")
    else:
        missing_h = sorted(set(range(24)) - unique_h)
        st.warning(f"Assigned {len(combined_h)}h ({len(unique_h)} unique). Unassigned hours: {missing_h}")

    st.divider()
    st.subheader("3. Load-Shifting Simulator")
    st.caption("Simulate moving usage onto timers in W3 Super Off-Peak:")
    st.slider("Shift W1 Peak → W3 (%)", 0.0, 100.0, step=1.0, key="shift_w1_pct")
    st.slider("Shift W4 Daytime → W3 (%)", 0.0, 100.0, step=1.0, key="shift_w4_pct")

    st.button("Reset to Defaults", on_click=reset_all_callback, use_container_width=True)


# ==============================================================================
# CORE CALCULATION ENGINE
# ==============================================================================
r1 = st.session_state["w1_rate"] / 100.0
r2 = st.session_state["w2_rate"] / 100.0
r3 = st.session_state["w3_rate"] / 100.0
r4 = st.session_state["w4_rate"] / 100.0
sc_comp = st.session_state["comp_sc"] / 100.0

b_pre = st.session_state["base_pre_apr"] / 100.0
b_post = st.session_state["base_post_apr"] / 100.0
sc_base = st.session_state["base_sc"] / 100.0

s1_frac = st.session_state["shift_w1_pct"] / 100.0
s4_frac = st.session_state["shift_w4_pct"] / 100.0

records = []
for m in MONTHS:
    hrs = HOURLY_KWH[m]
    days = MONTHLY_DAYS[m]
    tot_kwh = sum(hrs)

    k1_raw = sum(hrs[h] for h in w1_h)
    k2_raw = sum(hrs[h] for h in w2_h)
    k3_raw = sum(hrs[h] for h in w3_h)
    k4_raw = sum(hrs[h] for h in w4_h)

    moved_1 = k1_raw * s1_frac
    moved_4 = k4_raw * s4_frac

    k1 = k1_raw - moved_1
    k2 = k2_raw
    k3 = k3_raw + moved_1 + moved_4
    k4 = k4_raw - moved_4

    c1, c2, c3, c4 = k1 * r1, k2 * r2, k3 * r3, k4 * r4
    sc_cost = days * sc_comp
    comp_bill = c1 + c2 + c3 + c4 + sc_cost

    if st.session_state["use_exact_pdf"]:
        base_bill = ACTUAL_FUSE_PDF_BILLS[m]
    else:
        b_rate = b_pre if m <= "2026-03" else b_post
        base_bill = tot_kwh * b_rate + days * sc_base

    diff = comp_bill - base_bill
    records.append({
        "Month": m,
        "Days": days,
        "Total_kWh": tot_kwh,
        "W1_kWh": k1,
        "W2_kWh": k2,
        "W3_kWh": k3,
        "W4_kWh": k4,
        "W1_Pct": (k1 / tot_kwh * 100.0) if tot_kwh else 0.0,
        "W2_Pct": (k2 / tot_kwh * 100.0) if tot_kwh else 0.0,
        "W3_Pct": (k3 / tot_kwh * 100.0) if tot_kwh else 0.0,
        "W4_Pct": (k4 / tot_kwh * 100.0) if tot_kwh else 0.0,
        "W1_Cost": c1,
        "W2_Cost": c2,
        "W3_Cost": c3,
        "W4_Cost": c4,
        "Standing_Charge": sc_cost,
        "New_Bill": comp_bill,
        "Baseline_Bill": base_bill,
        "Diff_GBP": diff,
        "Diff_Pct": (diff / base_bill * 100.0) if base_bill else 0.0,
    })

df = pd.DataFrame(records)

tot_days = int(df["Days"].sum())
tot_kwh = df["Total_kWh"].sum()
tot_base = df["Baseline_Bill"].sum()
tot_comp = df["New_Bill"].sum()
tot_diff = tot_comp - tot_base
tot_diff_pct = (tot_diff / tot_base * 100.0) if tot_base else 0.0

tot_usage_cost = df[["W1_Cost", "W2_Cost", "W3_Cost", "W4_Cost"]].sum().sum()
blended_p = (tot_usage_cost / tot_kwh * 100.0) if tot_kwh else 0.0
base_usage_cost = tot_base - (tot_days * sc_base)
base_blended_p = (base_usage_cost / tot_kwh * 100.0) if tot_kwh else 0.0


# ==============================================================================
# MAIN DASHBOARD UI
# ==============================================================================
st.title("UK Electricity Time-of-Use Tariff Comparator")
st.caption("Reconciled Jan–Sep 2026 Smart Meter + Fuse Energy PDF Actuals (3,902.262 kWh | 273 Days | Europe/London)")

# KPI Metrics Row
k_col1, k_col2, k_col3, k_col4, k_col5 = st.columns(5)

with k_col1:
    st.metric(
        label="9-Month Baseline Bill",
        value=f"£{tot_base:,.2f}",
        delta=f"Avg £{tot_base / 9:.2f}/mo ({base_blended_p:.2f}p/kWh)",
        delta_color="off",
    )

with k_col2:
    st.metric(
        label="Comparison Tariff Bill",
        value=f"£{tot_comp:,.2f}",
        delta=f"Avg £{tot_comp / 9:.2f}/mo (SC £{df['Standing_Charge'].sum():.2f})",
        delta_color="off",
    )

with k_col3:
    sign = "+" if tot_diff > 0 else ""
    st.metric(
        label="Net Difference",
        value=f"{sign}£{tot_diff:,.2f}",
        delta=f"{sign}{tot_diff_pct:.2f}% vs. baseline",
        delta_color="inverse",
    )

with k_col4:
    st.metric(
        label="Effective Blended Rate",
        value=f"{blended_p:.2f}p/kWh",
        delta=f"{blended_p - base_blended_p:+.2f}p vs. baseline",
        delta_color="inverse",
    )

with k_col5:
    tot_w1_kwh = df["W1_kWh"].sum()
    spread = r1 - r3
    if tot_diff <= 0:
        st.metric("Break-Even Shift", "0 kWh", delta="Already cheaper than baseline", delta_color="normal")
    elif spread > 0:
        req_kwh = tot_diff / spread
        req_pct = (req_kwh / tot_w1_kwh * 100.0) if tot_w1_kwh > 0 else 999.0
        st.metric(
            label="Break-Even Shift (W1→W3)",
            value=f"{req_kwh:,.0f} kWh",
            delta=f"{req_pct:.1f}% of W1 Peak ({tot_w1_kwh:.0f} kWh)",
            delta_color="off",
        )
    else:
        st.metric("Break-Even Shift", "N/A", delta="W3 rate >= W1 rate", delta_color="off")

st.divider()

# Charts Section
tab_bill, tab_hourly = st.tabs(["📊 Monthly Bill Comparison (£)", "🕒 24-Hour Load Profile & Window Assignment"])

with tab_bill:
    if HAS_PLOTLY:
        fig = go.Figure()
        fig.add_trace(
            go.Bar(
                x=df["Month"],
                y=df["Baseline_Bill"],
                name="Baseline Bill (£)",
                marker_color="#64748B",
                text=[f"£{v:.2f}" for v in df["Baseline_Bill"]],
                textposition="outside",
            )
        )
        fig.add_trace(
            go.Bar(
                x=df["Month"],
                y=df["New_Bill"],
                name="Comparison Tariff (£)",
                marker_color="#2563EB",
                text=[f"£{v:.2f}" for v in df["New_Bill"]],
                textposition="outside",
            )
        )
        fig.update_layout(
            barmode="group",
            yaxis_title="Monthly Bill (£)",
            xaxis_title="Billing Month",
            height=360,
            margin=dict(l=20, r=20, t=30, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            yaxis=dict(range=[0, max(df["Baseline_Bill"].max(), df["New_Bill"].max()) * 1.18]),
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        chart_df = df.set_index("Month")[["Baseline_Bill", "New_Bill"]]
        st.bar_chart(chart_df, height=340)

with tab_hourly:
    hourly_totals = [sum(HOURLY_KWH[m][h] for m in MONTHS) for h in range(24)]
    hour_labels = [f"{h:02d}:00" for h in range(24)]
    win_names = []
    win_colors = []
    for h in range(24):
        if h in w1_h:
            win_names.append(f"W1 Peak ({st.session_state['w1_rate']:.2f}p)")
            win_colors.append("#DC2626")
        elif h in w3_h:
            win_names.append(f"W3 Super Off ({st.session_state['w3_rate']:.2f}p)")
            win_colors.append("#059669")
        elif h in w2_h:
            win_names.append(f"W2 Eve/Night ({st.session_state['w2_rate']:.2f}p)")
            win_colors.append("#2563EB")
        elif h in w4_h:
            win_names.append(f"W4 Daytime ({st.session_state['w4_rate']:.2f}p)")
            win_colors.append("#4F46E5")
        else:
            win_names.append("Unassigned")
            win_colors.append("#94A3B8")

    if HAS_PLOTLY:
        fig_hr = go.Figure(
            go.Bar(
                x=hour_labels,
                y=hourly_totals,
                marker_color=win_colors,
                text=win_names,
                hovertemplate="<b>%{x}</b><br>9-Month Usage: %{y:.2f} kWh<br>Window: %{text}<extra></extra>",
            )
        )
        fig_hr.update_layout(
            yaxis_title="9-Month Total Consumption (kWh)",
            xaxis_title="Local Hour (Europe/London)",
            height=360,
            margin=dict(l=20, r=20, t=25, b=20),
        )
        st.plotly_chart(fig_hr, use_container_width=True)
    else:
        hr_df = pd.DataFrame({"Hour": hour_labels, "kWh": hourly_totals}).set_index("Hour")
        st.bar_chart(hr_df, height=340)

# Monthly Breakdown Table Section
st.subheader("Monthly Breakdown Table")
t_col1, t_col2 = st.columns([3, 1])
with t_col1:
    table_view = st.radio(
        "Table Display Mode",
        options=["Cost Breakdown (£)", "Consumption Share (%)", "Consumption Volume (kWh)", "Full Combined Data"],
        horizontal=True,
    )

w1_tag = f"W1 ({int(st.session_state['w1_start']):02d}-{int(st.session_state['w1_end']):02d})"
w2_tag = f"W2 ({int(st.session_state['w2_start']):02d}-{int(st.session_state['w2_end']):02d})"
w3_tag = f"W3 ({int(st.session_state['w3_start']):02d}-{int(st.session_state['w3_end']):02d})"
w4_tag = f"W4 ({int(st.session_state['w4_start']):02d}-{int(st.session_state['w4_end']):02d})"

# Build summary row
summary_row = pd.DataFrame([{
    "Month": "TOTAL",
    "Days": tot_days,
    "Total_kWh": tot_kwh,
    "W1_kWh": df["W1_kWh"].sum(),
    "W2_kWh": df["W2_kWh"].sum(),
    "W3_kWh": df["W3_kWh"].sum(),
    "W4_kWh": df["W4_kWh"].sum(),
    "W1_Pct": (df["W1_kWh"].sum() / tot_kwh * 100.0),
    "W2_Pct": (df["W2_kWh"].sum() / tot_kwh * 100.0),
    "W3_Pct": (df["W3_kWh"].sum() / tot_kwh * 100.0),
    "W4_Pct": (df["W4_kWh"].sum() / tot_kwh * 100.0),
    "W1_Cost": df["W1_Cost"].sum(),
    "W2_Cost": df["W2_Cost"].sum(),
    "W3_Cost": df["W3_Cost"].sum(),
    "W4_Cost": df["W4_Cost"].sum(),
    "Standing_Charge": df["Standing_Charge"].sum(),
    "New_Bill": tot_comp,
    "Baseline_Bill": tot_base,
    "Diff_GBP": tot_diff,
    "Diff_Pct": tot_diff_pct,
}])

full_df = pd.concat([df, summary_row], ignore_index=True)

if table_view == "Cost Breakdown (£)":
    disp_df = full_df[[
        "Month", "Days", "Total_kWh",
        "W1_Cost", "W2_Cost", "W3_Cost", "W4_Cost",
        "Standing_Charge", "New_Bill", "Baseline_Bill", "Diff_GBP", "Diff_Pct"
    ]].rename(columns={
        "Total_kWh": "Total kWh",
        "W1_Cost": f"{w1_tag} (£)",
        "W2_Cost": f"{w2_tag} (£)",
        "W3_Cost": f"{w3_tag} (£)",
        "W4_Cost": f"{w4_tag} (£)",
        "Standing_Charge": "Stand. Chg (£)",
        "New_Bill": "New Bill (£)",
        "Baseline_Bill": "Baseline (£)",
        "Diff_GBP": "Diff (£)",
        "Diff_Pct": "Diff (%)",
    })
    fmt = {
        "Total kWh": "{:.2f}",
        f"{w1_tag} (£)": "£{:.2f}",
        f"{w2_tag} (£)": "£{:.2f}",
        f"{w3_tag} (£)": "£{:.2f}",
        f"{w4_tag} (£)": "£{:.2f}",
        "Stand. Chg (£)": "£{:.2f}",
        "New Bill (£)": "£{:.2f}",
        "Baseline (£)": "£{:.2f}",
        "Diff (£)": "{:+.2f}",
        "Diff (%)": "{:+.2f}%",
    }
elif table_view == "Consumption Share (%)":
    disp_df = full_df[[
        "Month", "Days", "Total_kWh",
        "W1_Pct", "W2_Pct", "W3_Pct", "W4_Pct",
        "New_Bill", "Baseline_Bill", "Diff_GBP"
    ]].rename(columns={
        "Total_kWh": "Total kWh",
        "W1_Pct": f"{w1_tag} (%)",
        "W2_Pct": f"{w2_tag} (%)",
        "W3_Pct": f"{w3_tag} (%)",
        "W4_Pct": f"{w4_tag} (%)",
        "New_Bill": "New Bill (£)",
        "Baseline_Bill": "Baseline (£)",
        "Diff_GBP": "Diff (£)",
    })
    fmt = {
        "Total kWh": "{:.2f}",
        f"{w1_tag} (%)": "{:.2f}%",
        f"{w2_tag} (%)": "{:.2f}%",
        f"{w3_tag} (%)": "{:.2f}%",
        f"{w4_tag} (%)": "{:.2f}%",
        "New Bill (£)": "£{:.2f}",
        "Baseline (£)": "£{:.2f}",
        "Diff (£)": "{:+.2f}",
    }
elif table_view == "Consumption Volume (kWh)":
    disp_df = full_df[[
        "Month", "Days", "Total_kWh",
        "W1_kWh", "W2_kWh", "W3_kWh", "W4_kWh",
        "New_Bill", "Baseline_Bill", "Diff_GBP"
    ]].rename(columns={
        "Total_kWh": "Total kWh",
        "W1_kWh": f"{w1_tag} (kWh)",
        "W2_kWh": f"{w2_tag} (kWh)",
        "W3_kWh": f"{w3_tag} (kWh)",
        "W4_kWh": f"{w4_tag} (kWh)",
        "New_Bill": "New Bill (£)",
        "Baseline_Bill": "Baseline (£)",
        "Diff_GBP": "Diff (£)",
    })
    fmt = {
        "Total kWh": "{:.2f}",
        f"{w1_tag} (kWh)": "{:.2f}",
        f"{w2_tag} (kWh)": "{:.2f}",
        f"{w3_tag} (kWh)": "{:.2f}",
        f"{w4_tag} (kWh)": "{:.2f}",
        "New Bill (£)": "£{:.2f}",
        "Baseline (£)": "£{:.2f}",
        "Diff (£)": "{:+.2f}",
    }
else:
    disp_df = full_df.copy()
    fmt = {col: "{:.2f}" for col in disp_df.columns if col not in ("Month", "Days")}

st.dataframe(
    disp_df.style.format(fmt),
    use_container_width=True,
    hide_index=True,
    height=390,
)

# CSV Export Button
csv_buffer = io.StringIO()
full_df.to_csv(csv_buffer, index=False)
with t_col2:
    st.download_button(
        label="⬇️ Download Full CSV",
        data=csv_buffer.getvalue(),
        file_name="tariff_comparison_2026.csv",
        mime="text/csv",
        use_container_width=True,
    )
