import matplotlib.pyplot as plt
import streamlit as st

def exibir_graficos(df_total,df_gastos):
    """Exibe os gráficos pizza e de barras 
    Args:
    df_total (pd.Dataframe): Dataframe com todas as transações (gastos e recebimentos)
    df_gastos (pd.Dataframe): Dataframe com transações apenasa dos gastos

    Returns:
    None
    
    """

    plota_grafico_pizza(df_total, df_gastos)

    df_head = ranqueia_gatos(df_gastos)

    plot_grafico_mais_gastos(df_head)
    

def plota_grafico_pizza(df_total, df_gastos):
    """
    Plota um gráfico de pizza que mostra o total de gastos com o total de recebimentos.

    Args:
    df_total (pd.DataFrame): DataFrame com todas as transações (coluna 'tipo' e 'valor').

    Returns:
    None
    """

    df_grouped = df_total.groupby('tipo')['valor'].sum().reset_index()
    fig, ax = plt.subplots()
    ax.pie(df_grouped['valor'], labels=df_grouped['tipo'], autopct=lambda p: f'{p * sum(df_grouped["valor"]) / 100:.2f}', startangle=90)
    ax.set_title('Gastos vs Recebimentos')
    ax.axis('equal') 
    st.pyplot(fig)


def ranqueia_gatos(df_gastos):
    """
    Retorna um DataFrame com as 5 categorias de gasto de maior valor.

    Args:
        df_gastos (pd.DataFrame): DataFrame contendo transações de gastos (colunas 'descrição' e 'valor').

    Returns:
        pd.DataFrame: DataFrame com as 5 descrições de gasto mais altas, ordenado em ordem decrescente de valor.
    """
   
    df_gastos_agrupados = df_gastos.groupby('descrição')['valor'].sum().reset_index()
    df_ordem = df_gastos_agrupados.sort_values(by='valor', ascending=False)
    df_head = df_ordem.head(5)

    return df_head


def plot_grafico_mais_gastos(df_head):
    """
    Plota um gráfico de barras mostrando os 5 maiores gastos.

    Args:
        df_head (pd.DataFrame): DataFrame resultante de ranqueia_gatos, com colunas 'descrição' e 'valor'.

    Returns:
        None
    """

    fig2, ax2 = plt.subplots()
    df_head.plot(x='descrição', y='valor', kind='bar', ax=ax2, title='Top 5 gastos')
    
    for p in ax2.patches:
        ax2.annotate(f'{p.get_height():.2f}', (p.get_x() + p.get_width() / 2, p.get_height()), 
                 ha='center', va='bottom', fontsize=10)
    st.pyplot(fig2)

def plota_graficos_categ(df_agg):
    """
    Plota um gráfico de barras dos gastos agrupados por categoria, excluindo 'salário'.

    Args:
        df_agg (pd.Series): Série Pandas com o total de gastos por categoria.

    Returns:
        None
    """
    fig, ax = plt.subplots()
    df_agg.plot(kind='bar', ax=ax)
    ax.set_xlabel('Categoria')
    ax.set_ylabel('Total de Gastos')
    ax.set_title('Gastos por Categoria')

    for bars in ax.patches:
        ax.annotate(f'{bars.get_height():.2f}', (bars.get_x() + bars.get_width() / 2, bars.get_height()), 
                ha='center', va='bottom', fontsize=10)
    
    st.pyplot(fig)    