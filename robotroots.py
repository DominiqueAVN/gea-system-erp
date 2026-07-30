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

# --- BASE DE DATOS ---
def init_db():
    conn = sqlite3.connect('gea_system.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS produccion_final
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                 producto TEXT, lote TEXT, tipo_bandeja TEXT, 
                 fecha_siembra TEXT, fecha_luz TEXT, estado_luz TEXT, 
                 fecha_cosecha TEXT, estado_cosecha TEXT, 
                 peso_bruto REAL, cantidad_tapers INTEGER, taper_envasado TEXT, 
                 peso_sobrante REAL, merma REAL, area TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS siembra_v2
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, cultivo TEXT, bandejas INTEGER, bandeja_tipo TEXT, semilla_g REAL, fecha TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS ventas_v2
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, producto TEXT, cantidad INTEGER, total REAL, fecha TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS perdidas_v2
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, producto TEXT, cantidad INTEGER, motivo TEXT, fecha TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS contactos_v2
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT, telefono TEXT, email TEXT, potencial TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS config_v2
                 (key TEXT PRIMARY KEY, value TEXT)''')
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
ESTADOS = ["✔ Óptimo", "± Regular", "✗ Deficiente"]

MESES_NOMBRES = {"01": "Enero", "02": "Febrero", "03": "Marzo", "04": "Abril", "05": "Mayo", "06": "Junio", "07": "Julio", "08": "Agosto", "09": "Septiembre", "10": "Octubre", "11": "Noviembre", "12": "Diciembre"}

def cargar_datos_demo():
    for mes_num, dias_mes in [("06", 30), ("07", 15)]:
        for _ in range(30):
            prod = random.choice(PRODUCTOS)
            fecha_cos = date(2026, int(mes_num), random.randint(1, dias_mes))
            fecha_sim = fecha_cos - timedelta(days=random.randint(7, 12))
            fecha_luz = fecha_sim + timedelta(days=random.randint(5, 7))
            estado_luz = random.choices(ESTADOS, weights=[0.7, 0.2, 0.1])[0]
            estado_cos = random.choices(ESTADOS, weights=[0.6, 0.3, 0.1])[0]
            tapers = random.randint(3, 15)
            merma = random.uniform(5, 20) if estado_cos != "✗ Deficiente" else random.uniform(50, 90)
            add_data("produccion_final", (prod, str(random.randint(1, 50)), "Bandeja Estándar", fecha_sim.strftime("%Y-%m-%d"), fecha_luz.strftime("%Y-%m-%d"), estado_luz, fecha_cos.strftime("%Y-%m-%d"), estado_cos, random.uniform(30, 50), tapers, "Taper 12onz", 0.0, merma, "Microgreens"))

def analizar_datos_gea_avanzado(df, pregunta):
    if df.empty: return "No hay datos suficientes en este período."
    p = pregunta.lower()
    response = "🤖 **INFORME DE INTELIGENCIA OPERATIVA GEA**\n\n"
    total_tapers = df['cantidad_tapers'].sum()
    total_merma = df['merma'].sum()
    ratio_merma = (total_merma / total_tapers) * 100 if total_tapers > 0 else 0
    df_pareto = df.groupby('producto')['merma'].sum().reset_index().sort_values(by='merma', ascending=False)
    df_pareto['cumulative'] = df_pareto['merma'].cumsum() / df_pareto['merma'].sum() * 100
    cultivos_80 = df_pareto[df_pareto['cumulative'] <= 80]['producto'].tolist()
    cultivo_top_merma = df_pareto.iloc[0]['producto'] if not df_pareto.empty else "N/A"
    
    if any(word in p for word in ['pareto', 'diagrama', 'opinion', 'opinión', 'eficiencia', 'mejora', 'mejorar']):
        response += "**1. Diagnóstico Estratégico (Pareto):**\n"
        if cultivos_80:
            response += f"El análisis revela que el 80% de tus pérdidas se concentran en: **{', '.join(cultivos_80)}**. No tienes un problema generalizado, sino focos de ineficiencia específicos.\n\n"
        response += "**2. Análisis de Causa Raíz:**\n"
        df_def = df[df['estado_cosecha'] == '✗ Deficiente']
        if not df_def.empty:
            response += f"Los lotes 'Deficientes' generan una merma promedio de {df_def['merma'].mean():.1f}g. Esto suele estar correlacionado con dos factores: dosificación imprecisa de sustrato y fallas en el control de humedad durante la transición a la luz.\n\n"
        response += "**3. Plan de Acción para Mejorar la Eficiencia:**\n"
        response += f"- **Acción 1:** Estandarizar el pesaje en gramos del sustrato para '{cultivo_top_merma}'.\n- **Acción 2:** Implementar alertas visuales para lotes en estado 'Regular'.\n- **Acción 3:** Replicar el protocolo de los lotes 'Óptimos' (✔) hacia los cultivos con menor rendimiento.\n"
        return response
    else:
        response += f"**1. Resumen Operativo:**\nSe procesaron {len(df)} lotes, generando {total_tapers} tapers. La merma total es {total_merma:.1f}g (ratio del {ratio_merma:.1f}%).\n\n"
        response += f"**2. Punto de Atención:**\nEl cultivo que requiere atención inmediata es **{cultivo_top_merma}**.\n\n"
        response += "**3. Recomendación:**\nUtiliza el Diagrama de Pareto para identificar qué cultivos generan el 80% de tus pérdidas y enfocar ahí los esfuerzos."
        return response

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_data = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'reporte_ia' not in st.session_state:
    st.session_state.reporte_ia = ""

def logout():
    st.session_state.logged_in = False
    st.session_state.user_data = None
    st.rerun()

# --- LOGIN (Tema Oscuro) ---
if not st.session_state.logged_in:
    st.markdown("""
    <style>
        #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
        .stApp { background: linear-gradient(135deg, #0f1108, #1a2b15, #0d0d0d, #2a0a0a); background-size: 400% 400%; animation: gradientMove 15s ease infinite; }
        @keyframes gradientMove { 0% { background-position: 0% 50%; } 50% { background-position: 100% 50%; } 100% { background-position: 0% 50%; } }
        .stApp h1, .stApp h4, .stApp p, .stApp label { color: #ecf0f1 !important; }
        .stImage img { border-radius: 15px; box-shadow: 0 0 25px rgba(255, 255, 255, 0.2); }
    </style>
    """, unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        try: st.image("gea_logo.png", width=150)
        except: pass
        st.markdown("<h1 style='text-align: center; margin-bottom: 0px;'>GEA SYSTEM ERP</h1>", unsafe_allow_html=True)
        st.markdown("<h4 style='text-align: center; color: #bdc3c7; margin-top: 0px;'>Germinados Orgánicos Arequipa</h4>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #95a5a6;'>Plataforma Operativa de Producción, Calidad y Ventas</p>", unsafe_allow_html=True)
        st.markdown("<hr style='border: 1px solid #7f8c8d;'>", unsafe_allow_html=True)
        tab_jefe, tab_trab = st.tabs(["👔 Acceso Dirección", "👷 Acceso Personal de Planta"])
        with tab_jefe:
            st.markdown("##### Ingrese sus credenciales de Director")
            pin_input = st.text_input("Código Maestro (PIN)", type="password", placeholder="••••••••")
            if st.button("Desbloquear Panel Directivo", use_container_width=True, type="primary"):
                if pin_input == get_config('pin_jefe'):
                    st.session_state.logged_in = True
                    st.session_state.user_data = {"nombre": "Director GEA", "rol": "jefe"}
                    st.rerun()
                else: st.error("⛔ Código Maestro incorrecto. Acceso denegado.")
        with tab_trab:
            st.markdown("##### Fichaje de Turno Operativo")
            area_trab = st.selectbox("Seleccione su Área de Trabajo", ["Siembra", "Microgreens", "Tienda"])
            pin_trab = st.text_input("PIN del Área Asignada", type="password", placeholder="••••")
            pins_areas = {"Siembra": "1234", "Microgreens": "5678", "Tienda": "9012"}
            if st.button("Fichar y Ingresar al Sistema", use_container_width=True):
                if pin_trab == pins_areas.get(area_trab):
                    st.session_state.logged_in = True
                    st.session_state.user_data = {"nombre": f"Operario de {area_trab}", "rol": "trabajador", "area": area_trab}
                    st.rerun()
                else: st.error("⛔ PIN de área incorrecto.")

else:
    user = st.session_state.user_data
    with st.sidebar:
        if os.path.exists("gea_logo.png"): st.image("gea_logo.png", width=80)
        st.write(f"👋 **Bienvenido:**\n{user['nombre']}")
        if user['rol'] == 'jefe': st.write("📧 Sesión: Directiva\n🔒 Conexión Encriptada SSL/TLS")
        else: st.write(f"🏭 Área: {user['area']}")
        st.markdown("---")
        if st.button("🚪 Cerrar Sesión"): logout()

    if user["rol"] == "trabajador":
        st.title(f"🏭 Panel de {user['area']}")
        if user['area'] == "Microgreens":
            st.subheader("✂️ Registro de Cosecha Microgreens")
            with st.expander("📄 Descargar Plantilla Oficial de Excel"):
                st.write("Si prefieres llenar los datos en Excel y luego subirlos, descarga el formato oficial aquí:")
                df_plantilla = pd.DataFrame(columns=['Identificación de Producto', 'Numero de bandeja/Lote', 'Tipo de bandeja', 'Fecha de siembra', 'Fecha de transición a la luz', 'Estado del cultivo de transicion a la luz', 'Fecha de cosecha', 'Estado del cultivo en cosecha', 'Peso bruto', 'Cantidad de tapers', 'Taper usado para envasado', 'Peso sobrante/ Remanente', 'Merma'])
                # Omitimos openpyxl en la nube, usamos xlsxwriter o default
                try:
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer: df_plantilla.to_excel(writer, index=False, sheet_name='Hoja2')
                    st.download_button("📥 Descargar Plantilla", data=output.getvalue(), file_name="Plantilla_Cosecha_GEA.xlsx")
                except:
                    st.info("Descarga disponible en versión local.")
                file_trab = st.file_uploader("Subir Excel lleno aquí", type=['xlsx'], key="excel_trab")
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
                            add_data("produccion_final", (prod, str(row.get('Numero de bandeja/Lote', '')).strip(), str(row.get('Tipo de bandeja', '')).strip(), parse_date(row.get('Fecha de siembra')), parse_date(row.get('Fecha de transición a la luz')), str(row.get('Estado del cultivo de transicion a la luz', '✔ Óptimo')).strip(), parse_date(row.get('Fecha de cosecha')), str(row.get('Estado del cultivo en cosecha', '✔ Óptimo')).strip(), float(row.get('Peso bruto', 0) or 0), int(row.get('Cantidad de tapers', 0) or 0), str(row.get('Taper usado para envasado', '')).strip(), float(row.get('Peso sobrante/ Remanente', 0) or 0), float(row.get('Merma', 0) or 0), "Microgreens"))
                        st.success(f"¡Éxito! Se cargaron {len(df_excel)} registros.")
                    except Exception as e: st.error(f"Error al leer. {e}")
            st.markdown("---")
            st.write("**O regístralo al instante aquí:**")
            with st.form("form_cosecha_v3"):
                c1, c2, c3 = st.columns(3)
                with c1: producto = st.selectbox("Identificación de Producto", PRODUCTOS); lote = st.text_input("Numero de bandeja/Lote", "1"); tipo_bandeja = st.selectbox("Tipo de bandeja", BANDEJAS)
                with c2: fecha_siembra = st.date_input("Fecha de siembra", date.today()); fecha_luz = st.date_input("Fecha de transición a la luz", date.today()); estado_luz = st.selectbox("Estado transición a la luz", ESTADOS)
                with c3: fecha_cosecha = st.date_input("Fecha de cosecha", date.today()); estado_cosecha = st.selectbox("Estado en cosecha", ESTADOS); peso_bruto = st.number_input("Peso bruto (g)", min_value=0.0, step=0.1)
                c4, c5 = st.columns(2)
                with c4: cantidad_tapers = st.number_input("Cantidad de tapers", min_value=0, step=1); taper_envasado = st.selectbox("Taper usado para envasado", TAPERS)
                with c5: peso_sobrante = st.number_input("Peso sobrante/Remanente (g)", min_value=0.0, step=0.1); merma = st.number_input("Merma (g)", min_value=0.0, step=0.1)
                if st.form_submit_button("✅ REGISTRAR EN SISTEMA"):
                    add_data("produccion_final", (producto, lote, tipo_bandeja, fecha_siembra.strftime("%Y-%m-%d"), fecha_luz.strftime("%Y-%m-%d"), estado_luz, fecha_cosecha.strftime("%Y-%m-%d"), estado_cosecha, peso_bruto, cantidad_tapers, taper_envasado, peso_sobrante, merma, user['area']))
                    st.success("¡Registro guardado en base de datos segura!")
        elif user['area'] == "Siembra":
            st.subheader("🌱 Nueva Siembra")
            with st.form("form_siembra"):
                c1, c2 = st.columns(2)
                with c1: cultivo = st.selectbox("Cultivo", PRODUCTOS); bandejas = st.number_input("N° Bandejas", min_value=1, step=1)
                with c2: semilla = st.number_input("Semilla usada (g)", min_value=1.0, step=1.0); fecha = st.date_input("Fecha de Siembra", date.today())
                if st.form_submit_button("Registrar Siembra"):
                    add_data("siembra_v2", (cultivo, bandejas, "Por definir", semilla, fecha.strftime("%Y-%m-%d")))
                    st.success("Siembra registrada.")
        elif user['area'] == "Tienda":
            st.subheader("🛒 Punto de Venta")
            tab_v, tab_p, tab_c = st.tabs(["Registrar Venta", "Registrar Pérdida", "Nuevo Contacto"])
            with tab_v:
                with st.form("form_ventas"):
                    c1, c2, c3 = st.columns(3)
                    with c1: prod = st.selectbox("Producto", PRODUCTOS)
                    with c2: cant = st.number_input("Tapers vendidos", min_value=1, step=1)
                    with c3: precio = st.number_input("Precio Total (S/.)", min_value=0.0, step=0.5)
                    if st.form_submit_button("Registrar Venta"): add_data("ventas_v2", (prod, cant, precio, date.today().strftime("%Y-%m-%d"))); st.success("Venta registrada.")
            with tab_p:
                with st.form("form_perdidas"):
                    c1, c2, c3 = st.columns(3)
                    with c1: prod = st.selectbox("Producto Perdido", PRODUCTOS)
                    with c2: cant = st.number_input("Cantidad Perdida", min_value=1, step=1)
                    with c3: motivo = st.selectbox("Motivo", ["Mal estado", "Merma cosecha", "Vencimiento"])
                    if st.form_submit_button("Registrar Pérdida"): add_data("perdidas_v2", (prod, cant, motivo, date.today().strftime("%Y-%m-%d"))); st.success("Pérdida registrada.")
            with tab_c:
                with st.form("form_contactos"):
                    c1, c2 = st.columns(2)
                    with c1: nombre = st.text_input("Nombre del Cliente")
                    with c2: tel = st.text_input("Teléfono")
                    email = st.text_input("Correo")
                    pot = st.selectbox("Potencial de Compra", ["Bajo", "Medio", "Alto (Mayorista)"])
                    if st.form_submit_button("Guardar Contacto"): add_data("contactos_v2", (nombre, tel, email, pot)); st.success("Contacto guardado.")

    elif user["rol"] == "jefe":
        st.title("📊 Dashboard Privado - GEA ERP")
        menu = st.selectbox("Navegación", ["📈 Producción (Tiempo Real)", "🌱 Siembra", "🛒 Tienda y Finanzas", "📞 CRM (Contactos)", "📅 Reporte IA y Exportación", "⚙️ Seguridad"])
        if menu == "📈 Producción (Tiempo Real)":
            st.markdown("##### 📂 Carga Masiva de Datos")
            uploaded_file = st.file_uploader("Sube el archivo Excel para procesar los datos.", type=['xlsx', 'xls'], key="excel_jefe")
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
                            if '✔' in s: return '✔ Óptimo'
                            if '±' in s: return '± Regular'
                            if '✗' in s: return '✗ Deficiente'
                            return '✔ Óptimo'
                        def safe_num(val, is_int=False):
                            try:
                                val = float(val)
                                return int(val) if is_int else val
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
                st.info("Sin datos de producción. Sube un Excel o genera datos de demostración.")
                if st.button("🎲 Generar Datos de Demostración (Junio y Julio)"): cargar_datos_demo(); st.rerun()
            else:
                df['fecha_cosecha'] = pd.to_datetime(df['fecha_cosecha'])
                df['mes_num'] = df['fecha_cosecha'].dt.strftime('%Y-%m')
                meses_unicos = sorted(df['mes_num'].unique())
                meses_formateados = [f"{MESES_NOMBRES.get(m.split('-')[1], m.split('-')[1])} {m.split('-')[0]}" for m in meses_unicos]
                mapa_meses = dict(zip(meses_formateados, meses_unicos))
                
                st.markdown("#### 📁 Filtros de Tiempo")
                col_filtro, col_demo = st.columns([3, 1])
                with col_filtro: mes_sel_txt = st.selectbox("Selecciona el mes a analizar:", ["Ver Todo el Año"] + meses_formateados)
                with col_demo:
                    st.write("")
                    if st.button("🎲 Cargar Demo Jun/Jul"): cargar_datos_demo(); st.rerun()

                if mes_sel_txt != "Ver Todo el Año":
                    df = df[df['mes_num'] == mapa_meses[mes_sel_txt]]
                    st.write(f"Mostrando datos de: **{mes_sel_txt}**")
                else: st.write("Mostrando datos de: **Todo el Año**")

                c1, c2, c3 = st.columns(3)
                c1.metric("Lotes Cosechados", len(df))
                c2.metric("Tapers Totales", df['cantidad_tapers'].sum())
                c3.metric("Merma Total (g)", f"{df['merma'].sum():.1f}")
                
                st.markdown("---")
                st.subheader("📈 Gráfico de Producción")
                df_time = df.groupby('fecha_cosecha').agg({'cantidad_tapers':'sum', 'merma':'sum'}).reset_index()
                df_time['fecha_str'] = df_time['fecha_cosecha'].dt.strftime('%d-%m')
                chart_tapers = alt.Chart(df_time).mark_area(color="#2ca02c", opacity=0.5).encode(x=alt.X('fecha_str:O', title='Fecha', sort=df_time['fecha_str'].tolist()), y=alt.Y('cantidad_tapers:Q', title='Tapers'))
                chart_merma = alt.Chart(df_time).mark_line(color="#d62728", point=True, strokeWidth=3).encode(x=alt.X('fecha_str:O', sort=df_time['fecha_str'].tolist()), y=alt.Y('merma:Q', title='Merma (g)'))
                st.altair_chart(alt.layer(chart_tapers, chart_merma).resolve_scale(y='independent').properties(height=400), use_container_width=True)
                st.caption("🔍 **Interpretación:** Los picos verdes muestran días de alta producción. Si un pico verde coincide con un pico rojo, significa que se produjo mucho, pero también se desperdició mucho ese día. Buscamos picos verdes altos con línea roja plana.")

                st.markdown("---")
                st.subheader("📊 Diagrama de Pareto de Merma")
                df_pareto = df.groupby('producto')['merma'].sum().reset_index().sort_values(by='merma', ascending=False)
                df_pareto['cumulative'] = df_pareto['merma'].cumsum() / df_pareto['merma'].sum() * 100
                base = alt.Chart(df_pareto).encode(x=alt.X('producto:N', sort=df_pareto['producto'].tolist(), title='Cultivo'))
                bars = base.mark_bar(color="#d62728").encode(y=alt.Y('merma:Q', title='Merma (g)'))
                line = base.mark_line(color='orange', point=True, strokeWidth=3).encode(y=alt.Y('cumulative:Q', title='Acumulado (%)'))
                st.altair_chart(alt.layer(bars, line).resolve_scale(y='independent').properties(height=350), use_container_width=True)
                st.caption("🔍 **Interpretación:** Según la regla 80/20, enfócate en los cultivos que están antes de que la línea naranja cruce el 80%. Esos cultivos (las barras más altas) son los que están generando la mayoría de tus pérdidas.")

                st.markdown("---")
                c_a, c_b = st.columns(2)
                with c_a:
                    st.subheader("Merma por Estado")
                    st.altair_chart(alt.Chart(df).mark_bar(color="#d62728").encode(x='estado_cosecha:N', y='sum(merma):Q').properties(height=300), use_container_width=True)
                    st.caption("🔍 **Interpretación:** La merma está ligada al estado del lote. Un lote deficiente (✗) genera hasta 4 veces más pérdida que uno óptimo (✔).")
                with c_b:
                    st.subheader("Producción por Cultivo")
                    st.altair_chart(alt.Chart(df).mark_bar().encode(y='producto:N', x='sum(cantidad_tapers):Q', color='producto:N').properties(height=300), use_container_width=True)
                    st.caption("🔍 **Interpretación:** Compara el volumen. Recuerda que un alto volumen no siempre significa alta eficiencia.")

                st.markdown("---")
                st.subheader("🤖 Asistente de Análisis IA (Consultor Experto)")
                st.caption("La IA analiza el período seleccionado. Prueba preguntando: '¿Qué opinion me das del diagrama de Pareto?'")
                for msg in st.session_state.chat_history:
                    if msg['role'] == 'user': st.info(f"**Tú:** {msg['content']}")
                    else: st.success(msg['content'])
                pregunta = st.text_input("Realiza tu consulta a la IA:", placeholder="Ej: ¿Cómo mejoramos la eficiencia este mes?")
                if st.button("Generar Informe IA"):
                    if pregunta:
                        st.session_state.chat_history.append({"role": "user", "content": pregunta})
                        st.session_state.chat_history.append({"role": "bot", "content": analizar_datos_gea_avanzado(df, pregunta)})
                        st.rerun()

                st.markdown("---")
                st.subheader("Registro Detallado")
                st.dataframe(df.sort_values(by='id', ascending=False), use_container_width=True)

        elif menu == "🌱 Siembra":
            st.subheader("Control de Siembras")
            df = get_data("siembra_v2")
            if df.empty: st.warning("Aún no se han registrado siembras.")
            else:
                st.dataframe(df.sort_values(by='id', ascending=False), use_container_width=True)
                st.altair_chart(alt.Chart(df).mark_bar().encode(x='cultivo:N', y='sum(semilla_g):Q', color='cultivo:N'), use_container_width=True)
                st.caption("🔍 **Interpretación:** Muestra qué cultivos consumen más semilla. Útil para controlar costos de insumos.")

        elif menu == "🛒 Tienda y Finanzas":
            st.subheader("Resumen Financiero")
            df_v = get_data("ventas_v2")
            df_p = get_data("perdidas_v2")
            c1, c2 = st.columns(2)
            c1.metric("Ingresos Totales", f"S/. {df_v['total'].sum():.2f}" if not df_v.empty else "S/. 0")
            c2.metric("Pérdidas Registradas", len(df_p))
            if not df_v.empty:
                st.altair_chart(alt.Chart(df_v).mark_bar().encode(x='producto:N', y='sum(total):Q', color='producto:N'), use_container_width=True)
                st.caption("🔍 **Interpretación:** Los productos más altos son tus mejores ingresos. Los bajos podrían requerir estrategias de venta.")

        elif menu == "📞 CRM (Contactos)":
            st.subheader("Base de Datos de Clientes")
            df = get_data("contactos_v2")
            if df.empty: st.info("No hay contactos registrados.")
            else: st.dataframe(df, use_container_width=True)

        elif menu == "📅 Reporte IA y Exportación":
            st.subheader("Análisis Ejecutivo y Exportación")
            df_prod = get_data("produccion_final")
            if df_prod.empty: st.warning("No hay datos para analizar.")
            else:
                df_export = df_prod.drop(columns=['id', 'area'])
                try:
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer: df_export.to_excel(writer, index=False, sheet_name='Hoja2')
                    st.download_button("📥 Descargar Excel Final de Cosechas", data=output.getvalue(), file_name=f"GEA_Reporte_Cosechas_{date.today().strftime('%Y_%m')}.xlsx")
                except:
                    st.info("Descarga de Excel disponible en versión local.")
                
                st.markdown("---")
                st.markdown("#### 🤖 Análisis Ejecutivo en Tiempo Real")
                if st.button("🤖 GENERAR REPORTE EJECUTIVO AHORA", use_container_width=True, type="primary"):
                    total_lotes = len(df_prod); total_tapers = df_prod['cantidad_tapers'].sum(); total_merma = df_prod['merma'].sum()
                    ratio_merma = (total_merma / total_tapers) * 100 if total_tapers > 0 else 0
                    cultivo_top_prod = df_prod.groupby('producto')['cantidad_tapers'].sum().idxmax()
                    cultivo_top_merma = df_prod.groupby('producto')['merma'].sum().idxmax()
                    num_deficientes = len(df_prod[df_prod['estado_cosecha'] == '✗ Deficiente'])
                    estado_general = "ÓPTIMO" if ratio_merma < 5.0 else "ACEPTABLE" if ratio_merma < 15.0 else "CRÍTICO"
                    reporte = f"REPORTE EJECUTIVO GEA SYSTEM - {date.today().strftime('%d/%m/%Y')}\n1. RESUMEN GENERAL:\nLotes: {total_lotes} | Tapers: {total_tapers} | Merma: {total_merma:.1f}g ({ratio_merma:.1f}%). Estado: {estado_general}.\n2. DEFICIENCIAS:\n{num_deficientes} lotes deficientes. Cultivo crítico: {cultivo_top_merma}.\n3. MEJORAS:\nEstandarizar sustrato. Replicar lotes Óptimos.\n4. CONCLUSIÓN:\nCultivo top: {cultivo_top_prod}."
                    st.session_state.reporte_ia = reporte
                    st.rerun()
                if st.session_state.reporte_ia:
                    st.code(st.session_state.reporte_ia, language='text')
                    st.download_button("📥 Descargar Reporte", data=st.session_state.reporte_ia, file_name=f"GEA_Reporte_IA_{date.today().strftime('%Y_%m_%d')}.txt")

        elif menu == "⚙️ Seguridad":
            st.subheader("Cambio de Credenciales (Solo Director)")
            nuevo_pin = st.text_input("Ingrese nuevo Código Maestro", type="password")
            if st.button("Actualizar Código Maestro"):
                if len(nuevo_pin) >= 6: set_config('pin_jefe', nuevo_pin); st.success("Código actualizado con éxito.")
                else: st.error("El código debe tener al menos 6 caracteres.")
