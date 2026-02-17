import streamlit as st
import pandas as pd
import altair as alt

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Control de Lotes", page_icon="📈", layout="centered")

# --- BLOQUE DE SEGURIDAD ---
def check_password():
    if "password_correct" not in st.session_state:
        st.title("🔐 Acceso Restringido")
        st.text_input("Ingrese la clave de acceso", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.title("🔐 Acceso Restringido")
        st.text_input("Ingrese la clave de acceso", type="password", on_change=password_entered, key="password")
        st.error("😕 Clave incorrecta")
        return False
    return True

def password_entered():
    if st.session_state["password"] == "pioneros2026": # TU CLAVE
        st.session_state["password_correct"] = True
        del st.session_state["password"]
    else:
        st.session_state["password_correct"] = False

# --- APLICACIÓN ---
if check_password():
    
    @st.cache_data
    def cargar_datos():
        try:
            df = pd.read_excel('Datos_Pagos.xlsx', sheet_name='Pagos')
            df.columns = df.columns.str.strip()
            
            if 'fecha_deuda' in df.columns:
                df['fecha_deuda'] = pd.to_datetime(df['fecha_deuda']).dt.strftime('%d/%m/%Y')
            
            for col in ['pagos', 'cobros', 'deuda', 'Valor _Escritura']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            return df
        except Exception as e:
            st.error(f"Error al cargar el archivo: {e}")
            return None

    df = cargar_datos()

    if df is not None:
        st.title("📑 Ficha de Consulta")
        if 'fecha_deuda' in df.columns:
            st.info(f"📅 **Información al:** {df['fecha_deuda'].iloc[0]}")
        
        st.divider()

        # FILTROS
        c1, c2 = st.columns(2)
        with c1:
            proy_sel = st.selectbox("📌 Proyecto", sorted(df['Proy'].unique()))
        df_f = df[df['Proy'] == proy_sel]
        with c2:
            lote_sel = st.selectbox("🏠 Lote", sorted(df_f['Lote'].unique()))

        res = df_f[df_f['Lote'] == lote_sel]

        if not res.empty:
            f = res.iloc[0]

            # 1. DATOS DEL PROPIETARIO
            st.subheader("👤 Datos del Propietario")
            with st.container(border=True):
                st.markdown(f"### {f['Nombre']}")
                st.write(f"**🆔 RUT:** {f['RUT']}")
                
                tel_raw = str(f['Telefono'])
                tel_clean = "".join(filter(str.isdigit, tel_raw))
                if tel_clean:
                    st.write(f"**📞 Teléfono:** +{tel_clean}")
                    ws_url = f"https://wa.me/{tel_clean}?text=Hola%20{f['Nombre']},%20le%20contacto%20por%20el%20lote%20{lote_sel}"
                    st.link_button("💬 Enviar WhatsApp", ws_url, use_container_width=True)
                else:
                    st.warning("⚠️ Sin teléfono registrado")

            # 2. RESUMEN FINANCIERO (Métricas)
            st.subheader("💰 Resumen de Cuenta")
            m1, m2, m3 = st.columns(3)
            m1.metric("Cobros", f"${f['cobros']:,.0f}")
            m2.metric("Pagado", f"${f['pagos']:,.0f}")
            
            deuda_val = f['deuda']
            # Color inverso: si la deuda es "positiva" (debe dinero), se ve rojo en el indicador delta
            m3.metric("Deuda", f"${deuda_val:,.0f}", 
                      delta=f"{deuda_val:,.0f}" if deuda_val != 0 else None, 
                      delta_color="inverse")
            
            st.info(f"**Modalidad:** {f['Modalidad']}")

            # 3. GRÁFICO (Orden: Cobros, Pagos, Deuda)
            st.markdown("---")
            st.write("### 📊 Estado de Pagos")
            
            chart_df = pd.DataFrame({
                'Concepto': ['1. Cobros', '2. Pagos', '3. Deuda'],
                'Monto': [f['cobros'], f['pagos'], f['deuda']]
            })

            # Lógica de color: Rojo si la deuda es negativa (según tu indicación)
            color_deuda = '#E74C3C' if deuda_val < 0 else '#27AE60'
            
            try:
                # Intento de gráfico profesional con Altair
                chart = alt.Chart(chart_df).mark_bar().encode(
                    x=alt.X('Concepto', sort=None, title=None),
                    y=alt.Y('Monto', title='Monto ($)'),
                    color=alt.Color('Concepto', scale=alt.Scale(
                        domain=['1. Cobros', '2. Pagos', '3. Deuda'],
                        range=['#2E86C1', '#27AE60', color_deuda]
                    ), legend=None)
                ).properties(height=450)
                st.altair_chart(chart, use_container_width=True)
            except Exception:
                # Si falla Altair, muestra gráfico básico para no bloquear la app
                st.bar_chart(chart_df.set_index('Concepto'))

            # 4. EXPANSIBLE DE DETALLES
            with st.expander("📝 Ver detalles de contrato"):
                st.write(f"**Vendedor:** {f['Vende']}")
                st.write(f"**Dirección:** {f['Direccion']}")
                st.write(f"**Valor Escritura:** ${f['Valor _Escritura']:,.0f}")
        else:
            st.info("Seleccione un lote para ver la información.")