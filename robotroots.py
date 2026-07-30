import streamlit as st
import sqlite3
import pandas as pd
import altair as alt
from datetime import date, datetime, timedelta
import os
import io
import random

# --- CONFIGURACIÓN INICIAL ---
st.set_page_config(page_title="GEA System ERP", page_icon="gea_logo.png", layout="wide")

# --- DISEÑO CORPORATIVO (Fondo Estampado y Cursor) ---
st.markdown("""
<style>
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    
    /* Fondo oscuro con estampado de germinados */
    .stApp {
        background: linear-gradient(rgba(10, 15, 10, 0.93), rgba(20, 5, 5, 0.95)), url('https://images.unsplash.com/photo-1576045057995-568f588f82fb?q=80&w=2070&auto=format&fit=crop');
        background-size: cover;
        background-attachment: fixed;
    }
    
    .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp p, .stApp label, .stApp span {
        color: #ecf0f1 !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    /* Puntero del mouse sofisticado */
    body, html, * {
        cursor: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><path fill="%234CAF50" d="M12 2L2 22h20L12 2z"/></svg>') 12 12, auto;
    }
    
    .stButton>button {
        border: 1px solid #4CAF50; background-color: transparent; color: #ecf0f1; transition: all 0.3s ease;
    }
    .stButton>button:hover { background-color: #4CAF50; color: white; }
</style>
""", unsafe_allow_html=True)

