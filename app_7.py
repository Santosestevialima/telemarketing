# =========================
# IMPORTS
# =========================
import pandas as pd
import streamlit as st
import seaborn as sns
import matplotlib.pyplot as plt

from PIL import Image
from io import BytesIO

# =========================
# CONFIGURAÇÕES VISUAIS
# =========================
custom_params = {
    "axes.spines.right": False,
    "axes.spines.top": False
}
sns.set_theme(style="ticks", rc=custom_params)


# =========================
# FUNÇÕES AUXILIARES
# =========================

@st.cache_data(show_spinner=True)
def load_data(file_data):
    try:
        return pd.read_csv(file_data, sep=';')
    except Exception:
        return pd.read_excel(file_data)


@st.cache_data
def multiselect_filter(df, col, selected):
    if 'all' in selected:
        return df
    return df[df[col].isin(selected)].reset_index(drop=True)


@st.cache_data
def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
    return output.getvalue()


# =========================
# FUNÇÃO PRINCIPAL
# =========================
def main():

    # Configuração da página
    st.set_page_config(
        page_title='Telemarketing analysis',
        page_icon='📊',
        layout='wide',
        initial_sidebar_state='expanded'
    )

    # Título
    st.title('📊 Telemarketing analysis')
    st.markdown('---')

    # Sidebar
    try:
        image = Image.open("Bank-Branding.jpg")
        st.sidebar.image(image)
    except Exception:
        pass

    st.sidebar.header("📂 Suba o arquivo")
    data_file = st.sidebar.file_uploader(
        "Bank marketing data",
        type=['csv', 'xlsx']
    )

    if data_file is None:
        st.info("⬅️ Faça o upload de um arquivo para começar")
        return

    # =========================
    # LEITURA DOS DADOS
    # =========================
    bank_raw = load_data(data_file)
    bank = bank_raw.copy()

    st.subheader("Antes dos filtros")
    st.dataframe(bank_raw.head())

    # =========================
    # FORMULÁRIO DE FILTROS
    # =========================
    with st.sidebar.form("filters_form"):

        graph_type = st.radio("Tipo de gráfico:", ["Barras", "Pizza"])

        min_age = int(bank.age.min())
        max_age = int(bank.age.max())
        age_range = st.slider(
            "Idade",
            min_value=min_age,
            max_value=max_age,
            value=(min_age, max_age)
        )

        def multiselect_block(label, series):
            options = sorted(series.unique().tolist())
            options.append("all")
            return st.multiselect(label, options, default=["all"])

        jobs = multiselect_block("Profissão", bank.job)
        marital = multiselect_block("Estado civil", bank.marital)
        default = multiselect_block("Default", bank.default)
        housing = multiselect_block("Financiamento imobiliário", bank.housing)
        loan = multiselect_block("Empréstimo", bank.loan)
        contact = multiselect_block("Meio de contato", bank.contact)
        month = multiselect_block("Mês do contato", bank.month)
        day = multiselect_block("Dia da semana", bank.day_of_week)

        apply_filters = st.form_submit_button("Aplicar filtros")

    # =========================
    # APLICAÇÃO DOS FILTROS
    # =========================
    if apply_filters:

        bank = (
            bank.query("age >= @age_range[0] and age <= @age_range[1]")
                .pipe(multiselect_filter, "job", jobs)
                .pipe(multiselect_filter, "marital", marital)
                .pipe(multiselect_filter, "default", default)
                .pipe(multiselect_filter, "housing", housing)
                .pipe(multiselect_filter, "loan", loan)
                .pipe(multiselect_filter, "contact", contact)
                .pipe(multiselect_filter, "month", month)
                .pipe(multiselect_filter, "day_of_week", day)
        )

        st.subheader("Após os filtros")
        st.dataframe(bank.head())

        # =========================
        # DOWNLOAD TABELA FILTRADA
        # =========================
        st.download_button(
            "📥 Download tabela filtrada (Excel)",
            data=to_excel(bank),
            file_name="bank_filtered.xlsx"
        )

        st.markdown("---")

        # =========================
        # ANÁLISE DE PROPORÇÃO
        # =========================
        raw_perc = bank_raw.y.value_counts(normalize=True).mul(100).to_frame("y").sort_index()
        filt_perc = bank.y.value_counts(normalize=True).mul(100).to_frame("y").sort_index()

        col1, col2 = st.columns(2)

        col1.subheader("Proporção original")
        col1.dataframe(raw_perc)
        col1.download_button(
            "📥 Download",
            data=to_excel(raw_perc),
            file_name="bank_raw_y.xlsx"
        )

        col2.subheader("Proporção filtrada")
        col2.dataframe(filt_perc)
        col2.download_button(
            "📥 Download",
            data=to_excel(filt_perc),
            file_name="bank_filtered_y.xlsx"
        )

        st.markdown("---")
        st.subheader("Proporção de aceite")

        # =========================
        # GRÁFICOS
        # =========================
        fig, ax = plt.subplots(1, 2, figsize=(6, 3))

        if graph_type == "Barras":
            sns.barplot(x=raw_perc.index, y="y", data=raw_perc, ax=ax[0])
            ax[0].set_title("Dados brutos")
            ax[0].bar_label(ax[0].containers[0])

            sns.barplot(x=filt_perc.index, y="y", data=filt_perc, ax=ax[1])
            ax[1].set_title("Dados filtrados")
            ax[1].bar_label(ax[1].containers[0])
        else:
            raw_perc.plot(kind="pie", y="y", autopct="%.2f%%", ax=ax[0])
            ax[0].set_title("Dados brutos")

            filt_perc.plot(kind="pie", y="y", autopct="%.2f%%", ax=ax[1])
            ax[1].set_title("Dados filtrados")

        st.pyplot(fig)


# =========================
# EXECUÇÃO
# =========================
if __name__ == "__main__":
    main()
