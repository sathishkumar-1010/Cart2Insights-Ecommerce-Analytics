
import mysql.connector
import pandas as pd
import streamlit as st


@st.cache_resource
def get_connection():
    return mysql.connector.connect(
        host=st.secrets["mysql"]["host"],
        user=st.secrets["mysql"]["user"],
        password=st.secrets["mysql"]["password"],
        database=st.secrets["mysql"]["database"]
    )


def run_query(query, params=None):
    conn = get_connection()

    return pd.read_sql(
        query,
        conn,
        params=params
    )