# --- BASE DE DATOS ---
def init_db():
    conn = sqlite3.connect('gea_system.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS produccion_final
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, producto TEXT, lote TEXT, tipo_bandeja TEXT, 
                 fecha_siembra TEXT, fecha_luz TEXT, estado_luz TEXT, fecha_cosecha TEXT, estado_cosecha TEXT, 
                 peso_bruto REAL, cantidad_tapers INTEGER, taper_envasado TEXT, peso_sobrante REAL, merma REAL, area TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS siembra_final
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, cultivo TEXT, bandejas INTEGER, semilla_g REAL, sustrato_g REAL, fecha TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS finanzas_final
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, tipo TEXT, concepto TEXT, cantidad INTEGER, monto REAL, fecha TEXT)''')
                 
    c.execute('''CREATE TABLE IF NOT EXISTS config_v2 (key TEXT PRIMARY KEY, value TEXT)''')
    c.execute("INSERT OR IGNORE INTO config_v2 (key, value) VALUES ('pin_jefe', 'GEA-Director-2026')")
    conn.commit()
    conn.close()

def add_data(table, data):
    conn = sqlite3.connect('gea_system.db')
    c = conn.cursor()
    placeholders = ','.join(['?']*len(data))
    c.execute(f"INSERT INTO {table} VALUES (null, {placeholders})", data)
    conn.commit()
    conn.close()

def get_data(table):
    conn = sqlite3.connect('gea_system.db')
    df = pd.read_sql_query(f"SELECT * FROM {table}", conn)
    conn.close()
    return df

def get_config(key):
    conn = sqlite3.connect('gea_system.db')
    c = conn.cursor()
    c.execute("SELECT value FROM config_v2 WHERE key=?", (key,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None

def set_config(key, value):
    conn = sqlite3.connect('gea_system.db')
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO config_v2 (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()

init_db()

PRODUCTOS = ["Rabanito morado/mix", "Rabanito rosado", "Rabanito rojo", "Brocoli", "Beterraga", "Linaza", "Girasol", "Cilantro", "Nabo", "Zanahoria"]
BANDEJAS = ["Bandeja chata", "Bandeja delgada", "Bandeja alta", "Bandeja verde"]
TAPERS = ["Taper 8nz", "Taper 12onz", "Taper 16onz"]
ESTADOS = ["Optimo", "Regular", "Deficiente"]
MESES_NOMBRES = {"01": "Enero", "02": "Febrero", "03": "Marzo", "04": "Abril", "05": "Mayo", "06": "Junio", "07": "Julio", "08": "Agosto", "09": "Septiembre", "10": "Octubre", "11": "Noviembre", "12": "Diciembre"}

def cargar_datos_demo():
    for mes_num, dias_mes in [("06", 30), ("07", 15)]:
        for _ in range(30):
            prod = random.choice(PRODUCTOS)
            fecha_cos = date(2026, int(mes_num), random.randint(1, dias_mes))
            fecha_sim = fecha_cos - timedelta(days=random.randint(7, 12))
            fecha_luz = fecha_sim + timedelta(days=random.randint(5, 7))
            estado_cos = random.choices(ESTADOS, weights=[0.6, 0.3, 0.1])[0]
            tapers = random.randint(3, 15)
            merma = random.uniform(5, 20) if estado_cos != "Deficiente" else random.uniform(50, 90)
            add_data("produccion_final", (prod, str(random.randint(1, 50)), "Bandeja Estándar", fecha_sim.strftime("%Y-%m-%d"), fecha_luz.strftime("%Y-%m-%d"), "Optimo", fecha_cos.strftime("%Y-%m-%d"), estado_cos, random.uniform(30, 50), tapers, "Taper 12onz", 0.0, merma, "Microgreens"))
            add_data("finanzas_final", ("Venta", prod, tapers, tapers*5.0, fecha_cos.strftime("%Y-%m-%d")))

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_data = None
if 'chat_history' not in st.session_state: st.session_state.chat_history = []
if 'reporte_ia' not in st.session_state: st.session_state.reporte_ia = ""

def logout():
    st.session_state.logged_in = False
    st.session_state.user_data = None
    st.rerun()

# --- LOGIN ---
if not st.session_state.logged_in:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        try: st.image("gea_logo.png", width=150)
        except: pass
        st.markdown("<h1 style='text-align: center; margin-bottom: 0px;'>GEA SYSTEM ERP</h1>", unsafe_allow_html=True)
        st.markdown("<h4 style='text-align: center; color: #bdc3c7; margin-top: 0px;'>Germinados Orgánicos Arequipa</h4>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #95a5a6;'>Plataforma Operativa de Producción, Calidad y Ventas</p>", unsafe_allow_html=True)
        st.markdown("<hr style='border: 1px solid #7f8c8d;'>", unsafe_allow_html=True)
        tab_jefe, tab_trab = st.tabs(["Acceso Gerencia", "Acceso Personal de Planta"])
        with tab_jefe:
            st.markdown("##### Ingrese sus credenciales de Director")
            pin_input = st.text_input("Código Maestro (PIN)", type="password", placeholder="••••••••")
            if st.button("Desbloquear Panel Directivo", use_container_width=True):
                if pin_input == get_config('pin_jefe'):
                    st.session_state.logged_in = True
                    st.session_state.user_data = {"nombre": "Director GEA", "rol": "jefe"}
                    st.rerun()
                else: st.error("Código Maestro incorrecto. Acceso denegado.")
        with tab_trab:
            st.markdown("##### Fichaje de Turno Operativo")
            area_trab = st.selectbox("Seleccione su Área de Trabajo", ["Siembra", "Microgreens", "Tienda"])
            pin_trab = st.text_input("PIN del Área Asignada", type="password", placeholder="••••")
            pins_areas = {"Siembra": "1234", "Microgreens": "5678", "Tienda": "9012"}
            if st.button("Fichar e Ingresar al Sistema", use_container_width=True):
                if pin_trab == pins_areas.get(area_trab):
                    st.session_state.logged_in = True
                    st.session_state.user_data = {"nombre": f"Operario de {area_trab}", "rol": "trabajador", "area": area_trab}
                    st.rerun()
                else: st.error("PIN de área incorrecto.")

else:
    user = st.session_state.user_data
    with st.sidebar:
        if os.path.exists("gea_logo.png"): st.image("gea_logo.png", width=80)
        st.write(f"**Bienvenido:**\n{user['nombre']}")
        if user['rol'] == 'jefe': st.write("**Sesión:** Gerencia\n**Conexión:** Encriptada SSL/TLS")
        else: st.write(f"**Área:** {user['area']}")
        st.markdown("---")
        if st.button("Cerrar Sesión"): logout()

    if user["rol"] == "trabajador":
        st.title(f"Panel de {user['area']}")
        
        if user['area'] == "Microgreens":
            st.subheader("Registro de Cosecha Microgreens")
            with st.expander("Carga de Registros vía Excel"):
                st.write("Suba el archivo Excel con el formato oficial. Los datos se enviarán automáticamente al panel directivo.")
                file_trab = st.file_uploader("Seleccionar archivo Excel", type=['xlsx'], key="excel_trab")
                if file_trab is not None:
                    try:
                        df_excel = pd.read_excel(file_trab, sheet_name='Hoja2')
                        df_excel.columns = df_excel.columns.str.strip()
                        for index, row in df_excel.iterrows():
                            prod = str(row.get('Identificación de Producto', '')).strip()
                            if prod == 'nan' or prod == '': continue
                            def parse_date(d):
                                try: return pd.to_datetime(d).strftime('%Y-%m-%d')
                                except: return date.today().strftime('%Y-%m-%d')
                            def map_state(s):
                                s = str(s)
                                if '✔' in s: return 'Optimo'
                                if '±' in s: return 'Regular'
                                if '✗' in s: return 'Deficiente'
                                return 'Optimo'
                            add_data("produccion_final", (prod, str(row.get('Numero de bandeja/Lote', '')).strip(), str(row.get('Tipo de bandeja', '')).strip(), parse_date(row.get('Fecha de siembra')), parse_date(row.get('Fecha de transición a la luz')), map_state(row.get('Estado del cultivo de transicion a la luz')), parse_date(row.get('Fecha de cosecha')), map_state(row.get('Estado del cultivo en cosecha')), float(row.get('Peso bruto', 0) or 0), int(row.get('Cantidad de tapers', 0) or 0), str(row.get('Taper usado para envasado', '')).strip(), float(row.get('Peso sobrante/ Remanente', 0) or 0), float(row.get('Merma', 0) or 0), "Microgreens"))
                        st.success(f"Proceso completado. Se han cargado {len(df_excel)} registros al sistema.")
                    except Exception as e: st.error(f"Error al procesar el archivo. Verifique el formato. Detalle: {e}")
            st.markdown("---")
            st.write("**Registro Manual Instantáneo**")
            with st.form("form_cosecha_v3"):
                c1, c2, c3 = st.columns(3)
                with c1: producto = st.selectbox("Identificación de Producto", PRODUCTOS); lote = st.text_input("Numero de bandeja/Lote", "1"); tipo_bandeja = st.selectbox("Tipo de bandeja", BANDEJAS)
                with c2: fecha_siembra = st.date_input("Fecha de siembra", date.today()); fecha_luz = st.date_input("Fecha de transición a la luz", date.today()); estado_luz = st.selectbox("Estado transición a la luz", ESTADOS)
                with c3: fecha_cosecha = st.date_input("Fecha de cosecha", date.today()); estado_cosecha = st.selectbox("Estado en cosecha", ESTADOS); peso_bruto = st.number_input("Peso bruto (g)", min_value=0.0, step=0.1)
                c4, c5 = st.columns(2)
                with c4: cantidad_tapers = st.number_input("Cantidad de tapers", min_value=0, step=1); taper_envasado = st.selectbox("Taper usado para envasado", TAPERS)
                with c5: peso_sobrante = st.number_input("Peso sobrante/Remanente (g)", min_value=0.0, step=0.1); merma = st.number_input("Merma (g)", min_value=0.0, step=0.1)
                if st.form_submit_button("Registrar en Sistema"):
                    add_data("produccion_final", (producto, lote, tipo_bandeja, fecha_siembra.strftime("%Y-%m-%d"), fecha_luz.strftime("%Y-%m-%d"), estado_luz, fecha_cosecha.strftime("%Y-%m-%d"), estado_cosecha, peso_bruto, cantidad_tapers, taper_envasado, peso_sobrante, merma, user['area']))
                    st.success("Registro guardado en base de datos segura.")

        elif user['area'] == "Siembra":
            st.subheader("Nueva Siembra")
            with st.form("form_siembra"):
                c1, c2, c3 = st.columns(3)
                with c1: cultivo = st.selectbox("Cultivo", PRODUCTOS); bandejas = st.number_input("N° Bandejas", min_value=1, step=1)
                with c2: semilla = st.number_input("Semilla usada (g)", min_value=1.0, step=1.0); sustrato = st.number_input("Sustrato usado (g)", min_value=0.0, step=1.0)
                with c3: fecha = st.date_input("Fecha de Siembra", date.today())
                if st.form_submit_button("Registrar Siembra"):
                    add_data("siembra_final", (cultivo, bandejas, semilla, sustrato, fecha.strftime("%Y-%m-%d")))
                    st.success("Siembra registrada.")

        elif user['area'] == "Tienda":
            st.subheader("Punto de Venta y Costos")
            tab_v, tab_c, tab_p = st.tabs(["Registrar Venta", "Registrar Costo", "Registrar Pérdida"])
            with tab_v:
                with st.form("form_ventas"):
                    c1, c2, c3 = st.columns(3)
                    with c1: prod = st.selectbox("Producto", PRODUCTOS)
                    with c2: cant = st.number_input("Cantidad vendida", min_value=1, step=1)
                    with c3: precio = st.number_input("Monto Total (S/.)", min_value=0.0, step=0.5)
                    if st.form_submit_button("Registrar Venta"): add_data("finanzas_final", ("Venta", prod, cant, precio, date.today().strftime("%Y-%m-%d"))); st.success("Venta registrada.")
            with tab_c:
                with st.form("form_costos"):
                    c1, c2, c3 = st.columns(3)
                    with c1: concepto = st.text_input("Concepto (Ej: Semilla, Sustrato, Luz)")
                    with c2: cant = st.number_input("Cantidad", min_value=1, step=1)
                    with c3: precio = st.number_input("Monto Total (S/.)", min_value=0.0, step=0.5)
                    if st.form_submit_button("Registrar Costo"): add_data("finanzas_final", ("Costo", concepto, cant, precio, date.today().strftime("%Y-%m-%d"))); st.success("Costo registrada.")
            with tab_p:
                with st.form("form_perdidas"):
                    c1, c2, c3 = st.columns(3)
                    with c1: prod = st.selectbox("Producto Perdido", PRODUCTOS)
                    with c2: cant = st.number_input("Cantidad Perdida", min_value=1, step=1)
                    with c3: precio = st.number_input("Costo de Pérdida (S/.)", min_value=0.0, step=0.5)
                    if st.form_submit_button("Registrar Pérdida"): add_data("finanzas_final", ("Perdida", prod, cant, precio, date.today().strftime("%Y-%m-%d"))); st.success("Pérdida registrada.")

    elif user["rol"] == "jefe":
        st.title("Dashboard Privado - GEA ERP")
        st.markdown("#### Selección de Módulo")
        menu = st.selectbox("Navegación", ["Producción (Microgreens)", "Siembra", "Tienda y Finanzas", "Seguridad"])
        
        # Lógica de Carpetas Mensuales
        def filtro_meses(df, fecha_col='fecha'):
            if df.empty: return df
            df[fecha_col] = pd.to_datetime(df[fecha_col])
            df['mes_num'] = df[fecha_col].dt.strftime('%Y-%m')
            meses_unicos = sorted(df['mes_num'].unique())
            meses_formateados = [f"{MESES_NOMBRES.get(m.split('-')[1], m.split('-')[1])} {m.split('-')[0]}" for m in meses_unicos]
            mapa_meses = dict(zip(meses_formateados, meses_unicos))
            st.markdown("##### Carpetas Mensuales")
            mes_sel_txt = st.selectbox("Seleccione el período a analizar:", ["Ver Todo el Año"] + meses_formateados)
            if mes_sel_txt != "Ver Todo el Año":
                return df[df['mes_num'] == mapa_meses[mes_sel_txt]]
            return df

        if menu == "Producción (Microgreens)":
            st.markdown("##### Carga Masiva de Datos Históricos")
            uploaded_file = st.file_uploader("Suba el archivo Excel para procesar los datos.", type=['xlsx', 'xls'], key="excel_jefe")
            if uploaded_file is not None:
                try:
                    df_excel = pd.read_excel(uploaded_file, sheet_name='Hoja2')
                    df_excel.columns = df_excel.columns.str.strip()
                    registros_cargados = 0
                    for index, row in df_excel.iterrows():
                        prod = str(row.get('Identificación de Producto', '')).strip()
                        if prod == 'nan' or prod == '': continue
                        def parse_date(d):
                            try: return pd.to_datetime(d).strftime('%Y-%m-%d')
                            except: return date.today().strftime('%Y-%m-%d')
                        def map_state(s):
                            s = str(s)
                            if '✔' in s: return 'Optimo'
                            if '±' in s: return 'Regular'
                            if '✗' in s: return 'Deficiente'
                            return 'Optimo'
                        def safe_num(val, is_int=False):
                            try: val = float(val); return int(val) if is_int else val
                            except: return 0
                        merma_val = row.get('Merma')
                        merma = 100.0 if str(merma_val).strip().lower() == 'desechada' else safe_num(merma_val)
                        add_data("produccion_final", (prod, str(row.get('Numero de bandeja/Lote', '')).strip(), str(row.get('Tipo de bandeja', '')).strip(), parse_date(row.get('Fecha de siembra')), parse_date(row.get('Fecha de transición a la luz')), map_state(row.get('Estado del cultivo de transicion a la luz')), parse_date(row.get('Fecha de cosecha')), map_state(row.get('Estado del cultivo en cosecha')), safe_num(row.get('Peso bruto')), safe_num(row.get('Cantidad de tapers'), is_int=True), str(row.get('Taper usado para envasado', '')).strip(), safe_num(row.get('Peso sobrante/ Remanente')), merma, "Microgreens"))
                        registros_cargados += 1
                    if registros_cargados > 0: st.success(f"Proceso completado. Se han cargado {registros_cargados} registros al sistema.")
                except Exception as e: st.error(f"Error al procesar el archivo. Detalle: {e}")

            st.markdown("---")
            df = get_data("produccion_final")
            if df.empty:
                st.info("Sin datos de producción. Suba un Excel o genere datos de demostración.")
                if st.button("Generar Datos de Demostración (Junio y Julio)"): cargar_datos_demo(); st.rerun()
            else:
                df = filtro_meses(df, 'fecha_cosecha')
                c1, c2, c3 = st.columns(3)
                c1.metric("Lotes Cosechados", len(df))
                c2.metric("Tapers Totales", df['cantidad_tapers'].sum())
                c3.metric("Merma Total (g)", f"{df['merma'].sum():.1f}")
                
                st.markdown("---")
                st.subheader("Gráfico de Producción")
                df_time = df.groupby('fecha_cosecha').agg({'cantidad_tapers':'sum', 'merma':'sum'}).reset_index()
                df_time['fecha_str'] = df_time['fecha_cosecha'].dt.strftime('%d-%m')
                chart_tapers = alt.Chart(df_time).mark_area(color="#4CAF50", opacity=0.5).encode(x=alt.X('fecha_str:O', title='Fecha', sort=df_time['fecha_str'].tolist()), y=alt.Y('cantidad_tapers:Q', title='Tapers'))
                chart_merma = alt.Chart(df_time).mark_line(color="#C62828", point=True, strokeWidth=2).encode(x=alt.X('fecha_str:O', sort=df_time['fecha_str'].tolist()), y=alt.Y('merma:Q', title='Merma (g)'))
                st.altair_chart(alt.layer(chart_tapers, chart_merma).resolve_scale(y='independent').properties(height=400), use_container_width=True)
                st.caption("Interpretación: Los picos verdes muestran días de alta producción. Si coinciden con picos rojos, indica alto desperdicio.")

                st.markdown("---")
                st.subheader("Diagrama de Pareto de Merma")
                df_pareto = df.groupby('producto')['merma'].sum().reset_index().sort_values(by='merma', ascending=False)
                df_pareto['cumulative'] = df_pareto['merma'].cumsum() / df_pareto['merma'].sum() * 100
                base = alt.Chart(df_pareto).encode(x=alt.X('producto:N', sort=df_pareto['producto'].tolist(), title='Cultivo'))
                bars = base.mark_bar(color="#C62828").encode(y=alt.Y('merma:Q', title='Merma (g)'))
                line = base.mark_line(color='#FF9800', point=True, strokeWidth=2).encode(y=alt.Y('cumulative:Q', title='Acumulado (%)'))
                st.altair_chart(alt.layer(bars, line).resolve_scale(y='independent').properties(height=350), use_container_width=True)
                st.caption("Interpretación: Enfóquese en los cultivos antes de que la línea naranja cruce el 80%. Representan la mayoría de las pérdidas.")

                st.markdown("---")
                c_a, c_b = st.columns(2)
                with c_a:
                    st.subheader("Merma por Estado")
                    st.altair_chart(alt.Chart(df).mark_bar(color="#C62828").encode(x='estado_cosecha:N', y='sum(merma):Q').properties(height=300), use_container_width=True)
                    st.caption("Interpretación: Un lote deficiente genera hasta 4 veces más pérdida que uno óptimo.")
                with c_b:
                    st.subheader("Producción por Cultivo")
                    st.altair_chart(alt.Chart(df).mark_bar().encode(y='producto:N', x='sum(cantidad_tapers):Q', color='producto:N').properties(height=300), use_container_width=True)
                    st.caption("Interpretación: Alto volumen no equivale a alta eficiencia. Cruce estos datos con el Pareto.")

                st.markdown("---")
                st.subheader("Asistente de Análisis IA (Consultor Experto)")
                for msg in st.session_state.chat_history:
                    if msg['role'] == 'user': st.info(f"**Usuario:** {msg['content']}")
                    else: st.success(msg['content'])
                pregunta = st.text_input("Realice su consulta a la IA:", placeholder="Ej: ¿Cómo mejoramos la eficiencia este mes?")
                if st.button("Generar Informe IA"):
                    if pregunta:
                        st.session_state.chat_history.append({"role": "user", "content": pregunta})
                        p = pregunta.lower()
                        resp = f"**INFORME DE INTELIGENCIA OPERATIVA**\n\n**1. Resumen:**\nSe procesaron {len(df)} lotes, generando {df['cantidad_tapers'].sum()} tapers. Merma total: {df['merma'].sum():.1f}g.\n\n"
                        if any(w in p for w in ['pareto', 'mejora', 'eficiencia']):
                            resp += "**2. Diagnóstico:**\nEnfocar esfuerzos en los cultivos con mayor merma acumulada.\n\n**3. Plan de Acción:**\n- Estandarizar pesaje de sustrato.\n- Alertas visuales para lotes 'Regulares'.\n- Replicar protocolo de lotes 'Óptimos'."
                        else:
                            resp += "**2. Recomendación:**\nUtilice el Diagrama de Pareto para identificar focos de pérdida."
                        st.session_state.chat_history.append({"role": "bot", "content": resp})
                        st.rerun()

                st.markdown("---")
                st.subheader("Registro Detallado")
                st.dataframe(df.sort_values(by='id', ascending=False), use_container_width=True)

        elif menu == "Siembra":
            st.subheader("Control de Siembras")
            df = get_data("siembra_final")
            if df.empty: st.warning("No se han registrado siembras.")
            else:
                df = filtro_meses(df, 'fecha')
                c1, c2 = st.columns(2)
                c1.metric("Total Bandejas", df['bandejas'].sum())
                c2.metric("Total Semilla (g)", f"{df['semilla_g'].sum():.1f}")
                st.markdown("---")
                st.dataframe(df.sort_values(by='id', ascending=False), use_container_width=True)
                st.subheader("Uso de Insumos por Cultivo")
                chart_data = df.groupby('cultivo').agg({'semilla_g':'sum', 'sustrato_g':'sum'}).reset_index().melt(id_vars=['cultivo'])
                st.altair_chart(alt.Chart(chart_data).mark_bar().encode(x='cultivo:N', y='value:Q', color='variable:N'), use_container_width=True)
                st.caption("Interpretación: Muestra qué cultivos consumen más semilla y sustrato. Útil para controlar costos de insumos.")

        elif menu == "Tienda y Finanzas":
            st.subheader("Resumen Financiero")
            df = get_data("finanzas_final")
            if df.empty: st.warning("No hay datos financieros.")
            else:
                df = filtro_meses(df, 'fecha')
                
                ventas = df[df['tipo']=='Venta']['monto'].sum()
                costos = df[df['tipo']=='Costo']['monto'].sum()
                perdidas = df[df['tipo']=='Perdida']['monto'].sum()
                ganancias = ventas - costos - perdidas
                
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Ingresos (Ventas)", f"S/. {ventas:.2f}")
                c2.metric("Costos Operativos", f"S/. {costos:.2f}")
                c3.metric("Pérdidas", f"S/. {perdidas:.2f}")
                c4.metric("Ganancia Neta", f"S/. {ganancias:.2f}")
                
                st.markdown("---")
                st.subheader("Distribución Financiera")
                chart_data = pd.DataFrame({'Tipo': ['Ventas', 'Costos', 'Pérdidas'], 'Monto': [ventas, costos, perdidas]})
                st.altair_chart(alt.Chart(chart_data).mark_bar().encode(x='Tipo:N', y='Monto:Q', color='Tipo:N'), use_container_width=True)
                st.caption("Interpretación: La barra de Ventas debe superar siempre la suma de Costos y Pérdidas para asegurar rentabilidad.")
                
                st.markdown("---")
                st.subheader("Registro Detallado de Movimientos")
                st.dataframe(df.sort_values(by='id', ascending=False), use_container_width=True)

        elif menu == "Seguridad":
            st.subheader("Cambio de Credenciales (Solo Director)")
            nuevo_pin = st.text_input("Ingrese nuevo Código Maestro", type="password")
            if st.button("Actualizar Código Maestro"):
                if len(nuevo_pin) >= 6: set_config('pin_jefe', nuevo_pin); st.success("Código actualizado con éxito.")
                else: st.error("El código debe tener al menos 6 caracteres.")
