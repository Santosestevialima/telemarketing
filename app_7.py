import pandas as pd
import streamlit as st
import seaborn as sns
import matplotlib.pyplot as plt
from PIL import Image
from io import BytesIO

# ===============================
# CONFIGURAÇÃO VISUAL
# ===============================
custom_params = {
    "axes.spines.right": False,
    "axes.spines.top": False
}
sns.set_theme(style="ticks", rc=custom_params)

# ===============================
# FUNÇÕES COM CACHE NOVO
# ===============================

@st.cache_data(show_spinner=True)
def load_data(file_data):
    if file_data.name.endswith(".csv"):
        return pd.read_csv(file_data, sep=";")
    else:
        return pd.read_excel(file_data)


@st.cache_data
def multiselect_filter(df, col, selecionados):
    if "all" in selecionados:
        return df
    return df[df[col].isin(selecionados)].reset_index(drop=True)


@st.cache_data
def convert_df(df):
    return df.to_csv(index=False).encode("utf-8")


@st.cache_data
def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Sheet1")
    return output.getvalue()

# ===============================
# APLICAÇÃO PRINCIPAL
# ===============================

def main():
    st.set_page_config(
        page_title="Telemarketing analysis",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    st.title("Telemarketing analysis")
    st.markdown("---")

    # SIDEBAR
    try:
        image = Image.open("Bank-Branding.jpg")
        st.sidebar.image(image)
    except:
        st.sidebar.warning("Imagem não encontrada")

    st.sidebar.subheader("Suba o arquivo")
    data_file = st.sidebar.file_uploader(
        "Bank marketing data",
        type=["csv", "xlsx"]
    )

    if data_file is None:
        st.info("👈 Faça upload de um arquivo para começar")
        return

    # ===============================
    # DADOS
    # ===============================
    bank_raw = load_data(data_file)
    bank = bank_raw.copy()

    st.subheader("Antes dos filtros")
    st.dataframe(bank_raw.head())

    # ===============================
    # FILTROS
    # ===============================
    with st.sidebar.form("filters"):

        graph_type = st.radio(
            "Tipo de gráfico",
            ["Barras", "Pizza"]
        )

        min_age = int(bank.age.min())
        max_age = int(bank.age.max())
        idades = st.slider(
            "Idade",
            min_value=min_age,
            max_value=max_age,
            value=(min_age, max_age)
        )

        def multiselect_with_all(label, series):
            options = sorted(series.unique().tolist())
            options.append("all")
            return st.multiselect(label, options, ["all"])

        jobs = multiselect_with_all("Profissão", bank.job)
        marital = multiselect_with_all("Estado civil", bank.marital)
        default = multiselect_with_all("Default", bank.default)
        housing = multiselect_with_all("Financiamento imobiliário", bank.housing)
        loan = multiselect_with_all("Empréstimo", bank.loan)
        contact = multiselect_with_all("Meio de contato", bank.contact)
        month = multiselect_with_all("Mês do contato", bank.month)
        day = multiselect_with_all("Dia da semana", bank.day_of_week)

        submit = st.form_submit_button("Aplicar filtros")

    # ===============================
    # APLICAR FILTROS
    # ===============================
    bank = (
        bank.query("age >= @idades[0] and age <= @idades[1]")
        .pipe(multiselect_filter, "job", jobs)
        .pipe(multiselect_filter, "marital", marital)
        .pipe(multiselect_filter, "default", default)
        .pipe(multiselect_filter, "housing", housing)
        .pipe(multiselect_filter, "loan", loan)
        .pipe(multiselect_filter, "contact", contact)
        .pipe(multiselect_filter, "month", month)
        .pipe(multiselect_filter, "day_of_week", day)
    )

    # ===============================
    # RESULTADOS
    # ===============================
    st.subheader("Após os filtros")
    st.dataframe(bank.head())

    st.download_button(
        "📥 Download Excel",
        data=to_excel(bank),
        file_name="bank_filtered.xlsx"
    )

    st.markdown("---")

    # ===============================
    # PROPORÇÕES
    # ===============================
    raw_perc = bank_raw.y.value_counts(normalize=True).sort_index() * 100
    filt_perc = bank.y.value_counts(normalize=True).sort_index() * 100

    col1, col2 = st.columns(2)

    col1.subheader("Proporção original")
    col1.dataframe(raw_perc)
    col1.download_button(
        "Download",
        data=to_excel(raw_perc.reset_index()),
        file_name="bank_raw_y.xlsx"
    )

    col2.subheader("Proporção filtrada")
    col2.dataframe(filt_perc)
    col2.download_button(
        "Download",
        data=to_excel(filt_perc.reset_index()),
        file_name="bank_y.xlsx"
    )

    st.markdown("---")

    # ===============================
    # GRÁFICOS
    # ===============================
    st.subheader("Proporção de aceite")

    fig, ax = plt.subplots(1, 2, figsize=(8, 4))

    if graph_type == "Barras":
        sns.barplot(x=raw_perc.index, y=raw_perc.values, ax=ax[0])
        ax[0].set_title("Dados brutos")

        sns.barplot(x=filt_perc.index, y=filt_perc.values, ax=ax[1])
        ax[1].set_title("Dados filtrados")

    else:
        raw_perc.plot(kind="pie", autopct="%.2f%%", ax=ax[0])
        ax[0].set_title("Dados brutos")

        filt_perc.plot(kind="pie", autopct="%.2f%%", ax=ax[1])
        ax[1].set_title("Dados filtrados")

    st.pyplot(fig)


if __name__ == "__main__":
    main()

