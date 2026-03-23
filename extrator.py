import ee
import geopandas as gpd
import pandas as pd
import os
import json
import re
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

def autenticar_ee():
    json_key = os.getenv('EARTH_ENGINE_KEY')
    if not json_key:
        raise ValueError("EARTH_ENGINE_KEY não encontrada.")
    info = json.loads(json_key)
    credenciais = ee.ServiceAccountCredentials(info['client_email'], key_data=json_key)
    ee.Initialize(credenciais)

def mascarar_nuvens(imagem):
    qa = imagem.select('QA60')
    nuvem_bit, cirrus_bit = 1 << 10, 1 << 11
    mascara = qa.bitwiseAnd(nuvem_bit).eq(0).And(qa.bitwiseAnd(cirrus_bit).eq(0))
    return imagem.updateMask(mascara).divide(10000)

def validar_arquivo(nome_arquivo):
    padrao = r"^(\d+)-(\d{8})\.shp$"
    match = re.match(padrao, nome_arquivo)
    if not match: return None, None
    cod_area, data_str = match.groups()
    data_dt = datetime.strptime(data_str, "%Y%m%d")
    return (cod_area, data_dt) if data_dt >= datetime(2022, 1, 1) else (None, None)

def processar_repositorio():
    autenticar_ee()

    hoje = datetime.now()
    pasta_raiz = os.getenv('PASTA_AREAS', 'areas')
    excel_final = os.getenv('NOME_EXCEL', 'analise.xlsx')

    # Definição da ordem exata das colunas
    bandas = ['B1','B2','B3','B4','B5','B6','B7','B8','B8A','B9','B11','B12']

    ordem_colunas = [
        'area', 'data', 'n_pixels',
        *[f"{b}_{stat}" for b in bandas for stat in ['mean', 'median', 'std']]
    ]

    for root, _, files in os.walk(pasta_raiz):
        for nome_arq in files:
            if nome_arq.endswith(".shp"):
                cod_area, data_cursor = validar_arquivo(nome_arq)
                if not cod_area: continue

            if os.path.exists(excel_final):
                try:
                    df_ex = pd.read_excel(excel_final, sheet_name=str(cod_area))
                    if not df_ex.empty:
                        data_cursor = pd.to_datetime(df_ex['data'].max()) + timedelta(days=7)
                except: pass

            try:
                gdf = gpd.read_file(os.path.join(root, nome_arq)).to_crs("EPSG:4326")
                geom_ee = ee.Geometry(gdf.geometry.iloc[0].__geo_interface__)

                while data_cursor + timedelta(days=7) <= hoje:

                    s_ini, s_fim = data_cursor.strftime('%Y-%m-%d'), (data_cursor + timedelta(days=7)).strftime('%Y-%m-%d')

                    imagem = (
                        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
                        .filterBounds(geom_ee)
                        .filterDate(s_ini, s_fim)
                        .map(mascarar_nuvens)
                        .select(bandas) # Pega de B1 em diante
                        .median()
                    )

                    reducer = (
                        ee.Reducer.mean()
                        .combine(ee.Reducer.median(), '', True)
                        .combine(ee.Reducer.stdDev(), '', True)
                        .combine(ee.Reducer.count(), '', True)
                    )

                    stats = imagem.reduceRegion(
                        reducer=reducer,
                        geometry=geom_ee,
                        scale=10
                    ).getInfo()

                    if stats and any(v is not None for v in stats.values()):

                        stats_formatado = {}
                        n_pixels = None

                        for k, v in stats.items():
                            if k.endswith('_stdDev'):
                                stats_formatado[k.replace('_stdDev', '_std')] = v
                            elif k.endswith('_count'):
                                n_pixels = v
                            else:
                                stats_formatado[k] = v

                        registro = {
                            'area': cod_area,
                            'data': s_ini,
                            'n_pixels': n_pixels,
                            **stats_formatado
                        }

                        df_novo = pd.DataFrame([registro]).reindex(columns=ordem_colunas)

                        mode = 'a' if os.path.exists(excel_final) else 'w'

                        with pd.ExcelWriter(
                            excel_final,
                            engine='openpyxl',
                            mode=mode,
                            if_sheet_exists='overlay' if mode == 'a' else None
                        ) as writer:

                            nome_aba = str(cod_area)

                            try:
                                df_atual = pd.read_excel(excel_final, sheet_name=nome_aba)

                                df_final = pd.concat([df_atual, df_novo], ignore_index=True)

                                df_final = df_final.drop_duplicates(subset=['area', 'data'])

                                df_final.to_excel(writer, sheet_name=nome_aba, index=False)

                            except:
                                df_novo.to_excel(writer, sheet_name=nome_aba, index=False)

                        print(f"Sucesso [{cod_area}]: {s_ini}")

                    data_cursor += timedelta(days=7)

            except Exception as e:
                print(f"Erro {nome_arq}: {e}")

if __name__ == "__main__":
    processar_repositorio()