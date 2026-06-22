import streamlit as st
import pandas as pd
import requests
import plotly.express as px

# --- CONFIGURACIÓN DE LA PÁGINA WEB ---
st.set_page_config(
    page_title="Panel de Producción de Cajas",
    page_icon="📦",
    layout="wide"
)

# --- CREDENCIALES DE TU SUPABASE ---
SUPABASE_URL = "https://yotaiegxvpmmihjodhcr.supabase.co/rest/v1/registro_cajas"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InlvdGFpZWd4dnBtbWloam9kaGNyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODIwNzAwNTQsImV4cCI6MjA5NzY0NjA1NH0.0hr1kHiF31v_jWWNVM4XK-Z4ejhHDAsxSb_jBuyHZ6Q"

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}"
}

# --- FUNCIÓN PARA LEER LOS DATOS EN TIEMPO REAL ---
def cargar_datos():
    try:
        # Hacemos una petición GET para leer las filas (ordenadas por fecha reciente)
        url_ordenada = f"{SUPABASE_URL}?order=fecha.desc"
        response = requests.get(url_ordenada, headers=HEADERS)
        
        if response.status_code == 200:
            datos = response.json()
            if len(datos) == 0:
                return pd.DataFrame()
            
            # Convertimos la respuesta JSON en un DataFrame de Pandas
            df = pd.DataFrame(datos)
            # Formatear la fecha para que se lea mejor
            df['fecha'] = pd.to_datetime(df['fecha']).dt.strftime('%Y-%m-%d %H:%M:%S')
            return df
        else:
            st.error(f"Error al conectar con Supabase ({response.status_code})")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return pd.DataFrame()

# --- INTERFAZ VISUAL (DASHBOARD) ---
st.title("🏭 Panel de Monitoreo de Producción en Tiempo Real")
st.markdown("Este tablero muestra el comportamiento de la planta de clasificación de cajas simulada.")

# Botón manual para refrescar datos
if st.button("🔄 Actualizar Datos"):
    st.rerun()

# Cargar los datos actuales de la nube
df_cajas = cargar_datos()

if df_cajas.empty:
    st.warning("Aún no hay datos registrados en la tabla de Supabase o la tabla está vacía.")
else:
    # Diccionario para renombrar las columnas técnicas a nombres limpios y profesionales
    nombres_columnas = {
        "fecha": "Fecha / Hora",
        "total_acumulado": "Total Acumulado",
        "grandes_acumulado": "Grandes Acumulado",
        "chicas_acumulado": "Chicas Acumulado",
        "total_x_minuto": "Total por Minuto",
        "grandes_x_minuto": "Grandes por Minuto",
        "chicas_x_minuto": "Chicas por Minuto"
    }

    # 1. TARJETAS DE INDICADORES (Últimos valores acumulados registrados)
    ultimo_registro = df_cajas.iloc[0] # El primero es el más nuevo debido al orden descandente
    
    st.subheader("📊 Estado Actual del Sistema (Acumulado)")
    col1, col2, col3 = st.columns(3)
    col1.metric(label="Total Cajas Procesadas", value=int(ultimo_registro['total_acumulado']))
    col2.metric(label="Cajas Grandes", value=int(ultimo_registro['grandes_acumulado']), delta="Línea Alta")
    col3.metric(label="Cajas Chicas", value=int(ultimo_registro['chicas_acumulado']), delta="Línea Baja")
    
    st.markdown("---")
    
    # 2. GRÁFICOS INTERACTIVOS (Producción por minuto)
    st.subheader("📈 Evolución de la Producción por Minuto")
    
    # Invertimos el orden para la gráfica (izquierda pasado -> derecha presente) y renombramos
    df_grafico = df_cajas.iloc[::-1].rename(columns=nombres_columnas)
    
    # Gráfico de líneas interactivo usando Plotly con los nuevos nombres
    fig = px.line(
        df_grafico, 
        x="Fecha / Hora", 
        y=["Total por Minuto", "Grandes por Minuto", "Chicas por Minuto"],
        labels={"value": "Cantidad de Cajas", "variable": "Categoría"},
        title="Rendimiento de Clasificación por Minuto",
        markers=True
    )
    st.plotly_chart(fig, width='stretch')
    
    st.markdown("---")
    
    # 3. TABLA DE DATOS HISTÓRICOS (Con numeración desde 1)
    st.subheader("📋 Historial de Registros Almacenados")
    
    # Filtramos las columnas requeridas y aplicamos el cambio de nombre visual
    df_historial_visual = df_cajas[[
        "fecha", "total_acumulado", "grandes_acumulado", "chicas_acumulado", 
        "total_x_minuto", "grandes_x_minuto", "chicas_x_minuto"
    ]].rename(columns=nombres_columnas)
    
    # Volteamos el DataFrame temporalmente para asignar el índice correlativo desde 1 (1 para el más antiguo)
    df_historial_visual = df_historial_visual.iloc[::-1]
    df_historial_visual.index = range(1, len(df_historial_visual) + 1)
    
    # Volvemos a poner el orden descendente para que el más nuevo aparezca arriba en la tabla, manteniendo sus IDs fijos
    df_historial_visual = df_historial_visual.iloc[::-1]
    
    # Mostramos la tabla limpia estilo Excel sin advertencias de tamaño
    st.dataframe(df_historial_visual, width='stretch')
