import streamlit as st
import pandas as pd

# 1. CONFIGURACIÓN ESTÉTICA INICIAL
st.set_page_config(page_title="Gestión de Pagos", page_icon="📈", layout="centered")

@st.cache_data
def cargar_datos():
    # Nota: Cambia a .read_excel('Datos_Pagos.xlsx', sheet_name='Pagos') en tu PC
    df = pd.read_excel('Datos_Pagos.xlsx', sheet_name='Pagos')
    df.columns = df.columns.str.strip()
    
    # Formateo de fecha_deuda (DD/MM/AAAA)
    if 'fecha_deuda' in df.columns:
        df['fecha_deuda'] = pd.to_datetime(df['fecha_deuda']).dt.strftime('%d/%m/%Y')
    
    # Limpieza financiera
    cols_num = ['pagos', 'cobros', 'deuda', 'Valor _Escritura']
    for col in cols_num:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    return df

try:
    df = cargar_datos()

    # --- CABECERA ---
    st.title("📑 Ficha de Cliente")
    
    if 'fecha_deuda' in df.columns:
        st.markdown(f"🗓️ **Información al:** {df['fecha_deuda'].iloc[0]}")
    
    st.divider()

    # --- FILTROS ---
    c1, c2 = st.columns(2)
    with c1:
        proy_sel = st.selectbox("📌 Proyecto", sorted(df['Proy'].unique()))
    df_f = df[df['Proy'] == proy_sel]
    with c2:
        lote_sel = st.selectbox("🏠 Lote", sorted(df_f['Lote'].unique()))

    # --- RESULTADOS ---
    res = df_f[df_f['Lote'] == lote_sel]

    if not res.empty:
        f = res.iloc[0]

        # A. INFORMACIÓN DEL CLIENTE (Antes del gráfico)
        st.subheader("👤 Datos del Propietario")
        with st.container(border=True):
            st.markdown(f"### {f['Nombre']}")
            st.markdown(f"**🆔 RUT:** {f['RUT']}")
            
            # Gestión de Teléfono y WhatsApp
            tel_raw = str(f['Telefono'])
            tel_clean = "".join(filter(str.isdigit, tel_raw))
            if tel_clean:
                st.markdown(f"**📞 Teléfono:** +{tel_clean}")
                ws_url = f"https://wa.me/{tel_clean}?text=Hola%20{f['Nombre']},%20le%20contacto%20por%20el%20lote%20{lote_sel}"
                st.link_button("💬 Enviar WhatsApp", ws_url, use_container_width=True)
            else:
                st.warning("Sin teléfono registrado")

        # B. RESUMEN FINANCIERO (Métricas)
        st.subheader("💰 Estado de Cuenta")
        m1, m2, m3 = st.columns(3)
        m1.metric("Cobros", f"${f['cobros']:,.0f}")
        m2.metric("Pagado", f"${f['pagos']:,.0f}")
        
        # Deuda y Modalidad
        color_deuda = "normal" if f['deuda'] <= 0 else "inverse"
        m3.metric("Deuda", f"${f['deuda']:,.0f}", delta=f"-{f['deuda']:,.0f}" if f['deuda'] > 0 else None, delta_color=color_deuda)
        
        st.info(f"**Modalidad de Pago:** {f['Modalidad']}")
        if f['Modalidad'] == 'T':
            st.success("Este cliente pagó el total del lote (Contado).")

        # C. GRÁFICO COMPARATIVO
        # Creamos el dataframe para el gráfico con las 3 columnas
        chart_df = pd.DataFrame({
            'Concepto': ['Cobros Totales', 'Pagos Realizados', 'Deuda Pendiente'],
            'Monto': [f['cobros'], f['pagos'], f['deuda']]
        })
        
        st.bar_chart(data=chart_df, x='Concepto', y='Monto', color='#2E86C1')

        # D. DETALLES EXTRA
        with st.expander("📝 Otros detalles"):
            st.write(f"**Vendedor:** {f['Vende']}")
            st.write(f"**Firma Escritura:** {f['Firma']}")
            st.write(f"**Valor Escritura:** ${f['Valor _Escritura']:,.0f}")

    else:
        st.info("Seleccione un lote para comenzar.")

except Exception as e:
    st.error(f"Hubo un problema al cargar los datos: {e}")