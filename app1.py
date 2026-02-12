import streamlit as st
import pandas as pd

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Control de Lotes", page_icon="📈", layout="centered")

# --- BLOQUE DE SEGURIDAD (LOGIN) ---
def check_password():
    """Retorna True si el usuario ingresó la contraseña correcta."""
    def password_entered():
        # CAMBIA AQUÍ TU CONTRASEÑA
        if st.session_state["password"] == "pioneros2026":
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Eliminar contraseña de la memoria
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # Pantalla inicial de Login
        st.title("🔐 Acceso Restringido")
        st.text_input("Ingrese la clave para acceder al sistema", 
                     type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        # Si la clave fue incorrecta
        st.title("🔐 Acceso Restringido")
        st.text_input("Ingrese la clave para acceder al sistema", 
                     type="password", on_change=password_entered, key="password")
        st.error("😕 Contraseña incorrecta. Intente de nuevo.")
        return False
    else:
        # Contraseña correcta
        return True

# --- APLICACIÓN PRINCIPAL ---
if check_password():
    
    @st.cache_data
    def cargar_datos():
        # Carga del Excel
        df = pd.read_excel('Datos_Pagos.xlsx', sheet_name='Pagos')
        df.columns = df.columns.str.strip()
        
        # Formateo de fecha_deuda a DD/MM/AAAA
        if 'fecha_deuda' in df.columns:
            df['fecha_deuda'] = pd.to_datetime(df['fecha_deuda']).dt.strftime('%d/%m/%Y')
        
        # Limpieza financiera (Asegurar que sean números)
        cols_num = ['pagos', 'cobros', 'deuda', 'Valor _Escritura']
        for col in cols_num:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        return df

    try:
        df = cargar_datos()

        # Botón para cerrar sesión (opcional)
        if st.sidebar.button("Cerrar Sesión"):
            st.session_state.clear()
            st.rerun()

        # CABECERA
        st.title("📑 Consulta de Lotes")
        if 'fecha_deuda' in df.columns:
            st.info(f"📅 **Información actualizada al:** {df['fecha_deuda'].iloc[0]}")
        st.divider()

        # FILTROS EN CASCADA
        c1, c2 = st.columns(2)
        with c1:
            proy_sel = st.selectbox("📌 Proyecto", sorted(df['Proy'].unique()))
        
        df_f = df[df['Proy'] == proy_sel]
        
        with c2:
            lote_sel = st.selectbox("🏠 Lote", sorted(df_f['Lote'].unique()))

        # RESULTADOS
        res = df_f[df_f['Lote'] == lote_sel]

        if not res.empty:
            f = res.iloc[0]

            # A. DATOS PERSONALES
            st.subheader("👤 Datos del Cliente")
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
                    st.warning("⚠️ Sin teléfono registrado")

            # B. ESTADO FINANCIERO
            st.subheader("💰 Resumen de Cuenta")
            m1, m2, m3 = st.columns(3)
            m1.metric("Cobros", f"${f['cobros']:,.0f}")
            m2.metric("Pagado", f"${f['pagos']:,.0f}")
            
            deuda = f['deuda']
            color_deuda = "normal" if deuda <= 0 else "inverse"
            m3.metric("Deuda", f"${deuda:,.0f}", 
                      delta=f"-{deuda:,.0f}" if deuda > 0 else None, 
                      delta_color=color_deuda)
            
            # Modalidad y Avisos
            st.write(f"**Modalidad de Pago:** {f['Modalidad']}")
            if f['Modalidad'] == 'T':
                st.success("✅ **Cliente al Contado:** No registra deuda pendiente.")

            # C. GRÁFICO VISUAL
            st.markdown("---")
            st.write("### 📊 Comparativa Financiera")
            chart_df = pd.DataFrame({
                'Concepto': ['Cobros', 'Pagos', 'Deuda'],
                'Monto': [f['cobros'], f['pagos'], f['deuda']]
            })
            st.bar_chart(data=chart_df, x='Concepto', y='Monto', color='#2E86C1')

            # D. OTROS DETALLES
            with st.expander("📝 Otros detalles del lote"):
                st.write(f"**Vendedor:** {f['Vende']}")
                st.write(f"**Firma Escritura:** {f['Firma']}")
                st.write(f"**Valor Escritura:** ${f['Valor _Escritura']:,.0f}")
                st.write(f"**Dirección:** {f['Direccion']}")

        else:
            st.info("Seleccione un lote para ver los detalles.")

    except Exception as e:
        st.error(f"Se produjo un error al cargar la aplicación: {e}")